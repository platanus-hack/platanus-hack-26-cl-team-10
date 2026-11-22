"""Cada protocolo de cada empresa itera por separado (ADR-0018). Por HTTP y con la clave del equipo.

Correr:  uv run --with httpx python -m unittest tests.test_protocolo_por_empresa

Factum copia `prot-correa-01` de su biblioteca para dos plantas de Oculta y para otra empresa. Cada copia trae sus
pautas, con `cumple` apuntando a las copias de sus protocolos; el de aislamiento se copia una vez por empresa. La
versión nueva de una copia no toca a las otras, cada propuesta dice su protocolo dueño y las métricas se agrupan por él.
"""

import copy
import importlib.util
import os
import unittest
from unittest import mock

from app import analisis, catalogo, db

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None
CLAVE = {"X-Clave-Equipo": "secreta"}
A = "prot-correa-01--oculta--planta-a"
B = "prot-correa-01--oculta--planta-b"
OTRA = "prot-correa-01--andina"


@unittest.skipUnless(TIENE_HTTPX, "falta httpx o fastapi")
class CadaProtocoloIteraSolo(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.cx = api.cx
        self.c = TestClient(api.app)
        self.entorno = mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"})
        self.entorno.start()
        accesos = {a["usuario"]: a["clave"] for a in self.c.post("/interno/ots/semilla", headers=CLAVE).json()["accesos"]}
        self.carla = self.login("carla.munoz@oculta.example", accesos["carla.munoz@oculta.example"])
        self.ana = self.login("ana.rojas@oculta.example", accesos["ana.rojas@oculta.example"])
        self.assertEqual(self.c.post("/interno/clientes", json={"id": "andina", "nombre": "Minera Andina"}, headers=CLAVE).status_code, 201)
        claves = {}
        for pid, nombre, usuario, rol in (("supervisor:andina", "Rosa", "rosa@andina.example", "supervisor"),
                                          ("operario:andina", "Luis", "luis@andina.example", "operador")):
            r = self.c.post("/interno/clientes/andina/personas",
                            json={"id": pid, "nombre": nombre, "usuario": usuario, "rol": rol}, headers=CLAVE)
            self.assertEqual(r.status_code, 201, r.text)
            claves[usuario] = r.json()["clave"]
        self.rosa = self.login("rosa@andina.example", claves["rosa@andina.example"])
        self.luis = self.login("luis@andina.example", claves["luis@andina.example"])
        self.copias = {}
        for cliente, sufijo in (("oculta", "planta-a"), ("oculta", "planta-b"), ("andina", None)):
            r = self.c.post(f"/interno/clientes/{cliente}/protocolos",
                            json={"base": "prot-correa-01", "actor": "equipo:factum", "sufijo": sufijo}, headers=CLAVE)
            self.assertEqual(r.status_code, 201, r.text)
            self.copias[r.json()["protocolo"]["id"]] = r.json()

    def tearDown(self):
        self.entorno.stop()

    def login(self, usuario, clave):
        token = self.c.post("/auth/entrar", json={"usuario": usuario, "clave": clave}).json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def ot_con_conflicto(self, pauta_id, supervisor, operador_h, operador_id, edge):
        """Una OT donde el operario declara «Parar la correa» sin que el sensor lo muestre: deja un conflicto en p1."""
        ot = self.c.post("/cliente/ots", json={"pauta_id": pauta_id}, headers=supervisor).json()["ot"]
        self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": operador_id}, headers=supervisor)
        self.c.post(f"/edge/{edge}/lecturas", json=[{"sensor_id": "correa", "valor": "en_marcha"}])
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": edge}, headers=operador_h).status_code, 200)
        self.c.post(f"/cliente/ots/{ot}/declarar", json={"texto": "paré la correa"}, headers=operador_h)
        self.c.post(f"/edge/{edge}/lecturas", json=[{"sensor_id": "correa", "valor": "detenida"}])
        self.c.delete(f"/edge/{edge}/sesion", headers=CLAVE)
        return ot

    # ─── La copia ──────────────────────────────────────────────────────────

    def test_cada_copia_trae_sus_pautas_y_comparte_el_aislamiento_dentro_de_la_empresa(self):
        self.assertEqual(sorted(self.copias), [OTRA, A, B])
        a = self.copias[A]
        self.assertEqual(sorted(p["id"] for p in a["pautas"]),
                         ["pauta-correa-ct-01--oculta--planta-a", "pauta-polin-ct-01--oculta--planta-a"])
        self.assertEqual(a["tambien_aplican"], ["prot-aislamiento-01--oculta"])
        self.assertEqual(self.copias[B]["tambien_aplican"], ["prot-aislamiento-01--oculta"])  # una sola vez por empresa
        self.assertEqual(self.copias[OTRA]["tambien_aplican"], ["prot-aislamiento-01--andina"])
        prot = self.c.get(f"/interno/protocolos/{A}", headers=CLAVE).json()
        self.assertEqual((prot["cliente"], prot["origen"]), ("oculta", "adaptado de prot-correa-01"))
        self.assertEqual(sorted(prot["propias"]), sorted(p["id"] for p in a["pautas"]))
        aisl = self.c.get("/interno/protocolos/prot-aislamiento-01--oculta", headers=CLAVE).json()
        self.assertEqual([c["id"] for c in aisl["controles"]], ["A1", "A2", "A3"])
        self.assertEqual(catalogo.protocolo_dueno(self.cx, "pauta-polin-ct-01--oculta--planta-a"), A)
        self.assertEqual(catalogo.protocolo_dueno(self.cx, "pauta-polin-ct-01"), "prot-correa-01")  # la de la biblioteca

    def test_cumple_apunta_a_las_copias_y_la_conformidad_da_lo_mismo_que_en_la_base(self):
        polin = db.leer_pauta(self.cx, "pauta-polin-ct-01--oculta--planta-a", 1)
        self.assertEqual([c for p in polin.en_orden for c in p.cumple],
                         [f"prot-aislamiento-01--oculta:{c}" for c in ("A1", "A2", "A3")])
        def hallazgos(pauta_id):
            pauta = db.leer_pauta(self.cx, pauta_id, 1)
            return sorted((h["tipo"], h["control"]) for h in analisis.conformidad(pauta, catalogo.controles_de(self.cx, pauta_id))["hallazgos"])
        self.assertEqual(hallazgos("pauta-polin-ct-01--oculta--planta-a"), [])
        base = hallazgos("pauta-correa-ct-01")
        self.assertEqual(base, [("falta", "A3"), ("juntos", "A1+A2")])
        for marca in ("oculta--planta-a", "oculta--planta-b", "andina"):
            self.assertEqual(hallazgos(f"pauta-correa-ct-01--{marca}"), base, marca)

    def test_cada_copia_se_habilita_solo_para_su_empresa(self):
        de_oculta = {p["id"] for p in self.c.get("/cliente/pautas", headers=self.carla).json()}
        de_andina = {p["id"] for p in self.c.get("/cliente/pautas", headers=self.rosa).json()}
        self.assertIn("pauta-polin-ct-01--oculta--planta-a", de_oculta)
        self.assertIn("pauta-polin-ct-01--oculta--planta-b", de_oculta)
        self.assertNotIn("pauta-polin-ct-01--andina", de_oculta)
        self.assertEqual({p for p in de_andina if "--" in p}, {"pauta-correa-ct-01--andina", "pauta-polin-ct-01--andina"})
        r = self.c.post("/cliente/ots", json={"pauta_id": "pauta-polin-ct-01--oculta--planta-a"}, headers=self.rosa)
        self.assertEqual(r.status_code, 403)

    # ─── En paralelo ───────────────────────────────────────────────────────

    def test_la_version_nueva_de_una_planta_no_toca_a_la_otra_ni_a_otra_empresa(self):
        b = "pauta-polin-ct-01--oculta--planta-b"
        for i in range(2):
            self.ot_con_conflicto(b, self.carla, self.ana, "operario:1", f"edge-b-{i}")
        [antes] = [m for m in self.c.get("/cliente/mejoras", headers=self.carla).json() if m["pauta"] == b and m["tipo"] == "desviacion"]
        self.assertEqual((antes["paso"], antes["estado"], antes["protocolo_dueno"]), ("p1", "abierta", B))

        a = "pauta-polin-ct-01--oculta--planta-a"
        v2 = copy.deepcopy(catalogo.leer_pauta(self.cx, a, 1)) | {"version": 2}
        v2.pop("aprobada")
        v2["pasos"][0]["instruccion"] = "Detén la correa y espera a que el sensor la vea detenida antes de seguir."
        self.assertEqual(self.c.post(f"/interno/protocolos/{A}/pautas", json={"pauta": v2, "actor": "equipo:factum"}, headers=CLAVE).status_code, 201)
        self.assertEqual(self.c.post(f"/pautas/{a}/versiones/2/aprobar", json={"actor": "equipo:pancho"}, headers=CLAVE).status_code, 200)

        self.assertEqual(self.c.post("/cliente/ots", json={"pauta_id": a}, headers=self.carla).json()["version"], 2)
        self.assertEqual(self.c.post("/cliente/ots", json={"pauta_id": b}, headers=self.carla).json()["version"], 1)
        self.assertEqual(self.c.post("/cliente/ots", json={"pauta_id": "pauta-polin-ct-01--andina"}, headers=self.rosa).json()["version"], 1)
        [despues] = [m for m in self.c.get("/cliente/mejoras", headers=self.carla).json() if m["id"] == antes["id"]]
        self.assertEqual((despues["estado"], despues["validacion"]), ("abierta", None))  # no la supera la versión de otra planta

    def test_las_metricas_se_agrupan_por_protocolo_dueno_y_cada_empresa_ve_los_suyos(self):
        for i in range(2):
            self.ot_con_conflicto("pauta-polin-ct-01--oculta--planta-a", self.carla, self.ana, "operario:1", f"edge-a-{i}")
        self.ot_con_conflicto("pauta-polin-ct-01--oculta--planta-b", self.carla, self.ana, "operario:1", "edge-b")
        self.ot_con_conflicto("pauta-polin-ct-01--andina", self.rosa, self.luis, "operario:andina", "edge-andina")
        de_oculta = {g["protocolo"]: g for g in self.c.get("/cliente/metricas/protocolos", headers=self.carla).json()}
        self.assertEqual((de_oculta[A]["ots"], de_oculta[B]["ots"]), (2, 1))
        self.assertEqual(de_oculta[A]["pautas"], ["pauta-polin-ct-01--oculta--planta-a"])
        self.assertEqual(de_oculta[A]["versiones"], {"pauta-polin-ct-01--oculta--planta-a": [1]})
        self.assertNotIn(OTRA, de_oculta)
        de_andina = {g["protocolo"] for g in self.c.get("/cliente/metricas/protocolos", headers=self.rosa).json()}
        self.assertEqual(de_andina, {OTRA})

    # ─── Lo que no se puede ────────────────────────────────────────────────

    def test_lo_que_no_se_puede(self):
        dos_veces = self.c.post("/interno/clientes/oculta/protocolos",
                                json={"base": "prot-correa-01", "actor": "equipo:factum", "sufijo": "planta-a"}, headers=CLAVE)
        self.assertEqual(dos_veces.status_code, 409)
        de_empresa = self.c.post("/interno/clientes/oculta/protocolos", json={"base": A, "actor": "equipo:factum"}, headers=CLAVE)
        self.assertEqual(de_empresa.status_code, 409)
        self.assertIn("biblioteca", de_empresa.json()["regla"])
        sin_empresa = self.c.post("/interno/clientes/nadie/protocolos", json={"base": "prot-correa-01", "actor": "equipo:factum"}, headers=CLAVE)
        self.assertEqual(sin_empresa.status_code, 404)
        sin_clave = self.c.post("/interno/clientes/oculta/protocolos", json={"base": "prot-correa-01", "actor": "equipo:factum", "sufijo": "x"})
        self.assertEqual(sin_clave.status_code, 401)


if __name__ == "__main__":
    unittest.main()
