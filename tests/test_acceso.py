"""Login y clientes: cada empresa ve lo suyo (ADR-0012). Casos de uso.

Correr:  uv run --with httpx python -m unittest tests.test_acceso
"""

import importlib.util
import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest import mock

from app import acceso, catalogo, db, semilla
from app.acceso import NoAutenticado, SinPermiso

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None


class Base(unittest.TestCase):
    def setUp(self):
        self.cx = db.conectar(":memory:")
        self.r = semilla.cargar(self.cx, datetime(2026, 11, 21, 18, 0, tzinfo=UTC))
        self.claves = {a["usuario"]: a["clave"] for a in self.r["accesos"]}
        acceso.crear_cliente(self.cx, "otra", "Otra Minera")
        _, self.clave_otra = acceso.crear_persona(self.cx, "otra", "supervisor:otra", "Pedro", "pedro@otra.example", "supervisor")

    def tearDown(self):
        self.cx.close()

    def entra(self, usuario):
        return acceso.quien(self.cx, acceso.entrar(self.cx, usuario, self.claves.get(usuario, self.clave_otra))["token"])


class ElLogin(Base):
    def test_entra_con_su_clave_y_el_token_dice_quien_es(self):
        r = acceso.entrar(self.cx, "carla.munoz@oculta.example", self.claves["carla.munoz@oculta.example"])
        yo = acceso.quien(self.cx, r["token"])
        self.assertEqual((yo["id"], yo["rol"], yo["cliente"]["nombre"]), ("supervisor:oculta", "supervisor", "Oculta"))

    def test_una_clave_mala_o_un_usuario_que_no_existe_dicen_lo_mismo(self):
        for usuario, clave in (("carla.munoz@oculta.example", "otra"), ("nadie@oculta.example", "x")):
            with self.assertRaises(NoAutenticado) as e:
                acceso.entrar(self.cx, usuario, clave)
            self.assertEqual(str(e.exception), "usuario o clave incorrectos")

    def test_el_usuario_no_distingue_mayusculas(self):
        acceso.entrar(self.cx, "Carla.Munoz@Oculta.example", self.claves["carla.munoz@oculta.example"])

    def test_ni_la_clave_ni_el_token_se_guardan_tal_cual(self):
        clave = self.claves["ana.rojas@oculta.example"]
        token = acceso.entrar(self.cx, "ana.rojas@oculta.example", clave)["token"]
        volcado = "\n".join(self.cx.iterdump())
        self.assertNotIn(clave, volcado)
        self.assertNotIn(token, volcado)

    def test_sin_token_con_uno_inventado_o_vencido_no_entra(self):
        for token in (None, "", "inventado"):
            with self.assertRaises(NoAutenticado):
                acceso.quien(self.cx, token)
        token = acceso.entrar(self.cx, "ana.rojas@oculta.example", self.claves["ana.rojas@oculta.example"])["token"]
        with mock.patch.object(acceso, "_ahora", return_value=datetime.now(UTC) + acceso.DURACION_SESION + timedelta(minutes=1)):
            with self.assertRaises(NoAutenticado):
                acceso.quien(self.cx, token)

    def test_salir_y_cambiar_la_clave_cierran_la_sesion(self):
        u = "ana.rojas@oculta.example"
        t1 = acceso.entrar(self.cx, u, self.claves[u])["token"]
        acceso.salir(self.cx, t1)
        with self.assertRaises(NoAutenticado):
            acceso.quien(self.cx, t1)
        t2 = acceso.entrar(self.cx, u, self.claves[u])["token"]
        nueva = acceso.nueva_clave(self.cx, "operario:1")
        with self.assertRaises(NoAutenticado):
            acceso.quien(self.cx, t2)
        with self.assertRaises(NoAutenticado):
            acceso.entrar(self.cx, u, self.claves[u])
        acceso.entrar(self.cx, u, nueva)

    def test_la_semilla_da_las_claves_una_sola_vez(self):
        self.assertEqual({a["rol"] for a in self.r["accesos"]}, {"supervisor", "operador"})
        self.assertEqual(semilla.cargar(self.cx)["accesos"], [])


class CadaEmpresaVeLoSuyo(Base):
    def test_el_supervisor_ve_todas_las_de_su_empresa_y_ninguna_de_otra(self):
        carla, pedro = self.entra("carla.munoz@oculta.example"), self.entra("pedro@otra.example")
        self.assertEqual(len(acceso.ots_de(self.cx, carla)), 21)
        self.assertEqual(acceso.ots_de(self.cx, pedro), [])
        with self.assertRaises(db.NoExiste):
            acceso.ot_de(self.cx, pedro, "ot-1001")

    def test_el_operador_ve_solo_las_que_tiene_asignadas(self):
        ana = self.entra("ana.rojas@oculta.example")
        mias = acceso.ots_de(self.cx, ana)
        self.assertTrue(mias)
        self.assertEqual({o["operador"] for o in mias}, {"operario:1"})
        ajena = next(o["ot"] for o in acceso.ots_de(self.cx, self.entra("carla.munoz@oculta.example")) if o["operador"] == "operario:2")
        with self.assertRaises(db.NoExiste):
            acceso.ot_de(self.cx, ana, ajena)

    def test_solo_un_supervisor_pide_y_solo_pautas_habilitadas(self):
        with self.assertRaises(SinPermiso):
            acceso.pedir_ot(self.cx, self.entra("ana.rojas@oculta.example"), "pauta-polin-demo")
        with self.assertRaises(SinPermiso):
            acceso.pedir_ot(self.cx, self.entra("pedro@otra.example"), "pauta-polin-demo")
        acceso.habilitar(self.cx, "otra", "pauta-polin-demo")
        r = acceso.pedir_ot(self.cx, self.entra("pedro@otra.example"), "pauta-polin-demo")
        self.assertEqual(r["cliente"], "otra")
        self.assertEqual([o["ot"] for o in acceso.ots_de(self.cx, self.entra("pedro@otra.example"))], [r["ot"]])

    def test_se_asigna_solo_a_un_operador_de_la_misma_empresa(self):
        carla, pedro = self.entra("carla.munoz@oculta.example"), self.entra("pedro@otra.example")
        acceso.operador_de_la_empresa(self.cx, carla, "operario:1")
        with self.assertRaises(SinPermiso):
            acceso.operador_de_la_empresa(self.cx, pedro, "operario:1")
        acceso.crear_persona(self.cx, "otra", "operario:otra-1", "Luis", "luis@otra.example", "operador")
        acceso.habilitar(self.cx, "otra", "pauta-brazo-01")
        ot = acceso.pedir_ot(self.cx, pedro, "pauta-brazo-01")["ot"]
        catalogo.asignacion(self.cx, ot, "operario:otra-1", "supervisor:otra")

    def test_una_persona_que_no_es_supervisor_no_asigna_aunque_su_id_lo_parezca(self):
        acceso.crear_persona(self.cx, "oculta", "supervisor:falso", "Falso", "falso@oculta.example", "operador")
        ot = acceso.pedir_ot(self.cx, self.entra("carla.munoz@oculta.example"), "pauta-polin-demo")["ot"]
        for actor in ("operario:1", "supervisor:falso"):
            with self.assertRaisesRegex(catalogo.ReglaDeNegocio, "solo un supervisor"):
                catalogo.asignacion(self.cx, ot, "operario:2", actor)
        catalogo.asignacion(self.cx, ot, "operario:2", "supervisor:oculta")

    def test_no_hay_roles_ni_usuarios_repetidos(self):
        with self.assertRaises(catalogo.ReglaDeNegocio):
            acceso.crear_persona(self.cx, "otra", "x", "X", "x@otra.example", "gerente")
        with self.assertRaises(catalogo.ReglaDeNegocio):
            acceso.crear_persona(self.cx, "otra", "y", "Y", "CARLA.MUNOZ@oculta.example", "operador")


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class PorHTTP(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.accesos = {a["usuario"]: a["clave"] for a in self.c.post("/interno/ots/semilla").json()["accesos"]}

    def cabecera(self, usuario):
        r = self.c.post("/auth/entrar", json={"usuario": usuario, "clave": self.accesos[usuario]})
        self.assertEqual(r.status_code, 200)
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def test_de_entrar_a_pedir_asignar_y_ver_una_ot(self):
        carla = self.cabecera("carla.munoz@oculta.example")
        self.assertEqual(self.c.get("/yo", headers=carla).json()["cliente"]["nombre"], "Oculta")
        self.assertEqual(len(self.c.get("/cliente/pautas", headers=carla).json()), 10)
        r = self.c.post("/cliente/ots", json={"pauta_id": "pauta-polin-demo"}, headers=carla)
        self.assertEqual((r.status_code, r.json()["cliente"]), (201, "oculta"))
        ot = r.json()["ot"]
        self.assertEqual([o["id"] for o in self.c.get("/cliente/operadores", headers=carla).json()], ["operario:1", "operario:2"])
        r = self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": "operario:2"}, headers=carla)
        self.assertEqual((r.status_code, r.json()["operador"]), (200, "operario:2"))
        bruno = self.cabecera("bruno.diaz@oculta.example")
        self.assertIn(ot, [o["ot"] for o in self.c.get("/cliente/ots", headers=bruno).json()])
        detalle = self.c.get(f"/cliente/ots/{ot}", headers=bruno).json()
        self.assertEqual((detalle["estado_general"], detalle["calificacion"]["nivel"]), ("asignada", "ok"))
        self.assertEqual(self.c.get(f"/cliente/ots/{ot}", headers=self.cabecera("ana.rojas@oculta.example")).status_code, 404)

    def test_sin_token_401_y_sin_rol_403(self):
        for metodo, ruta in (("get", "/yo"), ("get", "/cliente/pautas"), ("get", "/cliente/ots"), ("post", "/cliente/ots")):
            r = getattr(self.c, metodo)(ruta, json={"pauta_id": "pauta-polin-demo"}) if metodo == "post" else getattr(self.c, metodo)(ruta)
            self.assertEqual(r.status_code, 401, ruta)
        self.assertEqual(self.c.get("/yo", headers={"Authorization": "Bearer inventado"}).status_code, 401)
        self.assertEqual(self.c.post("/auth/entrar", json={"usuario": "carla.munoz@oculta.example", "clave": "mala"}).status_code, 401)
        ana = self.cabecera("ana.rojas@oculta.example")
        self.assertEqual(self.c.post("/cliente/ots", json={"pauta_id": "pauta-polin-demo"}, headers=ana).status_code, 403)
        self.assertEqual(self.c.get("/cliente/operadores", headers=ana).status_code, 403)

    def test_la_pagina_de_analisis_lee_rutas_que_existen(self):
        import re

        pagina = self.c.get("/analisis")
        self.assertEqual(pagina.status_code, 200)
        carla = self.cabecera("carla.munoz@oculta.example")
        rutas = set(re.findall(r'"(/(?:yo|cliente)[^"?]*)', pagina.text))
        self.assertEqual(rutas, {"/yo", "/cliente/metricas", "/cliente/metricas/pautas", "/cliente/mejoras"})
        for ruta in rutas:
            self.assertEqual(self.c.get(ruta, headers=carla).status_code, 200, ruta)

    def test_la_lista_trae_la_calificacion_de_cada_ot(self):
        carla = self.cabecera("carla.munoz@oculta.example")
        lista = self.c.get("/cliente/ots", headers=carla).json()
        self.assertEqual(len(lista), 21)
        for o in lista:
            self.assertEqual(o["calificacion"], self.c.get(f"/cliente/ots/{o['ot']}", headers=carla).json()["calificacion"], o["ot"])
        self.assertGreater(len({o["calificacion"]["nivel"] for o in lista}), 1)
        ana = self.c.get("/cliente/ots", headers=self.cabecera("ana.rojas@oculta.example")).json()
        self.assertTrue(ana)
        self.assertTrue(all("nivel" in o["calificacion"] for o in ana))

    def test_un_operador_lee_los_nombres_de_su_empresa_y_nada_mas(self):
        ana = self.cabecera("ana.rojas@oculta.example")
        personas = self.c.get("/cliente/personas", headers=ana).json()
        self.assertEqual({p["id"]: (p["nombre"], p["rol"]) for p in personas},
                         {"supervisor:oculta": ("Carla Muñoz", "supervisor"), "operario:1": ("Ana Rojas", "operador"),
                          "operario:2": ("Bruno Díaz", "operador")})
        self.assertEqual({k for p in personas for k in p}, {"id", "nombre", "rol"})
        self.assertEqual(self.c.get("/cliente/personas", headers=self.cabecera("carla.munoz@oculta.example")).json(), personas)
        self.assertEqual(self.c.get("/cliente/personas").status_code, 401)

    def test_los_nombres_de_una_empresa_no_salen_para_otra(self):
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": ""}):
            self.assertEqual(self.c.post("/interno/clientes", json={"id": "otra", "nombre": "Otra Minera"}).status_code, 201)
            r = self.c.post("/interno/clientes/otra/personas", json={"id": "operario:otra-1", "nombre": "Luis", "usuario": "luis@otra.example", "rol": "operador"})
        token = self.c.post("/auth/entrar", json={"usuario": "luis@otra.example", "clave": r.json()["clave"]}).json()["token"]
        personas = self.c.get("/cliente/personas", headers={"Authorization": f"Bearer {token}"}).json()
        self.assertEqual(personas, [{"id": "operario:otra-1", "nombre": "Luis", "rol": "operador"}])

    def otra_empresa_con_una_ot(self):
        self.assertEqual(self.c.post("/interno/clientes", json={"id": "otra", "nombre": "Otra Minera"}).status_code, 201)
        r = self.c.post("/interno/clientes/otra/personas", json={"id": "supervisor:otra", "nombre": "Pedro", "usuario": "pedro@otra.example", "rol": "supervisor"})
        self.assertEqual(self.c.put("/interno/clientes/otra/pautas/pauta-brazo-01").status_code, 200)
        token = self.c.post("/auth/entrar", json={"usuario": "pedro@otra.example", "clave": r.json()["clave"]}).json()["token"]
        return self.c.post("/cliente/ots", json={"pauta_id": "pauta-brazo-01"}, headers={"Authorization": f"Bearer {token}"}).json()["ot"]

    def test_el_operador_une_su_ot_a_una_estacion_libre_con_su_token(self):
        ana = self.cabecera("ana.rojas@oculta.example")
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            r = self.c.post("/cliente/ots/ot-1004/sesion", json={"edge_id": "edge-1"}, headers=ana)
            self.assertEqual((r.status_code, r.json()["ot_id"], r.json()["operario"]), (200, "ot-1004", "operario:1"))
            self.assertEqual(self.c.post("/cliente/ots/ot-1004/sesion", json={}, headers=ana).status_code, 200)
        self.assertEqual(self.c.get("/edge/edge-1/sesion").json()["ot_id"], "ot-1004")

    def test_una_estacion_ocupada_se_toma_solo_si_el_operador_lo_pide(self):
        self.assertEqual(self.c.post("/pauta/demo").status_code, 200)
        self.assertEqual(self.c.post("/ot/ot-prueba/abrir").status_code, 200)
        for ocupante in ("ot-1002", "ot-prueba"):  # la de un compañero y una del equipo, sin empresa
            self.assertEqual(self.c.post(f"/ot/{ocupante}/sesion", json={"edge_id": "edge-1", "operario": "operario:A"}).status_code, 200)
            ana = self.cabecera("ana.rojas@oculta.example")
            with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
                r = self.c.post("/cliente/ots/ot-1004/sesion", json={"edge_id": "edge-1"}, headers=ana)
                self.assertEqual(r.status_code, 409, ocupante)
                self.assertIn(ocupante, r.json()["regla"])
                self.assertIn("tomar", r.json()["regla"])
                self.assertEqual(self.c.get("/edge/edge-1/sesion").json()["ot_id"], ocupante)
                r = self.c.post("/cliente/ots/ot-1004/sesion", json={"edge_id": "edge-1", "tomar": True}, headers=ana)
                self.assertEqual((r.status_code, r.json()["ot_id"], r.json()["operario"]), (200, "ot-1004", "operario:1"))
                self.assertEqual(self.c.post("/ot/ot-1007/sesion", json={"edge_id": "edge-1", "operario": "operario:1"}).status_code, 401)

    def test_una_estacion_con_una_ot_completa_no_hace_falta_tomarla(self):
        self.assertEqual(self.c.post("/ot/ot-1005/sesion", json={"edge_id": "edge-1", "operario": "operario:2"}).status_code, 200)
        r = self.c.post("/cliente/ots/ot-1004/sesion", json={"edge_id": "edge-1"}, headers=self.cabecera("ana.rojas@oculta.example"))
        self.assertEqual((r.status_code, r.json()["ot_id"]), (200, "ot-1004"))

    def test_la_estacion_que_ejecuta_la_ot_de_otra_empresa_no_se_toma(self):
        ajena = self.otra_empresa_con_una_ot()
        self.assertEqual(self.c.post(f"/ot/{ajena}/sesion", json={"edge_id": "edge-1", "operario": "operario:A"}).status_code, 200)
        r = self.c.post("/cliente/ots/ot-1004/sesion", json={"edge_id": "edge-1", "tomar": True}, headers=self.cabecera("ana.rojas@oculta.example"))
        self.assertEqual(r.status_code, 403)
        self.assertNotIn(ajena, r.text)
        self.assertEqual(self.c.get("/edge/edge-1/sesion").json()["ot_id"], ajena)

    def test_solo_el_operador_de_la_ot_y_solo_si_esta_abierta(self):
        ana, carla = self.cabecera("ana.rojas@oculta.example"), self.cabecera("carla.munoz@oculta.example")
        cuerpo = {"edge_id": "edge-1", "tomar": True}
        self.assertEqual(self.c.post("/cliente/ots/ot-1004/sesion", json=cuerpo).status_code, 401)
        self.assertEqual(self.c.post("/cliente/ots/ot-1004/sesion", json=cuerpo, headers=carla).status_code, 403)
        self.assertEqual(self.c.post("/cliente/ots/ot-1002/sesion", json=cuerpo, headers=ana).status_code, 404)  # es de Bruno
        self.assertEqual(self.c.post("/cliente/ots/ot-1013/sesion", json=cuerpo, headers=ana).status_code, 404)  # sin asignar
        r = self.c.post("/cliente/ots/ot-1001/sesion", json=cuerpo, headers=ana)
        self.assertEqual((r.status_code, r.json()["regla"]), (409, "la OT ot-1001 ya está completa"))
        self.assertEqual(self.c.get("/sesiones").json(), [])

    def test_la_ficha_trae_lo_que_hace_falta_para_ejecutar_una_ot_que_ya_existe(self):
        ana = self.cabecera("ana.rojas@oculta.example")
        f = self.c.get("/cliente/ots/ot-1017/ficha", headers=ana).json()
        self.assertEqual((f["cliente"]["nombre"], f["operador_nombre"], f["pedida_por_nombre"], f["estado_general"], f["paso_actual"]),
                         ("Oculta", "Ana Rojas", "Carla Muñoz", "asignada", "e1"))
        self.assertEqual((f["pauta"], f["version"], f["nombre"]), ("pauta-polin-estacion", 4, "Cambio de polín en la cinta · estación del demo"))
        self.assertEqual([p["id"] for p in f["protocolos"]], ["prot-aislamiento-01", "prot-correa-01"])
        self.assertEqual([(p["id"], p["tipo_evidencia"]) for p in f["pasos"]],
                         [("e1", "sensor"), ("e2", "sensor"), ("e3", "sensor"), ("e4", "camara"), ("e5", "camara"), ("e6", "sensor")])
        self.assertEqual((f["pasos"][0]["sensor"], f["pasos"][0]["instruccion"][:16]), ({"id": "energia", "espera": "cortada"}, "Aprieta el botón"))
        self.assertEqual(self.c.get("/ot/ot-1017/ficha").json(), f)  # sin clave de equipo el servidor está abierto, como en local
        # la estación la ejecuta a nombre de su operadora y la ficha lo refleja
        self.assertEqual(self.c.post("/ot/ot-1017/sesion", json={"edge_id": "edge-1", "operario": f["operador"]}).status_code, 200)
        self.assertEqual(self.c.get("/cliente/ots/ot-1017/ficha", headers=ana).json()["estado_general"], "en_ejecucion")

    def test_la_ficha_no_sale_para_quien_no_es_y_sin_la_clave_no_dice_de_que_empresa_es(self):
        bruno = self.cabecera("bruno.diaz@oculta.example")
        self.assertEqual(self.c.get("/cliente/ots/ot-1017/ficha").status_code, 401)
        self.assertEqual(self.c.get("/cliente/ots/ot-1017/ficha", headers=bruno).status_code, 404)  # es de Ana
        self.assertEqual(self.c.get("/ot/no-existe/ficha").status_code, 404)
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            f = self.c.get("/ot/ot-1017/ficha").json()
            self.assertEqual((f["cliente"], f["operador_nombre"], f["pedida_por_nombre"]), (None, None, None))
            self.assertEqual((f["operador"], len(f["pasos"])), ("operario:1", 6))
            self.assertEqual(self.c.get("/ot/ot-1017/ficha", headers={"X-Clave-Equipo": "secreta"}).json()["cliente"]["id"], "oculta")

    def test_el_equipo_deja_la_ot_del_demo_pedida_por_su_supervisor_y_asignada_a_su_operador(self):
        f = self.c.get("/ot/ot-1019/ficha").json()  # la que deja la semilla
        self.assertEqual((f["pauta"], f["operador_nombre"], f["pedida_por_nombre"], f["estado_general"]),
                         ("pauta-polin-estacion", "Ana Rojas", "Carla Muñoz", "asignada"))
        cuerpo = {"pauta_id": "pauta-polin-estacion", "supervisor": "supervisor:oculta", "operador": "operario:1"}
        r = self.c.post("/interno/ots", json=cuerpo)  # la que abre «Nueva demo»
        self.assertEqual((r.status_code, r.json()["operador"], r.json()["estado_general"]), (201, "operario:1", "asignada"))
        f = self.c.get(f"/ot/{r.json()['ot']}/ficha").json()
        self.assertEqual((f["cliente"]["id"], f["pedida_por"], f["operador_nombre"]), ("oculta", "supervisor:oculta", "Ana Rojas"))
        self.assertIn(r.json()["ot"], [o["ot"] for o in self.c.get("/cliente/ots", headers=self.cabecera("ana.rojas@oculta.example")).json()])
        antes = len(self.c.get("/ots").json())
        for cambio, codigo in (({"supervisor": "operario:1"}, 403), ({"operador": "supervisor:oculta"}, 403), ({"supervisor": "nadie"}, 404), ({"pauta_id": "nada"}, 403)):
            self.assertEqual(self.c.post("/interno/ots", json={**cuerpo, **cambio}).status_code, codigo, cambio)
        self.assertEqual(len(self.c.get("/ots").json()), antes)
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            self.assertEqual(self.c.post("/interno/ots", json=cuerpo).status_code, 401)

    def test_salir_invalida_el_token(self):
        ana = self.cabecera("ana.rojas@oculta.example")
        self.assertEqual(self.c.post("/auth/salir", headers=ana).status_code, 204)
        self.assertEqual(self.c.get("/yo", headers=ana).status_code, 401)

    def test_el_equipo_crea_clientes_y_personas_con_su_clave(self):
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            self.assertEqual(self.c.post("/interno/clientes", json={"id": "nueva", "nombre": "Nueva"}).status_code, 401)
            k = {"X-Clave-Equipo": "secreta"}
            self.assertEqual(self.c.post("/interno/clientes", json={"id": "nueva", "nombre": "Nueva"}, headers=k).status_code, 201)
            r = self.c.post("/interno/clientes/nueva/personas", json={"id": "sup:nueva", "nombre": "Eva", "usuario": "eva@nueva.example", "rol": "supervisor"}, headers=k)
            self.assertEqual(r.status_code, 201)
            self.assertEqual(self.c.put("/interno/clientes/nueva/pautas/pauta-brazo-01", headers=k).status_code, 200)
            ficha = self.c.get("/interno/clientes/nueva", headers=k).json()
            self.assertEqual(([p["id"] for p in ficha["personas"]], [p["id"] for p in ficha["pautas"]]), (["sup:nueva"], ["pauta-brazo-01"]))
            nueva = self.c.post("/interno/personas/sup:nueva/clave", headers=k).json()["clave"]
        self.assertEqual(self.c.post("/auth/entrar", json={"usuario": "eva@nueva.example", "clave": r.json()["clave"]}).status_code, 401)
        token = self.c.post("/auth/entrar", json={"usuario": "eva@nueva.example", "clave": nueva}).json()["token"]
        self.assertEqual(self.c.get("/cliente/ots", headers={"Authorization": f"Bearer {token}"}).json(), [])


if __name__ == "__main__":
    unittest.main()
