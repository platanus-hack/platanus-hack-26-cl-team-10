"""El banco de pruebas /casos: cada criterio del PRD se corre contra un servidor vivo.

Correr:  uv run --with httpx python -m unittest tests.test_casos
Lo que el banco comprueba al correr se ve en el navegador; acá se vigila que exista,
que no se desfase del PRD y que no deje el servidor distinto de como lo encontró.
"""

import importlib.util
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PRD = RAIZ / "knowledge" / "projects" / "servicios-en-vivo" / "PRD.md"
BANCO = RAIZ / "app" / "estatico" / "casos.html"
EL_BANCO_MISMO = "CA15"

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


class ElBancoSigueAlPRD(unittest.TestCase):
    def setUp(self):
        self.criterios = re.findall(r"\*\*(CA\d+) —\*\*", PRD.read_text(encoding="utf-8"))
        self.tarjetas = re.findall(r'id: "(CA\d+)"', BANCO.read_text(encoding="utf-8"))

    def test_cada_criterio_del_prd_tiene_su_tarjeta(self):
        self.assertGreaterEqual(len(self.criterios), 14)
        sin_tarjeta = [c for c in self.criterios if c != EL_BANCO_MISMO and c not in self.tarjetas]
        self.assertEqual(sin_tarjeta, [])

    def test_ninguna_tarjeta_prueba_un_criterio_que_el_prd_no_tiene(self):
        self.assertEqual([t for t in self.tarjetas if t not in self.criterios], [])

    def test_cada_tarjeta_dice_que_test_la_cubre_y_ese_archivo_existe(self):
        archivos = re.findall(r'test: "(tests/[\w.]+)', BANCO.read_text(encoding="utf-8"))
        self.assertEqual(len(archivos), len(self.tarjetas))
        self.assertEqual([a for a in archivos if not (RAIZ / a).exists()], [])


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class ElBancoSeSirve(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api, db
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)

    def test_la_pagina_se_sirve_en_casos(self):
        r = self.c.get("/casos")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Correr todos", r.text)

    def test_la_pagina_trae_la_matriz_de_escenarios_y_el_servidor_la_corre(self):
        self.assertIn("Escenarios por industria", self.c.get("/casos").text)
        catalogo = self.c.get("/escenarios").json()
        self.assertEqual(len(catalogo), 72)
        r = self.c.post("/escenarios/correr").json()
        self.assertEqual({x["sello"] for x in r}, {"pasa"})
        uno = self.c.post("/escenarios/MIN-B2/correr").json()
        self.assertEqual(uno["sello"], "pasa")
        self.assertTrue(uno["bitacora"] and uno["stream"])
        self.assertEqual(self.c.post("/escenarios/NO-EXISTE/correr").status_code, 404)

    def test_cada_industria_tiene_su_seccion_con_trasfondo_arquitectura_y_tests(self):
        texto = self.c.get("/casos").text
        for ancla in ("mineria", "electrica", "construccion"):
            self.assertIn(f'href="#{ancla}"', texto)
        r = self.c.get("/industrias").json()
        self.assertEqual([i["codigo"] for i in r["industrias"]], ["MIN", "ELE", "CON"])
        for i in r["industrias"]:
            with self.subTest(i["codigo"]):
                self.assertGreaterEqual(len(i["trasfondo"]), 3)
                self.assertTrue(all("REFERENCIAS" in t["texto"] for t in i["trasfondo"][:2]))
                self.assertGreaterEqual(len(i["reglas"]), 3)
                self.assertGreaterEqual(len(i["tests"]), 26)
                corren = [t for t in i["tests"] if t["escenario"]]
                self.assertGreaterEqual(len(corren), 24)
        piezas = r["arquitectura"]
        self.assertIn("POST /edge/{id}/lecturas", piezas["controladores"])
        self.assertEqual({t["id"] for t in piezas["tablas"]} >= {"sensores", "eventos", "sesiones"}, True)

    def test_un_test_de_industria_trae_su_recorrido_por_controladores_servicios_y_tablas(self):
        r = self.c.post("/escenarios/MIN-B2/correr").json()
        tramos = r["recorrido"]
        self.assertEqual([t["accion"] for t in tramos], ["preparar", "lee", "lee"])
        self.assertEqual(tramos[1]["controladores"], ["POST /edge/{id}/lecturas"])
        self.assertIn("orden", tramos[1]["disparan"])
        self.assertIn("eventos", tramos[1]["tablas"])
        self.assertEqual((tramos[1]["nivel"], tramos[2]["nivel"]), ("error", "ok"))

    def test_la_guia_la_nombra_y_no_la_lista_como_endpoint(self):
        guia = self.c.get("/agente").text
        self.assertIn("http://testserver/casos", guia)
        self.assertNotIn("| `/casos` |", guia)

    def test_la_camara_acepta_el_edge_de_la_corrida_por_la_url(self):
        self.assertIn('get("edge")', self.c.get("/camara").text)

    def test_una_corrida_deja_los_sensores_como_estaban_y_no_toca_otra_ot(self):
        """La secuencia que el banco usa para aislarse: lo de antes vuelve y la OT ajena no se entera."""
        self.c.post("/pauta/demo")
        self.c.post("/ot/ot-ajena/abrir")
        self.c.post("/ot/ot-ajena/sesion", json={"edge_id": "edge-1", "operario": "operario:A"})
        self.c.post("/edge/edge-1/lecturas", json=[{"sensor_id": "energia", "valor": "viva"}])
        antes = self.c.get("/sensores").json()
        bitacora_ajena = self.c.get("/ot/ot-ajena/eventos").json()

        edge = "casos-edge-ca5-prueba"
        seguro = [{"sensor_id": "guarda", "valor": "cerrada"}, {"sensor_id": "energia", "valor": "cortada"},
                  {"sensor_id": "reed_bloqueo", "valor": "abierto"}]
        self.c.post(f"/edge/{edge}/lecturas", json=seguro)
        self.c.post("/ot/casos-ca5-prueba/abrir")
        self.c.post("/ot/casos-ca5-prueba/sesion", json={"edge_id": edge, "operario": "operario:casos"})
        self.c.post(f"/edge/{edge}/lecturas", json=[{"sensor_id": "energia", "valor": "viva"},
                                                    {"sensor_id": "guarda", "valor": "abierta"}])
        claves = [a["evidencia"]["clave"].split(":")[0] for a in self.c.get("/ot/casos-ca5-prueba/alertas").json()]
        self.assertEqual(sorted(claves), ["orden", "seguridad"])

        self.c.post(f"/edge/{edge}/lecturas", json=seguro[:2])
        self.assertEqual(self.c.delete(f"/edge/{edge}/sesion").status_code, 204)
        self.c.post(f"/edge/{edge}/lecturas", json=[{"sensor_id": k, "valor": v} for k, v in antes.items()])

        self.assertEqual(self.c.get("/ot/casos-ca5-prueba/alertas").json(), [])
        self.assertEqual({k: self.c.get("/sensores").json()[k] for k in antes}, antes)
        self.assertEqual(self.c.get("/ot/ot-ajena/eventos").json(), bitacora_ajena)
        self.assertEqual([s["edge_id"] for s in self.c.get("/sesiones").json()], ["edge-1"])


if __name__ == "__main__":
    unittest.main()
