"""El recorrido interno completo, por HTTP y con la clave del equipo: del protocolo a la mejora continua (ADR-0016).

Correr:  uv run --with httpx python -m unittest tests.test_recorrido_interno

1. El equipo carga un protocolo con sus controles críticos y escribe una pauta a la que le falta uno.
2. El validador lo dice antes de guardarla, y la pauta se aprueba igual: la falta queda como hallazgo.
3. El supervisor ve el hallazgo de conformidad apenas la pauta se le habilita, sin esperar ninguna OT.
4. Las OT corren; el operario se acerca sin cortar la energía en todas, y a la quinta el supervisor recibe la
   recomendación por desviación recurrente (a la tercera si el paso saltado no fuera control crítico).
5. El supervisor acepta las dos; el equipo las ve en /interno/mejoras.
6. El equipo escribe una versión que saca el candado: no se aprueba. Escribe otra que agrega la prueba que faltaba: sí.
7. Con las OT de la versión nueva, sin desviarse, la propuesta por desviación dice «mejoró» y la de conformidad, también.
"""

import copy
import importlib.util
import os
import unittest
from unittest import mock

from app import db

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None
CLAVE = {"X-Clave-Equipo": "secreta"}

PROTOCOLO = {
    "id": "prot-prueba-01", "nombre": "Cambio de rodillo de prueba", "actor": "equipo:factum", "industria": "mineria",
    "texto": "## Alcance\nToda mantención del rodillo de prueba.\n## El control crítico\nAislar, bloquear y comprobar.",
    "controles": [
        {"id": "A1", "nombre": "Aislar", "orden": 1},
        {"id": "A2", "nombre": "Bloquear", "orden": 2},
        {"id": "A3", "nombre": "Comprobar energía cero", "orden": 3},
    ],
}


def paso(i, titulo, sensor=None, espera=None, critico=False, cumple=(), tipo="sensor"):
    d = {"id": f"p{i}", "orden": i, "titulo": titulo, "instruccion": titulo, "tipo_evidencia": tipo, "capa_minima": 1,
         "control_critico": critico}
    if sensor:
        d["sensor"] = {"id": sensor, "espera": espera}
    if cumple:
        d["cumple"] = [f"prot-prueba-01:{c}" for c in cumple]
    return d


V1 = {"id": "pauta-prueba-01", "nombre": "Cambio de rodillo de prueba", "version": 1, "equipo": "rodillo de prueba",
      "pasos": [
          paso(1, "Cortar la energía", "energia", "cortada", True, ["A1"]),
          paso(2, "Poner tu candado", "bloqueo", "puesto", True, ["A2"]),
          paso(3, "Acercarte al rodillo", "operario", "presente"),
          paso(4, "Alejarte del rodillo", "operario", "ausente", True),
          paso(5, "Sacar tu candado", "bloqueo", "retirado", True),
          paso(6, "Devolver la energía", "energia", "viva", True),
      ]}


@unittest.skipUnless(TIENE_HTTPX, "falta httpx o fastapi")
class DelProtocoloALaMejoraContinua(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.entorno = mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"})
        self.entorno.start()
        accesos = {a["usuario"]: a["clave"] for a in self.c.post("/interno/ots/semilla", headers=CLAVE).json()["accesos"]}
        self.carla = self.login("carla.munoz@oculta.example", accesos)
        self.ana = self.login("ana.rojas@oculta.example", accesos)
        self.n = 0

    def tearDown(self):
        self.entorno.stop()

    def login(self, usuario, accesos):
        token = self.c.post("/auth/entrar", json={"usuario": usuario, "clave": accesos[usuario]}).json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def mejoras(self, pauta="pauta-prueba-01"):
        return [m for m in self.c.get("/cliente/mejoras", headers=self.carla).json() if m["pauta"] == pauta]

    def ot(self, acercarse_con_energia: bool):
        """Una OT de punta a punta por el servicio del cliente y el edge."""
        self.n += 1
        ot = self.c.post("/cliente/ots", json={"pauta_id": "pauta-prueba-01"}, headers=self.carla).json()["ot"]
        self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": "operario:1"}, headers=self.carla)
        edge = f"edge-recorrido-{self.n}"
        lecturas = [("energia", "viva"), ("bloqueo", "retirado"), ("operario", "ausente")]
        self.c.post(f"/edge/{edge}/lecturas", json=[{"sensor_id": s, "valor": v} for s, v in lecturas])
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": edge}, headers=self.ana).status_code, 200)
        orden = [("energia", "cortada"), ("bloqueo", "puesto")]
        if acercarse_con_energia:
            orden = [("operario", "presente"), ("operario", "ausente"), *orden]
        pauta = self.c.get(f"/cliente/ots/{ot}/pasos", headers=self.ana).json()
        if any(p["tipo_evidencia"] == "confirmacion" for p in pauta["pasos"]):
            orden.append(("declarar", None))
        orden += [("operario", "presente"), ("operario", "ausente"), ("bloqueo", "retirado"), ("energia", "viva")]
        for s, v in orden:
            if s == "declarar":
                self.c.post(f"/cliente/ots/{ot}/declarar", json={"texto": "probé que no arranca"}, headers=self.ana)
            else:
                self.c.post(f"/edge/{edge}/lecturas", json=[{"sensor_id": s, "valor": v}])
        self.c.delete(f"/edge/{edge}/sesion", headers=CLAVE)
        return ot

    def test_del_protocolo_a_la_version_que_deja_de_desviarse(self):
        # 1 y 2 · el protocolo con sus controles; el validador ve la falta antes de guardar
        self.assertEqual(self.c.post("/interno/protocolos", json=PROTOCOLO, headers=CLAVE).status_code, 201)
        v = self.c.post("/interno/pautas/validar", json={"pauta": V1, "protocolo_id": "prot-prueba-01"}, headers=CLAVE).json()
        self.assertTrue(v["valida"])
        self.assertIn(("C1", "prot-prueba-01: ningún paso cumple A3 Comprobar energía cero"),
                      [(h["regla"], h["texto"]) for h in v["hallazgos"]])
        r = self.c.post("/interno/protocolos/prot-prueba-01/pautas", json={"pauta": V1, "actor": "equipo:factum"}, headers=CLAVE)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(self.c.post("/pautas/pauta-prueba-01/versiones/1/aprobar", json={"actor": "equipo:pancho"},
                                     headers=CLAVE).status_code, 200)
        self.c.put("/interno/clientes/oculta/pautas/pauta-prueba-01", headers=CLAVE)

        # 3 · el hallazgo ya está, sin ninguna OT
        [conf] = self.mejoras()
        self.assertEqual((conf["tipo"], conf["conformidad"]["control"], conf["estado"]), ("conformidad", "A3", "abierta"))
        self.assertIsNotNone(conf["detectada"])

        # 4 · OT acercándose con la energía viva, hasta que llega la recomendación. «Cortar la energía» es control
        # crítico, así que cada incidente deja dos señales: seguridad en p1 y orden en p3, el paso que se adelantó. Las
        # dos se inflan la tasa de referencia y con el α repartido del aviso (mejora.alfa_en_vivo) hacen falta 6 OT.
        llego_en = None
        for i in range(1, 7):
            self.ot(acercarse_con_energia=True)
            desv = [m for m in self.mejoras() if m["tipo"] == "desviacion" and m["detectada"]]
            if desv:
                llego_en = i
                break
        self.assertEqual(llego_en, 6)
        desv = next(m for m in desv if m["paso"] == "p1")
        self.assertEqual((desv["paso"], desv["titulo"]), ("p1", "Cortar la energía"))
        self.assertGreaterEqual(desv["senales"]["seguridad"], 3)

        # 5 · el supervisor acepta las dos; el equipo las sigue
        for m in (conf, desv):
            self.assertEqual(self.c.post(f"/cliente/mejoras/{m['id']}/revision", json={"decision": "aceptar", "nota": ""},
                                         headers=self.carla).status_code, 200)
        aceptadas = {m["id"] for m in self.c.get("/interno/mejoras", headers=CLAVE).json() if m["cliente"]["id"] == "oculta"}
        self.assertLessEqual({conf["id"], desv["id"]}, aceptadas)

        # 6 · una versión que saca el candado no se aprueba; una que agrega la prueba, sí
        sin_candado = copy.deepcopy(V1) | {"version": 2}
        sin_candado["pasos"] = [p for p in sin_candado["pasos"] if p["id"] != "p2"]
        self.c.post("/interno/protocolos/prot-prueba-01/pautas", json={"pauta": sin_candado, "actor": "equipo:factum"}, headers=CLAVE)
        r = self.c.post("/pautas/pauta-prueba-01/versiones/2/aprobar", json={"actor": "equipo:pancho"}, headers=CLAVE)
        self.assertEqual(r.status_code, 409)
        self.assertIn("pierde controles críticos", r.json()["regla"])
        self.assertIn("A2 Bloquear", r.json()["regla"])

        con_prueba = copy.deepcopy(V1) | {"version": 3}
        pasos = con_prueba["pasos"]
        pasos.insert(2, paso(3, "Probar que no arranca", critico=True, cumple=["A3"], tipo="confirmacion"))
        for i, p in enumerate(pasos, 1):
            p["orden"] = i
            p["id"] = f"p{i}"
        self.assertEqual(self.c.post("/interno/pautas/validar", json={"pauta": con_prueba}, headers=CLAVE).json()["conformidad"]["hallazgos"], [])
        self.c.post("/interno/protocolos/prot-prueba-01/pautas", json={"pauta": con_prueba, "actor": "equipo:factum"}, headers=CLAVE)
        self.assertEqual(self.c.post("/pautas/pauta-prueba-01/versiones/3/aprobar", json={"actor": "equipo:pancho"},
                                     headers=CLAVE).status_code, 200)

        # 7 · seis OT de la versión 3, en orden: las dos propuestas se cierran
        for _ in range(6):
            self.ot(acercarse_con_energia=False)
        por_id = {m["id"]: m for m in self.mejoras()}
        self.assertEqual((por_id[conf["id"]]["estado"], por_id[conf["id"]]["validacion"]["resultado"]), ("aplicada", "mejoro"))
        d = por_id[desv["id"]]
        self.assertEqual((d["estado"], d["validacion"]["version_nueva"], d["validacion"]["ots_con_senal"]), ("aplicada", 3, 0))
        self.assertEqual(d["validacion"]["resultado"], "mejoro", d["validacion"])
        self.assertLess(d["validacion"]["p_valor"], 0.05)
