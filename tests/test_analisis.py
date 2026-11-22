"""Lo que se comprueba de una pauta sin modelo: citas, factibilidad, criterio e historia (ADR-0015).

Correr:  uv run python -m unittest tests.test_analisis
"""

import json
import unittest

from app import analisis, catalogo
from app.contratos import Estado, Evento, TipoEvento
from app.protocolos import DATOS, desde_json

POLIN = desde_json(DATOS / "pauta-polin.json")
CORREA = json.loads((DATOS / "estaciones" / "correa-ct-01.json").read_text(encoding="utf-8"))
DEMO = json.loads((DATOS / "estaciones" / "demo.json").read_text(encoding="utf-8"))


def pedidos(lista, analisis_):
    return [x["sobre"] for x in lista if x["analisis"] == analisis_]


def ot(*filas):
    """Una OT: (minuto, paso, estado, capa) o (minuto, 'alerta', evidencia)."""
    evs = [Evento(ot_id="x", tipo=TipoEvento.OT_ABIERTA, ts="2026-11-21T08:00:00", actor="sistema", detalle="")]
    for minuto, paso, *resto in filas:
        ts = f"2026-11-21T08:{minuto:02d}:00"
        if paso == "alerta":
            evs.append(Evento(ot_id="x", tipo=TipoEvento.ALERTA, ts=ts, actor="sistema", detalle="",
                              estado=Estado.EN_CONFLICTO, capa=1, evidencia=resto[0]))
        else:
            evs.append(Evento(ot_id="x", tipo=TipoEvento.VEREDICTO, ts=ts, actor="sistema", detalle="",
                              paso_id=paso, estado=resto[0], capa=resto[1]))
    return evs


class Citas(unittest.TestCase):
    def test_una_cita_inventada_no_pasa_y_el_formato_no_importa(self):
        texto = "1. **Parar la correa.** Pide la parada y espera a que quede quieta y vacía."
        borrador = {
            "pauta": {"pasos": [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]},
            "analisis": {"pasos": {"p1": {"cita": "Parar la correa. Pide la parada"},
                                   "p2": {"cita": "Engrasar el rodamiento"}}},
        }
        self.assertEqual(analisis.citas_sin_respaldo(borrador, texto), ["p2", "p3"])

    def test_una_cita_de_menos_de_cuatro_palabras_no_respalda_nada(self):
        borrador = {"pauta": {"pasos": [{"id": "p1"}, {"id": "p2"}]},
                    "analisis": {"pasos": {"p1": {"cita": "la"}, "p2": {"cita": "corta la energía y pon"}}}}
        self.assertEqual(analisis.citas_sin_respaldo(borrador, "Corta la energía y pon tu candado."), ["p1"])

    def test_una_negrita_pegada_a_una_coma_no_rompe_la_cita(self):
        borrador = {"pauta": {"pasos": [{"id": "p8"}]},
                    "analisis": {"pasos": {"p8": {"cita": "Sacar tu candado, con todos fuera de la correa."}}}}
        self.assertEqual(analisis.citas_sin_respaldo(borrador, "8. **Sacar tu candado**, con todos fuera de la correa."), [])


class Factibilidad(unittest.TestCase):
    def test_la_estacion_de_la_correa_cierra_todo_y_la_del_demo_no(self):
        self.assertFalse([f for f in analisis.factibilidad(POLIN, CORREA) if f["falta"]])
        faltan = {f["paso"] for f in analisis.factibilidad(POLIN, DEMO) if f["falta"]}
        self.assertEqual(faltan, {"p1", "p3", "p5", "p7", "p8"})  # correa, bloqueo y guarda no existen en el demo

    def test_un_valor_que_el_sensor_no_reporta_tampoco_sirve(self):
        estacion = {**CORREA, "sensores": {**CORREA["sensores"], "energia": ["viva"]}}
        self.assertIn("no reporta", analisis.factibilidad(POLIN, estacion)[1]["falta"])

    def test_lo_que_la_pauta_requiere_alcanza_para_ejecutarla(self):
        self.assertFalse([f for f in analisis.factibilidad(POLIN, analisis.requiere(POLIN)) if f["falta"]])


class SeCierranSolos(unittest.TestCase):
    def test_un_paso_que_espera_lo_que_otro_ya_dejo_se_delata(self):
        d = json.loads((DATOS / "pauta-polin.json").read_text(encoding="utf-8"))
        d["pasos"][3] = {**d["pasos"][3], "tipo_evidencia": "sensor", "sensor": {"id": "correa", "espera": "detenida"}}
        self.assertEqual(analisis.se_cierran_solos(catalogo.pauta_desde_dict(d)), ["p4"])  # p1 ya la dejó detenida

    def test_ninguna_pauta_de_datos_tiene_uno(self):
        for ruta in sorted(DATOS.glob("pauta-*.json")):
            self.assertEqual(analisis.se_cierran_solos(desde_json(ruta)), [], ruta.name)


class AlertasEnEjecucionCorrecta(unittest.TestCase):
    def test_una_pauta_que_pide_lo_que_una_regla_prohibe_se_delata(self):
        d = json.loads((DATOS / "pauta-polin.json").read_text(encoding="utf-8"))
        d["pasos"][1], d["pasos"][4] = {**d["pasos"][4], "orden": 2}, {**d["pasos"][1], "orden": 5}  # tapa antes que corriente
        d["pasos"][1]["sensor"], d["pasos"][0]["sensor"] = {"id": "guarda", "espera": "abierta"}, {"id": "energia", "espera": "viva"}
        r = analisis.alertas_en_ejecucion_correcta(catalogo.pauta_desde_dict(d))
        self.assertEqual([x["paso"] for x in r], ["p5"])
        self.assertIn("GUARDA ABIERTA", r[0]["aviso"])

    def test_ninguna_pauta_de_datos_dispara_una_regla_al_ejecutarse_bien(self):
        # La del demo físico reponía la corriente sin un paso que alejara al operario; desde la v5 lo tiene (e6).
        for ruta in sorted(DATOS.glob("pauta-*.json")):
            pasos = [a["paso"] for a in analisis.alertas_en_ejecucion_correcta(desde_json(ruta))]
            self.assertEqual(pasos, [], ruta.name)


class Criterio(unittest.TestCase):
    def test_solo_se_pide_analizar_lo_que_lo_necesita(self):
        r = analisis.criterio(POLIN, CORREA)
        self.assertEqual(pedidos(r, "instrumentar"), ["p4"])     # control crítico que cierra la palabra
        self.assertEqual(pedidos(r, "solucion-vision"), ["p6"])  # pregunta visual sin medir
        self.assertEqual(len(r), 2)                              # los otros ocho pasos no piden nada

    def test_una_pregunta_ya_medida_no_se_vuelve_a_pedir(self):
        r = analisis.criterio(POLIN, CORREA, preguntas_medidas={POLIN.paso("p6").pregunta_visual})
        self.assertEqual(pedidos(r, "solucion-vision"), [])

    def test_un_peligro_pide_regla_solo_si_no_existe_y_la_estacion_lo_mide(self):
        peligros = [
            {"que": "guarda abierta con corriente", "sensores": {"guarda": "abierta", "energia": "viva"}},  # ya existe
            {"que": "correa andando sin tapa", "sensores": {"correa": "en_marcha", "guarda": "abierta"}},
            {"que": "rodillo caliente", "sensores": {"temperatura_polin": "alta"}},
            {"que": "material pegado", "sensores": {}},
        ]
        r = analisis.criterio(POLIN, CORREA, peligros)
        self.assertEqual(pedidos(r, "regla-programatica"), ["correa andando sin tapa"])
        self.assertIn("rodillo caliente", pedidos(r, "instrumentar"))


class Historia(unittest.TestCase):
    def test_cuenta_ot_y_no_eventos_y_mide_el_tiempo_entre_pasos(self):
        V, C = Estado.VERIFICADO, Estado.EN_CONFLICTO
        ots = {
            "a": ot((2, "p1", V, 1), (3, "p2", C, 1), (4, "p2", C, 1), (6, "p2", V, 1), (7, "p3", V, None)),
            "b": ot((4, "p1", V, 1), (5, "alerta", {"pendiente": "p3", "clave": "orden:p5"}), (6, "p4", V, None)),
        }
        h = analisis.historia(POLIN, ots)
        self.assertIsNone(h["p1"]["segundos"])         # el primero incluiría la espera hasta que alguien toma la OT
        self.assertEqual(h["p2"]["segundos"], 240.0)   # de 2 a 6 minutos
        self.assertEqual(h["p2"]["conflicto"], 1)      # dos eventos, una OT
        self.assertEqual(h["p3"]["por_persona"], 1)    # sensor cerrado por una persona
        self.assertEqual(h["p3"]["alerta"], 1)
        self.assertEqual(h["p4"]["por_persona"], 0)    # un paso de confirmación siempre lo cierra una persona

    def test_con_poca_historia_no_se_propone_y_con_suficiente_si(self):
        C, V = Estado.EN_CONFLICTO, Estado.VERIFICADO
        una = ot((1, "p1", V, 1), (2, "p2", V, 1), (3, "p3", C, 1), (4, "p3", V, 1))
        pocas = analisis.historia(POLIN, {str(i): una for i in range(analisis.MIN_EJECUCIONES - 1)})
        self.assertEqual(analisis.criterio_de_historia(POLIN, pocas), [])
        varias = analisis.historia(POLIN, {str(i): una for i in range(analisis.MIN_EJECUCIONES)})
        self.assertEqual(pedidos(analisis.criterio_de_historia(POLIN, varias), "optimizar-proceso"), ["p3"])


class Comparar(unittest.TestCase):
    def test_una_pauta_calza_consigo_misma_y_no_con_la_que_junta_pasos(self):
        r = analisis.comparar(POLIN, POLIN)
        self.assertEqual((r["coinciden"], r["critico_igual"], r["sin_par"]), (10, 10, []))
        vieja = desde_json(DATOS / "pauta-correa.json")  # junta cortar y bloquear, y no prueba que no arranca
        self.assertLess(analisis.comparar(vieja, POLIN)["coinciden"], 10)


if __name__ == "__main__":
    unittest.main()
