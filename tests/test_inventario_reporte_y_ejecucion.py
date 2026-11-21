"""Lo que la API saca de la base para las skills (PRD de skills, sección 6): el inventario del servidor, el
validador de pautas, la capa y la confianza por paso, el reporte de una OT y la ejecución con login.

Correr:  uv run --with httpx python -m unittest tests.test_inventario_reporte_y_ejecucion
"""

import importlib.util
import json
import unittest

from app import db, protocolos

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None

SUPERVISORA, OPERADORA, OPERADOR = "carla.munoz@oculta.example", "ana.rojas@oculta.example", "bruno.diaz@oculta.example"


def pauta(nombre, **cambios):
    d = json.loads((protocolos.DATOS / f"{nombre}.json").read_text())
    return {**d, "version": d["version"] + 1, **cambios}


@unittest.skipUnless(TIENE_HTTPX, "requiere fastapi y httpx")
class Base(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        self.api = api
        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.accesos = {a["usuario"]: a["clave"] for a in self.c.post("/interno/ots/semilla").json()["accesos"]}
        self.carla, self.ana, self.bruno = (self.cabecera(u) for u in (SUPERVISORA, OPERADORA, OPERADOR))

    def cabecera(self, usuario):
        r = self.c.post("/auth/entrar", json={"usuario": usuario, "clave": self.accesos[usuario]})
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def ot_asignada(self, operador="operario:1"):
        ot = self.c.post("/cliente/ots", json={"pauta_id": "pauta-polin-demo"}, headers=self.carla).json()["ot"]
        self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": operador}, headers=self.carla)
        return ot

    def validar(self, d, **extra):
        r = self.c.post("/interno/pautas/validar", json={"pauta": d, **extra})
        self.assertEqual(r.status_code, 200)
        return r.json()


class ElInventario(Base):
    def test_cada_sensor_trae_lo_que_se_vio_en_la_bitacora_quien_lo_usa_y_que_peligro_lo_mira(self):
        inv = self.c.get("/interno/inventario").json()
        sensores = {s["id"]: s for s in inv["sensores"]}
        energia = sensores["energia"]
        self.assertEqual(set(energia["valores_vistos"]), {"viva", "cortada"})
        self.assertIn({"pauta": "pauta-polin-demo", "version": 1, "paso": "p1", "titulo": "Cortar la corriente del motor",
                       "espera": "cortada", "control_critico": True}, energia["pautas"])
        self.assertTrue(energia["reglas_de_peligro"])
        self.assertTrue(sensores["temp_c"]["numerico"])
        self.assertLess(sensores["temp_c"]["rango_visto"]["min"], sensores["temp_c"]["rango_visto"]["max"])
        self.assertIn("guarda", sensores)

    def test_las_clases_y_las_preguntas_visuales_salen_de_las_pautas_y_de_lo_que_respondio_la_camara(self):
        inv = self.c.get("/interno/inventario").json()
        clases = {c["clase"]: c for c in inv["clases"]}
        self.assertEqual({p["paso"] for p in clases["mouse"]["pautas"]}, {"l2", "l6"})
        self.assertIsNone(clases["mouse"]["en_el_modelo"])
        brazo = next(p for p in inv["preguntas_visuales"] if p["pauta"] == "pauta-brazo-01" and p["paso"] == "p5")
        self.assertEqual(brazo["confianza_media"], 0.62)
        self.assertEqual(len(inv["limites"]), 2)

    def test_con_el_detector_en_el_servidor_dice_que_clases_conoce(self):
        class Detector:
            modelo, clases = "yolo-prueba.onnx", ["mouse", "soda can"]
        self.api.detector = Detector()
        try:
            inv = self.c.get("/interno/inventario").json()
            clases = {c["clase"]: c for c in inv["clases"]}
            self.assertEqual((clases["mouse"]["en_el_modelo"], clases["pencil"]["en_el_modelo"]), (True, False))
            self.assertEqual(inv["detector"]["clases"], ["mouse", "soda can"])
            self.assertIn("I3", [h["regla"] for h in self.validar(pauta("pauta-loto"))["hallazgos"]])
        finally:
            self.api.detector = None


class ElValidador(Base):
    def test_las_pautas_del_repo_se_pueden_guardar_y_salen_los_huecos_ya_conocidos(self):
        loto = self.validar(pauta("pauta-loto"))
        self.assertEqual((loto["valida"], loto["errores"]), (True, []))
        self.assertEqual([(h["regla"], h["paso"]) for h in loto["hallazgos"]], [("V1", "l2"), ("V1", "l5")])
        polin = self.validar(pauta("pauta-polin"))
        self.assertEqual([(h["regla"], h["paso"]) for h in polin["hallazgos"]], [("V1", "p4")])
        self.assertIn("palabra del operario", polin["hallazgos"][0]["texto"])
        self.assertEqual(self.validar(pauta("pauta-polin-demo"))["hallazgos"], [])

    def test_no_guarda_nada(self):
        self.validar(pauta("pauta-polin-demo"))
        self.assertEqual([v["version"] for v in self.c.get("/pautas/pauta-polin-demo/versiones").json()], [1])

    def test_una_pauta_mal_formada_o_con_la_version_equivocada_no_se_puede_guardar(self):
        sin_pasos = self.validar(pauta("pauta-polin-demo", pasos=[]))
        self.assertFalse(sin_pasos["valida"])
        self.assertIn("sin pasos", sin_pasos["errores"][0])
        repetida = self.validar(pauta("pauta-polin-demo", version=1))
        self.assertFalse(repetida["valida"])
        self.assertIn("tiene que ser la 2", repetida["errores"][0])

    def test_un_paso_que_espera_el_valor_de_reposo_abre_una_alerta_de_orden(self):
        r = self.validar(pauta("pauta-loto"), reposo={"equipo": "frio"})
        self.assertIn(("V2", "l3"), [(h["regla"], h["paso"]) for h in r["hallazgos"]])
        self.assertEqual(r["reposo"]["equipo"], "frio")

    def test_la_reposicion_en_el_mismo_orden_y_la_capa_que_no_calza(self):
        d = pauta("pauta-polin-demo")
        pasos = {p["id"]: p for p in d["pasos"]}
        pasos["p7"]["orden"], pasos["p8"]["orden"] = 8, 7
        pasos["p4"]["capa_minima"] = 1
        r = self.validar({**d, "pasos": list(pasos.values())})
        reglas = {(h["regla"], h["paso"]) for h in r["hallazgos"]}
        self.assertIn(("V3", None), reglas)
        self.assertIn(("V4", "p4"), reglas)

    def test_un_sensor_o_un_valor_que_el_servidor_no_conoce(self):
        d = pauta("pauta-polin-demo")
        d["pasos"][0]["sensor"] = {"id": "termocupla_9", "espera": "fria"}
        d["pasos"][1]["sensor"] = {"id": "bloqueo", "espera": "trabado"}
        reglas = {(h["regla"], h["paso"]) for h in self.validar(d)["hallazgos"]}
        self.assertIn(("I1", "p1"), reglas)
        self.assertIn(("I2", "p2"), reglas)


class LaConfianzaPorPaso(Base):
    def test_cada_paso_dice_en_que_capa_cerro_con_que_confianza_en_cuantos_intentos_y_cuanto_tardo(self):
        pasos = {p["paso"]: p for p in self.c.get("/cliente/metricas/pautas/pauta-brazo-01/pasos", headers=self.carla).json()}
        p5 = pasos["p5"]
        self.assertEqual(p5["cerrado_en_capa"], {"3": 1})
        self.assertEqual(p5["confianza"]["bajo_el_umbral"], 1)
        self.assertEqual(p5["confianza"]["min"], 0.62)
        self.assertIsNone(pasos["p1"]["segundos_medios"])
        sensor = next(p for p in pasos.values() if p["tipo_evidencia"] == "sensor" and p["verificado"] and p["orden"] > 1)
        self.assertEqual(sensor["cerrado_en_capa"], {"1": sensor["verificado"]})
        self.assertGreaterEqual(sensor["intentos_medios"], 1)
        self.assertGreater(sensor["segundos_medios"], 0)


class ElReporte(Base):
    def test_el_reporte_de_una_ot_completa_trae_cada_paso_con_su_evidencia_y_cada_desviacion_con_su_evento(self):
        r = self.c.get("/cliente/ots/ot-1001/reporte", headers=self.carla).json()
        self.assertEqual((r["completa"], r["resultado"]["pasos_verificados"], r["pendientes"]), (True, 8, []))
        self.assertEqual(r["personas"]["a_cargo"], "Ana Rojas")
        self.assertEqual(r["pasos"][0]["cerrado_con"], {"con": "sensor", "sensor": "energia", "leido": "cortada", "esperado": "cortada"})
        clases = {d["clase"] for d in r["desviaciones"]}
        self.assertTrue({"seguridad", "orden", "senal"} <= clases)
        self.assertTrue(all(d["minutos"] is not None for d in r["desviaciones"] if d["clase"] == "seguridad"))

    def test_no_omite_ninguna_alerta_y_cada_evento_citado_existe(self):
        for ot in ("ot-1001", "ot-1003", "ot-1004", "ot-1008"):
            r = self.c.get(f"/cliente/ots/{ot}/reporte", headers=self.carla).json()
            eventos = {e["id"]: e for e in self.c.get(f"/cliente/ots/{ot}/eventos", headers=self.carla).json()}
            alertas = {i for i, e in eventos.items() if e["tipo"] == "alerta"}
            self.assertEqual(alertas, {d["evento"] for d in r["desviaciones"] if d["clase"] != "conflicto"}, ot)
            citados = [p["evento"] for p in r["pasos"] if p["evento"]] + [d["evento"] for d in r["desviaciones"]]
            self.assertTrue(set(citados) <= set(eventos), ot)
            for p in r["pasos"]:
                if p["estado"] == "verificado":
                    self.assertEqual((eventos[p["evento"]]["paso_id"], eventos[p["evento"]]["estado"]), (p["paso"], "verificado"))

    def test_en_markdown_se_lee_y_cita_los_eventos(self):
        r = self.c.get("/cliente/ots/ot-1001/reporte?formato=markdown", headers=self.carla)
        self.assertIn("text/markdown", r.headers["content-type"])
        texto = r.text
        self.assertTrue(texto.startswith("# OT ot-1001 · "))
        for d in self.c.get("/cliente/ots/ot-1001/reporte", headers=self.carla).json()["desviaciones"]:
            self.assertIn(f"evento {d['evento']}", texto)
        self.assertIn("Nada de este reporte lo redactó un modelo", texto)

    def test_lo_lee_quien_tiene_la_ot_y_su_supervisor(self):
        self.assertEqual(self.c.get("/cliente/ots/ot-1001/reporte", headers=self.ana).status_code, 200)
        self.assertEqual(self.c.get("/cliente/ots/ot-1001/reporte", headers=self.bruno).status_code, 404)
        self.assertEqual(self.c.get("/cliente/ots/ot-1001/reporte").status_code, 401)


class LaEjecucionConLogin(Base):
    def test_quien_declara_sale_del_token_y_queda_en_la_bitacora(self):
        ot = self.ot_asignada()
        self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": "edge-login"}, headers=self.ana)
        self.assertEqual(self.c.get(f"/cliente/ots/{ot}/pasos", headers=self.ana).json()["paso_actual"], "p1")
        r = self.c.post(f"/cliente/ots/{ot}/declarar", json={"texto": "corté la corriente", "actor": "operario:2"}, headers=self.ana)
        self.assertEqual(r.status_code, 200)
        declaracion = [e for e in self.c.get(f"/cliente/ots/{ot}/eventos", headers=self.ana).json() if e["tipo"] == "declaracion"]
        self.assertEqual([e["actor"] for e in declaracion], ["operario:1"])
        self.assertEqual(r.json()["estado"], "no_verificado")

    def test_solo_el_operador_que_tiene_la_ot_declara_y_el_supervisor_puede_confirmar(self):
        ot = self.ot_asignada()
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/declarar", json={"texto": "x"}, headers=self.bruno).status_code, 404)
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/declarar", json={"texto": "x"}, headers=self.carla).status_code, 403)
        r = self.c.post(f"/cliente/ots/{ot}/pasos/p1/confirmar", json={"motivo": "el sensor de energía no está conectado"}, headers=self.carla)
        self.assertEqual((r.status_code, r.json()["evidencia"]["tipo"]), (200, "persona"))
        self.assertIn("supervisor:oculta", r.json()["detalle"])
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/pasos/p3/confirmar", json={"motivo": "x"}, headers=self.ana).status_code, 409)

    def test_el_relevo_pasa_la_ot_de_un_operador_a_otro(self):
        ot = self.ot_asignada()
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/relevo/recibir", headers=self.bruno).status_code, 409)
        r = self.c.post(f"/cliente/ots/{ot}/relevo/entregar", headers=self.ana)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.c.get(f"/cliente/ots/{ot}", headers=self.carla).json()["estado_general"], "entregada")
        self.assertNotIn(ot, [o["ot"] for o in self.c.get("/cliente/ots", headers=self.ana).json()])
        r = self.c.post(f"/cliente/ots/{ot}/relevo/recibir", headers=self.bruno)
        self.assertEqual((r.status_code, r.json()["firmado_por"]), (200, "operario:2"))
        self.assertIn(ot, [o["ot"] for o in self.c.get("/cliente/ots", headers=self.bruno).json()])
        relevos = self.c.get(f"/cliente/ots/{ot}/reporte", headers=self.carla).json()["relevos"]
        self.assertEqual([(x["que"], x["quien"]) for x in relevos], [("entregado", "Ana Rojas"), ("recibido", "Bruno Díaz")])

    def test_una_ot_completa_no_se_declara_ni_se_entrega(self):
        self.assertEqual(self.c.post("/cliente/ots/ot-1014/declarar", json={"texto": "x"}, headers=self.ana).status_code, 409)
        self.assertEqual(self.c.post("/cliente/ots/ot-1014/relevo/entregar", headers=self.ana).status_code, 409)


if __name__ == "__main__":
    unittest.main()
