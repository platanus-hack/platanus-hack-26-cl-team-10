"""La referencia de la API dice lo que el servidor hace (app/referencia.py).

Cada prueba compara el OpenAPI con el servidor de verdad: lo que declara token responde 401 sin
token, cada error declarado se puede provocar y cada ejemplo tiene la forma de la respuesta real.

Correr:  uv run --with httpx python -m unittest tests.test_referencia
"""

import importlib.util
import os
import re
import unittest
from unittest import mock

from app import db

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None

SUPERVISORA, OPERADORA, OPERADOR = "carla.munoz@oculta.example", "ana.rojas@oculta.example", "bruno.diaz@oculta.example"


def cuerpo_minimo(esquema: dict, doc: dict):
    """Un cuerpo que pasa la validación, para que la respuesta hable del acceso y no del formato."""
    if "$ref" in esquema:
        return cuerpo_minimo(doc["components"]["schemas"][esquema["$ref"].rsplit("/", 1)[1]], doc)
    if "anyOf" in esquema:
        return cuerpo_minimo(esquema["anyOf"][0], doc)
    tipo = esquema.get("type")
    if tipo == "object":
        return {k: cuerpo_minimo(esquema["properties"][k], doc) for k in esquema.get("required", [])}
    return {"array": [], "integer": 1, "boolean": False}.get(tipo, "x")


@unittest.skipUnless(TIENE_HTTPX, "requiere fastapi y httpx")
class LaReferencia(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api, referencia
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.referencia = referencia
        self.c = TestClient(api.app)
        self.doc = self.c.get("/openapi.json").json()
        self.clientes = self.c.get("/referencia/clientes.json").json()

    def operaciones(self, doc=None):
        for ruta, operaciones in (doc or self.doc)["paths"].items():
            for metodo, op in operaciones.items():
                yield metodo, ruta, op

    def llamar(self, metodo, ruta, op, **extra):
        url = re.sub(r"\{(\w+)\}", lambda m: "1" if m.group(1) == "version" else "x", ruta)
        if "requestBody" in op:
            extra["json"] = cuerpo_minimo(op["requestBody"]["content"]["application/json"]["schema"], self.doc)
        return self.c.request(metodo, url, **extra)

    def sembrar(self):
        self.accesos = {a["usuario"]: a["clave"] for a in self.c.post("/interno/ots/semilla").json()["accesos"]}

    def cabecera(self, usuario):
        r = self.c.post("/auth/entrar", json={"usuario": usuario, "clave": self.accesos[usuario]})
        self.assertEqual(r.status_code, 200)
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def misma_forma(self, ejemplo, real, donde):
        if isinstance(ejemplo, dict) and isinstance(real, dict):
            self.assertEqual(sorted(ejemplo), sorted(real), donde)
            for llave in ejemplo:
                self.misma_forma(ejemplo[llave], real[llave], f"{donde}.{llave}")
        elif isinstance(ejemplo, list) and isinstance(real, list) and ejemplo and real:
            self.misma_forma(ejemplo[0], real[0], f"{donde}[0]")

    # ─── El documento está ordenado ─────────────────────────────────────────

    def test_cada_ruta_tiene_su_grupo_y_un_nombre_propio(self):
        grupos = {t["name"] for t in self.doc["tags"]}
        nombres = []
        for metodo, ruta, op in self.operaciones():
            self.assertEqual(len(op["tags"]), 1, ruta)
            self.assertIn(op["tags"][0], grupos, f"{metodo} {ruta} no calza con ningún grupo de app/referencia.py")
            self.assertTrue(op["summary"], ruta)
            nombres.append(op["operationId"])
        self.assertEqual(len(nombres), len(set(nombres)))

    def test_las_paginas_no_salen_y_el_acceso_no_es_un_parametro_suelto(self):
        for pagina in self.referencia.PAGINAS:
            self.assertNotIn(pagina, self.doc["paths"])
        for _, ruta, op in self.operaciones():
            cabeceras = [p["name"].lower() for p in op.get("parameters", []) if p["in"] == "header"]
            self.assertNotIn("authorization", cabeceras, ruta)
            self.assertNotIn("x-clave-equipo", cabeceras, ruta)
        self.assertEqual(self.doc["components"]["securitySchemes"]["Token"]["scheme"], "bearer")
        self.assertEqual(self.doc["components"]["securitySchemes"]["ClaveEquipo"]["name"], "X-Clave-Equipo")

    # ─── Lo que declara, el servidor lo cumple ──────────────────────────────

    def test_todo_el_servicio_para_clientes_declara_token_y_sin_token_responde_401(self):
        con_token = [(m, r, op) for m, r, op in self.operaciones() if op.get("security") == [{"Token": []}]]
        self.assertEqual({r for _, r, _ in con_token} - {"/auth/salir", "/yo"},
                         {r for _, r, _ in self.operaciones() if r.startswith("/cliente/")})
        for metodo, ruta, op in con_token:
            for cabeceras in ({}, {"Authorization": "Bearer inventado"}, {"Authorization": "Basic eDp5"}):
                r = self.llamar(metodo, ruta, op, headers=cabeceras)
                self.assertEqual(r.status_code, 401, f"{metodo} {ruta} {cabeceras}")
                self.assertIn("login", r.json())
                self.assertEqual(r.headers["www-authenticate"], "Bearer")
            self.assertIn("401", op["responses"])

    def test_todo_el_servicio_interno_declara_la_clave_y_sin_ella_responde_401(self):
        exigida = [(m, r, op) for m, r, op in self.operaciones() if op.get("security") == [{"ClaveEquipo": []}]]
        self.assertEqual({r for _, r, _ in exigida}, {r for _, r, _ in self.operaciones() if r.startswith("/interno/")})
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            for metodo, ruta, op in exigida:
                for cabeceras in ({}, {"X-Clave-Equipo": "otra"}):
                    r = self.llamar(metodo, ruta, op, headers=cabeceras)
                    self.assertEqual((r.status_code, list(r.json())), (401, ["clave"]), f"{metodo} {ruta}")
                if metodo == "get":
                    self.assertNotEqual(self.llamar(metodo, ruta, op, headers={"X-Clave-Equipo": "secreta"}).status_code, 401, ruta)

    def test_donde_la_clave_es_opcional_una_estacion_libre_no_la_pide(self):
        opcional = {(m, r) for m, r, op in self.operaciones() if op.get("security") == [{"ClaveEquipo": []}, {}]}
        self.assertEqual(opcional, {("get", "/clave"), ("post", "/ot/{ot_id}/sesion"), ("delete", "/edge/{edge_id}/sesion")})
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            self.assertEqual(self.c.get("/clave").json(), {"requerida": True, "valida": False})
            self.assertEqual(self.c.delete("/edge/edge-libre/sesion").status_code, 204)

    def test_cada_error_declarado_se_puede_provocar(self):
        self.sembrar()
        carla, ana, bruno = self.cabecera(SUPERVISORA), self.cabecera(OPERADORA), self.cabecera(OPERADOR)
        pedido = {"pauta_id": "pauta-polin-demo"}
        ot = self.c.post("/cliente/ots", json=pedido, headers=carla).json()["ot"]
        otra = self.c.post("/cliente/ots", json=pedido, headers=carla).json()["ot"]
        for o, operador in ((ot, "operario:1"), (otra, "operario:2")):
            self.c.post(f"/cliente/ots/{o}/asignar", json={"operador": operador}, headers=carla)
        self.c.post(f"/cliente/ots/{otra}/sesion", json={"edge_id": "edge-9"}, headers=bruno)
        provocados = {
            ("POST /auth/entrar", 401): self.c.post("/auth/entrar", json={"usuario": SUPERVISORA, "clave": "mala"}),
            ("POST /cliente/ots", 403): self.c.post("/cliente/ots", json=pedido, headers=ana),
            ("POST /cliente/ots", 409): self.c.post("/cliente/ots", json={**pedido, "ot_id": ot}, headers=carla),
            ("GET /cliente/ots/{ot_id}", 404): self.c.get(f"/cliente/ots/{otra}", headers=ana),
            ("POST /cliente/ots/{ot_id}/asignar", 403): self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": "operario:2"}, headers=ana),
            ("POST /cliente/ots/{ot_id}/asignar", 404): self.c.post("/cliente/ots/no-existe/asignar", json={"operador": "operario:2"}, headers=carla),
            ("POST /cliente/ots/{ot_id}/asignar", 409): self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": "operario:2"}, headers=carla),
            ("POST /cliente/ots/{ot_id}/sesion", 403): self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": "edge-9"}, headers=carla),
            ("POST /cliente/ots/{ot_id}/sesion", 404): self.c.post(f"/cliente/ots/{otra}/sesion", json={"edge_id": "edge-9"}, headers=ana),
            ("POST /cliente/ots/{ot_id}/sesion", 409): self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": "edge-9"}, headers=ana),
            ("GET /cliente/operadores", 403): self.c.get("/cliente/operadores", headers=ana),
        }
        declarados = {(ruta, codigo) for ruta, codigos in self.referencia.ERRORES_DE.items() for codigo in codigos}
        self.assertEqual(set(provocados), declarados)
        for (ruta, codigo), r in provocados.items():
            self.assertEqual(r.status_code, codigo, f"{ruta}: {r.text}")
            llave = self.referencia._CUERPOS[codigo][1]
            self.assertEqual(list(r.json()), [llave], ruta)
            metodo, camino = ruta.split(" ")
            esquema = self.doc["paths"][camino][metodo.lower()]["responses"][str(codigo)]["content"]["application/json"]["schema"]
            self.assertTrue(esquema["$ref"].endswith(self.referencia._CUERPOS[codigo][0]))

    # ─── El recorrido que la referencia le cuenta a un cliente ──────────────

    def test_el_recorrido_del_cliente_funciona_con_login_y_cada_ejemplo_tiene_la_forma_real(self):
        self.sembrar()
        real = {}
        r = self.c.post("/auth/entrar", json={"usuario": SUPERVISORA, "clave": self.accesos[SUPERVISORA]})
        real["POST /auth/entrar"] = r.json()
        carla = {"Authorization": f"Bearer {r.json()['token']}"}
        real["GET /yo"] = self.c.get("/yo", headers=carla).json()
        real["GET /cliente/pautas"] = self.c.get("/cliente/pautas", headers=carla).json()
        r = self.c.post("/cliente/ots", json={"pauta_id": "pauta-polin-demo"}, headers=carla)
        self.assertEqual(r.status_code, 201)
        real["POST /cliente/ots"], ot = r.json(), r.json()["ot"]
        real["GET /cliente/operadores"] = self.c.get("/cliente/operadores", headers=carla).json()
        real["GET /cliente/personas"] = self.c.get("/cliente/personas", headers=carla).json()
        real["POST /cliente/ots/{ot_id}/asignar"] = self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": "operario:1"}, headers=carla).json()

        ana = self.cabecera(OPERADORA)
        real["GET /cliente/ots"] = self.c.get("/cliente/ots", headers=ana).json()
        self.assertIn(ot, [o["ot"] for o in real["GET /cliente/ots"]])
        r = self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": "edge-9"}, headers=ana)
        self.assertEqual((r.status_code, r.json()["operario"]), (200, "operario:1"))
        real["POST /cliente/ots/{ot_id}/sesion"] = r.json()
        real["GET /cliente/ots/{ot_id}"] = self.c.get(f"/cliente/ots/{ot}", headers=ana).json()
        self.assertEqual(real["GET /cliente/ots/{ot_id}"]["estado_general"], "en_ejecucion")

        # La ejecución va sin token: es lo que la referencia declara, y la brecha del ADR-0012.
        real["GET /ot/{ot_id}"] = self.c.get(f"/ot/{ot}").json()
        r = self.c.post(f"/ot/{ot}/declarar", json={"actor": "operario:1", "texto": "listo", "paso_id": real["GET /ot/{ot_id}"]["paso_actual"]})
        self.assertEqual(r.status_code, 200)
        real["POST /ot/{ot_id}/declarar"] = r.json()
        real["GET /ot/{ot_id}/eventos"] = self.c.get(f"/ot/{ot}/eventos").json()

        self.assertEqual(self.c.post("/auth/salir", headers=ana).status_code, 204)
        self.assertEqual(self.c.get("/cliente/ots", headers=ana).status_code, 401)

        self.assertEqual(set(real), set(self.referencia.EJEMPLOS))
        for ruta, ejemplo in self.referencia.EJEMPLOS.items():
            self.misma_forma(ejemplo["respuesta"], real[ruta], ruta)
            metodo, camino = ruta.split(" ")
            op = self.clientes["paths"][camino][metodo.lower()]
            ok = next(r for codigo, r in op["responses"].items() if codigo.startswith("2"))
            self.assertEqual(ok["content"]["application/json"]["example"], ejemplo["respuesta"])

    def test_el_documento_para_clientes_trae_solo_lo_suyo(self):
        for _, ruta, op in self.operaciones(self.clientes):
            self.assertIn(op["tags"][0], self.referencia.PARA_CLIENTES, ruta)
            self.assertFalse(ruta.startswith("/interno"), ruta)
        self.assertEqual(list(self.clientes["components"]["securitySchemes"]), ["Token"])
        self.assertEqual({r for r in self.clientes["paths"] if r.startswith("/cliente/")},
                         {r for r in self.doc["paths"] if r.startswith("/cliente/")})
        usados = set(re.findall(r"#/components/schemas/(\w+)", self.c.get("/referencia/clientes.json").text))
        self.assertEqual(usados, set(self.clientes["components"]["schemas"]))
        self.assertNotIn("ProtocoloNuevo", usados)

    def test_la_pagina_carga_los_dos_documentos_sin_telemetria(self):
        r = self.c.get("/referencia")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers["content-type"])
        for esperado in ("/referencia/clientes.json", "/openapi.json", self.referencia.SCALAR_JS):
            self.assertIn(esperado, r.text)
        self.assertRegex(self.referencia.SCALAR_JS, r"@\d+\.\d+\.\d+$")
        self.assertRegex(r.text, r'"telemetry":\s*false')
        self.assertIn("/referencia", self.c.get("/agente").text)


if __name__ == "__main__":
    unittest.main()
