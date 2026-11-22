"""El eval de la mejora continua: ¿encuentra las conductas erróneas recurrentes sin engañarse con el ruido?

  uv run python scripts/simular_mejora.py                 # escribe knowledge/projects/mejora-continua/simulacion.md
  uv run python scripts/simular_mejora.py --rapido        # menos repeticiones, para probar

Seis partes: (1) fidelidad, que cada conducta simulada deja en la bitácora real la señal esperada; (2) el criterio,
la regla «el mismo paso en 2 OT» contra la prueba de app/recurrencia.py, con y sin un patrón; (3) la validación de
un cambio, con y sin efecto; (4) el aviso en vivo al supervisor; (5) la convergencia de varios protocolos en paralelo;
(6) las escenas del demo, de punta a punta por los servicios reales.
"""

from __future__ import annotations

import argparse
import dataclasses
import statistics
import sys
from multiprocessing import Pool
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import mejora, recurrencia  # noqa: E402
from app import simulacion as S  # noqa: E402
from app.protocolos import DATOS, desde_json  # noqa: E402

SALIDA = Path(__file__).resolve().parent.parent / "knowledge" / "projects" / "mejora-continua" / "simulacion.md"
PAUTA = desde_json(DATOS / "pauta-polin-demo.json")


def pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.0f} %" if x >= 0.1 or x == 0 else f"{100 * x:.1f} %".replace(".", ",")


def _p(x: float | None) -> str:
    return "—" if x is None else "< 0,0001" if x < 0.0001 else f"{x:.4f}".replace(".", ",")


def perfiles() -> list[str]:
    filas = ["| Perfil | Causa | Conducta | ¿La arregla la pauta? | Remedio | Efecto en la v2 | Fuente |", "|---|---|---|---|---|---|---|"]
    for p in S.PERFILES.values():
        efecto = "sin dato publicado" if p.efecto_v2 is None else f"tasa × {p.efecto_v2:g}"
        filas.append(f"| {p.nombre} | {p.causa} | `{p.modo}` | {'sí' if p.arreglable else '**no**'} | {p.remedio} | {efecto} | {p.fuente} |")
    return filas


def fidelidad(semillas: int) -> list[str]:
    casos = [("olvido", "p2"), ("presion", "p6"), ("apuro", "p4"), ("equipo", "p2"), ("impracticable", "p7")]
    filas = ["| Corrida | Desviaciones simuladas con señal | Señales leídas | Faltan | Sobran |", "|---|---|---|---|---|"]
    for perfil, paso in casos:
        sim = S.Simulador(PAUTA)
        f = S.fidelidad(sim.correr(20, [S.Patron(perfil, paso, 0.5)], ruido=0.05, semilla=7))
        filas.append(f"| {perfil} en {paso}, con ruido 5 %, 20 OT | {f['esperadas']} | {f['vistas']} | {len(f['faltan'])} | {len(f['sobran'])} |")
    saltables = [p.id for p in PAUTA.en_orden if S.senal_esperada(PAUTA, p.id, "saltar")]
    no = [p.id for p in PAUTA.en_orden if not S.senal_esperada(PAUTA, p.id, "saltar")]
    filas += ["", f"Saltarse un paso deja señal solo si el saltado es un control crítico de sensor seguido de otro paso de "
              f"sensor (alerta de orden), o si adelantar el siguiente deshace un control ya verificado (control perdido): "
              f"en `{PAUTA.id}` son {', '.join(saltables)}. Saltarse {', '.join(no)} no deja nada en la bitácora: "
              "la simulación lo rechaza en vez de contarlo como no detectado."]
    # el atajo de Monte Carlo contra el pipeline real, en un punto
    reales = {"minimo": 0, "recurrencia": 0}
    for s in range(semillas):
        sim = S.Simulador(PAUTA)
        c = sim.correr(20, [S.Patron("olvido", "p2", 0.3)], ruido=0.05, semilla=100 + s)
        props = c.propuestas()
        falsas_min = any(p["paso"] != "p3" for p in props)
        falsas_rec = any(p["paso"] != "p3" and p["recurrencia"]["recurrente"] for p in props)
        reales["minimo"] += falsas_min
        reales["recurrencia"] += falsas_rec
    filas += ["", f"Contraste con el pipeline real: {semillas} pautas simuladas de punta a punta (olvido en p2 al 30 %, ruido "
              f"5 %, 20 OT). Pautas con alguna propuesta falsa: regla de 2 OT {pct(reales['minimo'] / semillas)}, prueba "
              f"de recurrencia {pct(reales['recurrencia'] / semillas)}. Compáralo con la fila equivalente del Monte Carlo de abajo "
              "(20 OT, base 5 %, patrón 30 %): el ruido real cae en 8 pasos y el patrón deja su señal en p3."]
    return filas


def criterio(rep: int) -> list[str]:
    filas = ["| OT | Ruido por paso | Patrón | Regla 2 OT: propuesta falsa | Regla 2 OT: detecta | Recurrencia: propuesta falsa | Recurrencia: detecta |",
             "|---|---|---|---|---|---|---|"]
    for ots in (5, 10, 20, 50):
        for base in (0.02, 0.05, 0.10):
            for patron in (None, 0.3):
                r = S.montecarlo_criterio(8, ots, base, patron, repeticiones=rep, semilla=ots * 100 + int(base * 100))
                filas.append(f"| {ots} | {pct(base)} | {'—' if patron is None else pct(patron)} | {pct(r['minimo']['falsa_propuesta'])} "
                             f"| {pct(r['minimo']['detecta'])} | {pct(r['recurrencia']['falsa_propuesta'])} | {pct(r['recurrencia']['detecta'])} |")
    return filas


def validacion(rep: int) -> list[str]:
    filas = ["| OT por versión | Efecto real de la v2 | «Mejoró» con la regla anterior | «Mejoró» con Fisher |", "|---|---|---|---|"]
    for ots in (5, 10, 20, 50):
        for nombre, factor in (("ninguno", 1.0), ("THERP: tasa × 0,3", 0.3)):
            r = S.montecarlo_validacion(ots, 0.3, factor, repeticiones=rep, semilla=ots)
            filas.append(f"| {ots} | {nombre} | {pct(r['ingenua'])} | {pct(r['fisher'])} |")
    peor = S.montecarlo_peor_paso(8, 20, 0.10, repeticiones=rep)
    filas += ["", f"**Regresión a la media.** Se elige el paso que más se desvió en la v1 (8 pasos al 10 %, 20 OT) y se vuelve a "
              f"medir sin cambiar nada: la regla anterior dice «mejoró» el {pct(peor['ingenua'])} de las veces; Fisher, el "
              f"{pct(peor['fisher'])}. Elegir el peor ya sesga a Fisher un poco sobre su 5 %; por eso la escena 1 deja pasos "
              "sin cambiar como control."]
    return filas


def aviso(rep: int, semillas: int) -> list[dict]:
    filas = ["| α del aviso | Aviso falso en 200 OT de solo ruido | Detecta un paso al 30 % dentro de 200 OT | OT de la detección (mediana) |",
             "|---|---|---|---|"]
    for nombre, alfa in (("0,05 fijo", 0.05), ("0,005 fijo", 0.005), ("repartido, `mejora.alfa_en_vivo`", mejora.alfa_en_vivo)):
        nulo = S.montecarlo_aviso(7, 200, 0.05, None, alfa, repeticiones=max(100, rep // 4), semilla=1)
        alt = S.montecarlo_aviso(7, 200, 0.05, 0.3, alfa, repeticiones=max(100, rep // 4), semilla=2)
        filas.append(f"| {nombre} | {pct(nulo['falso_aviso'])} | {pct(alt['detecta_antes_de'])} | {alt['detecta_en']} |")
    estacion = desde_json(DATOS / "pauta-polin-estacion.json")
    numeros, falsos, nunca = [], 0, 0
    for s in range(semillas):
        c = S.Simulador(estacion, cliente="sim").correr(30, [S.Patron("presion", "e1", 0.3)], ruido=0.05, semilla=300 + s)
        av = c.avisos()
        n = next((a["numero"] for a in av if a["paso"] == "e1"), None)
        numeros.append(n) if n else None
        nunca += n is None
        falsos += any(a["paso"] != "e1" for a in av)
    numeros.sort()
    filas += ["", f"De punta a punta, en la pauta del demo (`pauta-polin-estacion`, 7 pasos): el operario se acerca sin apagar el "
              f"motor en el 30 % de las OT, con ruido al 5 % en el resto. En {semillas} corridas de 30 OT, la recomendación sobre "
              f"«Apagar el motor» le llegó al supervisor en la OT {numeros[len(numeros) // 2] if numeros else '—'} (mediana), "
              f"no llegó en {nunca}, y {falsos} corridas tuvieron además un aviso sobre otro paso. Si los demás pasos están "
              "limpios, en una versión recién aprobada el aviso llega a la tercera OT seguida que se salta el mismo paso "
              "(`tests/test_simulacion.py`); si la versión ya trae 4 OT limpias, a la cuarta "
              "(`tests/test_mejora_y_metricas.py`), porque el α de cada mirada depende de cuántas OT lleva la versión."]
    return filas


CASOS_CONVERGENCIA = [
    ("Planta A: olvido en «Poner tu candado»", S.Caso("oculta", "prot-correa-01", "planta-a", "pauta-polin-ct-01", [S.Patron("olvido", "p2", 0.3)])),
    ("Planta B: presión en «Volver a poner la tapa»", S.Caso("oculta", "prot-correa-01", "planta-b", "pauta-polin-ct-01", [S.Patron("presion", "p7", 0.3)])),
    ("Otra empresa: solo ruido", S.Caso("andina", "prot-correa-01", None, "pauta-polin-ct-01", [])),
]


def _una_convergencia(args):
    politica, semilla, rondas, ots = args
    r = S.iterar_en_paralelo([c for _, c in CASOS_CONVERGENCIA], iteraciones=rondas, ots_por_iteracion=ots,
                             semilla=semilla, politica=politica)
    return politica, list(r.values())


def convergencia(semillas: int, rondas: int, ots: int) -> list[str]:
    tareas = [(pol, s, rondas, ots) for pol in ("recurrencia", "minimo") for s in range(semillas)]
    with Pool() as pool:
        resultados = pool.map(_una_convergencia, tareas)
    filas = ["| Protocolo | Política | Convergió | Versiones escritas (mediana · máx.) | Tasa del patrón: 1.ª vuelta → últimas 3 | Escaló a la supervisión |",
             "|---|---|---|---|---|---|"]
    for i, (nombre, _) in enumerate(CASOS_CONVERGENCIA):
        for politica, etiqueta in (("recurrencia", "recurrencia, α repartido"), ("minimo", "regla de 2 OT")):
            hs = [r[i] for pol, r in resultados if pol == politica]
            conv = sum(S.convergio(h) for h in hs)
            versiones = [sum(x["version_nueva"] for x in h) for h in hs]
            ini = statistics.mean(h[0]["tasa_del_patron"] for h in hs)
            fin = statistics.mean(statistics.mean(x["tasa_del_patron"] for x in h[-3:]) for h in hs)
            escalo = sum(any(x["escaladas"] for x in h) for h in hs)
            filas.append(f"| {nombre} | {etiqueta} | {conv} de {len(hs)} | {statistics.median(versiones):g} · {max(versiones)} | "
                         f"{ini:.2f} → {fin:.2f} | {escalo} de {len(hs)} |")
    maximo = {pol: max(sum(x["version_nueva"] for x in h) for p, r in resultados if p == pol for h in r)
              for pol in ("recurrencia", "minimo")}
    filas += ["", f"Con la recurrencia ningún protocolo pasó de {maximo['recurrencia']} versiones en {rondas} vueltas; con la "
              f"regla de 2 OT, hasta {maximo['minimo']}."]
    filas += ["", f"{semillas} semillas por política, {rondas} vueltas de {ots} OT por protocolo, los tres protocolos sobre la misma "
              "base. «Convergió»: Factum no escribió otra versión en las 2 últimas vueltas. «Tasa del patrón»: la fracción de OT en "
              "que la conducta simulada se dio, sin contar el ruido."]
    return filas


def _escena(patrones, factores, n=50, ruido=0.05, semilla=11) -> tuple[list[dict], list[dict]]:
    sim = S.Simulador(PAUTA)
    sim.correr(n, patrones, ruido=ruido, semilla=semilla)
    v1 = sim.corrida.propuestas()
    sim.versionar(dataclasses.replace(PAUTA, version=PAUTA.version + 1))
    sim.correr(n, patrones, ruido=ruido, semilla=semilla + 1000, factores=factores)
    return v1, [p for p in sim.corrida.propuestas() if p["version"] == PAUTA.version]


def escenas() -> list[str]:
    filas = []
    casos = [
        ("1 · Olvido en «Poner tu candado»", [S.Patron("olvido", "p2", 0.3)], {"olvido": S.PERFILES["olvido"].efecto_v2},
         "La v2 agrega la verificación explícita; su efecto es el de THERP, no uno elegido por nosotros."),
        ("2 · Presión de tiempo en «Alejarte de la correa»", [S.Patron("presion", "p6", 0.3)], {"presion": 1.0},
         "El operario saca el candado antes de alejarse. La señal cae en «Poner tu candado», el control que se deshizo. "
         "Ningún texto de la pauta ataca la presión: la v2 no cambia la conducta y el sistema no debe adjudicarse una mejora."),
        ("3 · Solo ruido", [], {}, "Nadie se desvía con patrón. Lo correcto es no proponer nada."),
        ("4 · El sensor del candado falla", [S.Patron("equipo", "p2", 0.3)], {"equipo": 1.0},
         "La propuesta tiene que mandar a revisar el sensor, no la pauta."),
    ]
    for titulo, patrones, factores, que in casos:
        v1, despues = _escena(patrones, factores)
        filas += [f"### Escena {titulo}", "", que, "",
                  "| Paso | OT con señal (v1) | Señales | ¿Recurrente? | p | Validación con la v2 | p de la validación | La regla anterior habría dicho |",
                  "|---|---|---|---|---|---|---|---|"]
        for p in despues:
            senales = ", ".join(f"{k} {v}" for k, v in p["senales"].items() if v)
            val = p["validacion"] or {}
            antes = p["ots_con_senal"] / p["ejecuciones"]
            ingenua = ("mejoro" if val["ots_con_senal"] / val["ejecuciones"] < antes else "se_repite") if val.get("ejecuciones") else "—"
            filas.append(f"| {p['paso']} · {p['titulo']} | {p['ots_con_senal']} de {p['ejecuciones']} | {senales} | "
                         f"{'**sí**' if p['recurrencia']['recurrente'] else 'no'} | {_p(p['recurrencia']['p_valor'])} | "
                         f"{val.get('resultado', '—')} ({val.get('ots_con_senal', '—')} de {val.get('ejecuciones', '—')}) | "
                         f"{_p(val.get('p_valor'))} | {ingenua} |")
        if not despues:
            filas.append("| — | ninguna propuesta | | | | | | |")
        sugerencias = [p for p in despues if p["recurrencia"]["recurrente"]]
        if sugerencias:
            filas += ["", f"Sugerencia del paso recurrente: «{sugerencias[0]['sugerencia']}»"]
        filas.append("")
    return filas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args()
    rep, semillas = (200, 10) if a.rapido else (2000, 100)
    texto = [
        "# Simulación de la mejora continua", "",
        f"> Generado por `scripts/simular_mejora.py` el {date.today().isoformat()}, con {rep} repeticiones por fila de Monte Carlo "
        f"y {semillas} pautas de punta a punta. **Datos simulados.** Miden si el sistema distingue un patrón del ruido y si "
        "se adjudica mejoras que no causó; no miden cuánto se desvía un operario real ni cuánto sirve reescribir una pauta. "
        "Se regenera, no se edita a mano.", "",
        "La pauta es `pauta-polin-demo` (8 pasos, 6 controles críticos). Las OT pasan por `app/servicios.py` real; la conducta "
        "simulada queda aparte de la bitácora, así cada propuesta se puede revisar contra lo que de verdad pasó.", "",
        "## Perfiles", "",
        "Cada perfil es una causa. Si la pauta la arregla, y con qué efecto, se declara acá antes de correr: la v2 no deja de "
        "desviarse porque el operario simulado lo tenga programado.", "",
        *perfiles(), "",
        "## 1 · Fidelidad: lo simulado es lo que lee la mejora", "", *fidelidad(semillas), "",
        "## 2 · El criterio: ¿un patrón o ruido?", "",
        f"Ocho pasos que se desvían al azar con la tasa de ruido y, en las filas con patrón, uno que se desvía más. "
        f"«Propuesta falsa»: la pauta tiene al menos un paso marcado sin patrón. La regla de hoy es `mejora.MINIMO = {mejora.MINIMO}`; "
        f"la recurrencia compara cada paso con el resto de su pauta (binomial exacta, Holm, α = {recurrencia.ALFA}).", "",
        *criterio(rep), "",
        "## 3 · La validación: ¿la v2 mejoró o fue azar?", "",
        "La v1 y la v2 con OT distintas, un paso al 30 %. Hasta el 2026-11-21 `mejora.py` decía «mejoró» si la tasa de la v2 era "
        "menor; ahora pide Fisher exacta (`recurrencia.comprobar_cambio`) y si no alcanza dice «sin_evidencia».", "",
        *validacion(rep), "",
        "## 4 · El aviso en vivo al supervisor", "",
        "La recomendación le aparece al supervisor apenas un paso se vuelve recurrente: la prueba corre después de cada "
        "señal (`servicios._vigilar_patrones`). Mirar después de cada OT es probar muchas veces, y con un α fijo mirar sin fin "
        "termina dando un aviso falso con seguridad. Por eso el aviso, la versión que escribe Factum y la escalada reparten "
        f"su α entre las miradas: la k-ésima OT de una versión gasta {mejora.ALFA_VIDA:g}·6/(π²k²) (`mejora.alfa_en_vivo`), y "
        f"como esa serie suma {mejora.ALFA_VIDA:g}, la probabilidad de un aviso falso en toda la vida de una versión no pasa de "
        f"{mejora.ALFA_VIDA:g}, por muchas OT que se ejecuten. El costo es detectar más tarde un patrón moderado; un paso que "
        "se salta en cada OT, con el resto limpio, sigue avisando a la tercera.", "",
        *aviso(rep, semillas), "",
        "## 5 · Convergencia: varios protocolos mejorando en paralelo", "",
        "Cada empresa itera cada protocolo por su cuenta (ADR-0018). En cada vuelta, cada protocolo ejecuta sus OT con su "
        "versión vigente; después Factum lee sus propuestas por desviación y escribe la versión siguiente de las que se "
        "distinguen del ruido con el α repartido, o escala a la supervisión las que `mejora.py` marca `escalar`: un paso que "
        "vuelve a ser recurrente después de un cambio que no lo bajó. Una escalada queda firme mientras dure la versión. "
        "El efecto de cada versión es el declarado en los perfiles y se aplica una vez por paso. Se compara con la regla "
        "anterior, que versiona toda propuesta de dos OT.", "",
        *convergencia(*((3, 8, 20) if a.rapido else (10, 12, 30))), "",
        "Lo que muestra: con la regla de 2 OT, Factum escribe una versión en casi todas las vueltas y en los tres protocolos, "
        "también en el que solo tiene ruido: no converge. Con la recurrencia y el α repartido, el protocolo con solo ruido "
        "no recibe ninguna versión, el de la presión recibe una, no mejora y se escala, y el del olvido baja su tasa con la "
        "verificación de THERP y para; si el resto del olvido sigue sobre el ruido, intenta una segunda versión y, como no lo "
        "baja, escala.", "",
        "## 6 · Las escenas del demo, de punta a punta", "",

        "50 OT con la v1 y 50 OT nuevas con la v2, ruido 5 % en todos los pasos. Cada tabla son las propuestas de la v1 con su "
        "validación contra la v2.", "",
        *escenas(),
        "## Lo que esto no prueba", "",
        "- Las tasas por paso de una faena real. No hay estudios con tasas de desviación por paso en mantención minera; la "
        "desviación autodeclarada va de 0 a 90 % (Mendoza et al. 2024).",
        "- Cuánto baja la desviación al reescribir un paso. Fuera de la casilla de verificación de THERP no hay un efecto "
        "publicado: «impracticable» y «apuro» quedan sin efecto declarado y la simulación no los usa para afirmar mejoras.",
        "- Las tasas de THERP y HEART son de errores no intencionales, sobre todo de la industria nuclear. No cubren las violaciones.",
        "- Saltarse un paso que no es control crítico no deja señal: lo que la evidencia no ve, la mejora no lo propone.",
        "", "Fuentes: REFERENCIAS 10, 13, 33, 34 y 40; NUREG/CR-1278 tabla 20-7; NIST/SEMATECH e-Handbook 7.2.4 y 7.3.3; "
        "Sommers et al. 2025 (*Process Science*); Barnett et al. 2005 (regresión a la media).", "",
    ]
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text("\n".join(texto), encoding="utf-8")
    print(f"escrito {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
