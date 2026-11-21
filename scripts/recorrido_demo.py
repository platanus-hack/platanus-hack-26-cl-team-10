"""El recorrido del demo, de punta a punta y sin HTTP ni hardware.

Correr:  python3 scripts/recorrido_demo.py
Es el guion del ADR del demo convertido en código: si esto corre, el esqueleto
sostiene los cinco momentos. Los frentes reemplazan stubs sin romperlo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import cerebro, db, protocolos, verificacion
from app.contratos import Evento, TipoEvento
from app.reglas import estados_desde_eventos, evaluar, paso_actual, reglas_seguridad

cx = db.conectar(":memory:")


def declarar(ot_id, actor, texto):
    pauta = db.leer_pauta(cx, "pauta-correa-ct-01")
    paso = paso_actual(pauta, estados_desde_eventos(db.eventos(cx, ot_id)))
    v = evaluar(paso, texto, db.estado_sensores(cx), verificacion.juez_camara)
    db.agregar(cx, Evento(ot_id=ot_id, tipo=TipoEvento.VEREDICTO, ts=db.ahora(),
                          actor="sistema", paso_id=paso.id, estado=v.estado, capa=v.capa,
                          declarado=texto, evidencia=v.evidencia, detalle=v.detalle))
    marca = {"verificado": "✓", "en_conflicto": "✗ CONFLICTO", "no_verificado": "·"}[str(v.estado)]
    print(f"  {marca} {paso.id} «{texto}» → {v.estado} (capa {v.capa}): {v.detalle}")
    return v


def sensor(sensor_id, valor):
    db.escribir_sensor(cx, sensor_id, valor)
    print(f"  [sensor] {sensor_id} = {valor}")
    for a in reglas_seguridad(db.estado_sensores(cx)):
        db.agregar(cx, Evento(ot_id="ot-1", tipo=TipoEvento.ALERTA, ts=db.ahora(),
                              actor="sistema", estado=a.estado, capa=a.capa,
                              evidencia=a.evidencia, detalle=a.detalle))
        print(f"  🔊 ALERTA capa 1 → {a.detalle}")


print("— 1 · El protocolo se vuelve pauta y se abre la OT")
pauta = protocolos.desde_json()
db.guardar_pauta(cx, pauta)
db.abrir_ot(cx, "ot-1", pauta, "sistema")
print(f"  {pauta.nombre} v{pauta.version}: {len(pauta.pasos)} pasos")

print("— 2 · El operario A trabaja y la evidencia manda")
declarar("ot-1", "operario:A", "bloqueo puesto")          # sensor aún abierto → conflicto
sensor("reed_bloqueo", "cerrado")
sensor("energia", "cortada")
declarar("ot-1", "operario:A", "bloqueo puesto")          # ahora sí
sensor("guarda", "abierta")
declarar("ot-1", "operario:A", "guarda retirada")

print("— 3 · El momento: guarda abierta con energía viva")
sensor("energia", "viva")                                  # dispara la alerta crítica
sensor("energia", "cortada")

print("— 4 · A se va a mitad del trabajo; llega B")
evs = db.eventos(cx, "ot-1")
estado = cerebro.estado_de_ot(pauta, evs)
resumen = cerebro.redactar_resumen(estado, evs)
db.agregar(cx, Evento(ot_id="ot-1", tipo=TipoEvento.RELEVO_ENTREGADO, ts=db.ahora(),
                      actor="operario:A", detalle=resumen))
db.agregar(cx, Evento(ot_id="ot-1", tipo=TipoEvento.RELEVO_RECIBIDO, ts=db.ahora(),
                      actor="operario:B", detalle="operario:B confirma que recibió el turno"))
print(f"  resumen → {resumen}")
r = cerebro.responder("¿se puso el bloqueo?", pauta, db.eventos(cx, "ot-1"))
print(f"  B pregunta «¿se puso el bloqueo?» → {r['respuesta']} | evidencia: {r['evidencia']}")

print("— 5 · B termina la pauta")
verificacion.forzar_camara(pauta.paso("p3").pregunta_visual, True)
declarar("ot-1", "operario:B", "rodillo nuevo instalado")
sensor("guarda", "cerrada")
declarar("ot-1", "operario:B", "guarda reinstalada")
sensor("reed_bloqueo", "abierto")
declarar("ot-1", "operario:B", "bloqueo retirado y energizado")
declarar("ot-1", "operario:B", "la correa paró en dos segundos")

final = cerebro.estado_de_ot(pauta, db.eventos(cx, "ot-1"))
assert final["completa"], final
n = len(db.eventos(cx, "ot-1"))
print(f"\nPauta completa. Bitácora: {n} eventos, ninguno editado ni borrado.")
