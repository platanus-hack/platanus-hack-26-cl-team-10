"""Protocolos, sus pautas y las OT que pide un cliente. Casos de uso.

Correr:  uv run --with httpx python -m unittest tests.test_protocolos
Un protocolo es el documento del cliente. De él salen una o más pautas, y una pauta puede
salir de más de un protocolo. El equipo los carga por el servicio interno; el cliente solo
pide OT de las pautas que quedaron listas (ADR-0011).
"""

import importlib.util
import json
import os
import unittest
from unittest import mock

from app import catalogo, db, protocolos
from app.catalogo import ReglaDeNegocio
from app.protocolos import DATOS, PAUTA_DEMO, SEMILLA

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None
EQUIPO = "equipo:factum"
CORREA = "pauta-correa-ct-01"


def pauta_demo(version=1, **cambios):
    d = json.loads(PAUTA_DEMO.read_text(encoding="utf-8"))
    d["version"] = version
    d.update(cambios)
    return d


def protocolo(protocolo_id="prot-a", **cambios):
    return {"id": protocolo_id, "nombre": "Cambio de rodillo", "industria": "minería", "origen": "PDF del cliente",
            "texto": "1. Cortar la energía...", **cambios}


class Base(unittest.TestCase):
    def setUp(self):
        self.cx = db.conectar(":memory:")
        catalogo.preparar(self.cx)

    def tearDown(self):
        self.cx.close()


class ElProtocoloEsUnRecurso(Base):
    def test_se_carga_y_se_lee_con_su_texto(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        p = catalogo.leer_protocolo(self.cx, "prot-a")
        self.assertEqual((p["nombre"], p["industria"], p["creado_por"]), ("Cambio de rodillo", "minería", EQUIPO))
        self.assertEqual(p["texto"], "1. Cortar la energía...")
        self.assertEqual(p["pautas"], [])

    def test_la_lista_no_trae_el_texto(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        self.assertNotIn("texto", catalogo.listar_protocolos(self.cx)[0])

    def test_necesita_id_y_nombre_y_lo_carga_una_persona(self):
        for malo, actor in [(protocolo(id=" "), EQUIPO), (protocolo(nombre=""), EQUIPO), (protocolo(), "sistema"), (protocolo(), "")]:
            with self.assertRaises(ReglaDeNegocio):
                catalogo.crear_protocolo(self.cx, malo, actor)

    def test_no_se_carga_dos_veces_el_mismo_id(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        with self.assertRaises(ReglaDeNegocio):
            catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)

    def test_se_corrigen_sus_datos_pero_no_su_id(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        p = catalogo.cambiar_protocolo(self.cx, "prot-a", {"nombre": "Cambio de rodillo CT-01", "texto": "v2"})
        self.assertEqual((p["nombre"], p["texto"], p["industria"]), ("Cambio de rodillo CT-01", "v2", "minería"))
        for malo in ({"id": "otro"}, {"nombre": " "}):
            with self.assertRaises(ReglaDeNegocio):
                catalogo.cambiar_protocolo(self.cx, "prot-a", malo)

    def test_uno_que_no_existe_es_404(self):
        for accion in (lambda: catalogo.leer_protocolo(self.cx, "nada"), lambda: catalogo.borrar_protocolo(self.cx, "nada"),
                       lambda: catalogo.cambiar_protocolo(self.cx, "nada", {"nombre": "x"})):
            with self.assertRaises(db.NoExiste):
                accion()

    def test_se_borra_solo_si_ninguna_pauta_sale_de_el(self):
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        with self.assertRaises(ReglaDeNegocio):
            catalogo.borrar_protocolo(self.cx, "prot-a")
        catalogo.quitar_atribucion(self.cx, CORREA, "prot-a")
        catalogo.borrar_protocolo(self.cx, "prot-a")
        self.assertEqual(catalogo.listar_protocolos(self.cx), [])


class LasPautasSalenDeProtocolos(Base):
    def setUp(self):
        super().setUp()
        catalogo.crear_protocolo(self.cx, protocolo("prot-a"), EQUIPO)
        catalogo.crear_protocolo(self.cx, protocolo("prot-b", nombre="Aislamiento de energías"), EQUIPO)

    def test_una_pauta_creada_desde_un_protocolo_nace_atribuida_y_sin_aprobar(self):
        r = catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        self.assertFalse(r["aprobada"])
        self.assertEqual([p["id"] for p in r["protocolos"]], ["prot-a"])
        self.assertEqual([p["id"] for p in catalogo.leer_protocolo(self.cx, "prot-a")["pautas"]], [CORREA])

    def test_una_pauta_puede_salir_de_mas_de_un_protocolo(self):
        r = catalogo.crear_pauta_de(self.cx, ["prot-a", "prot-b", "prot-a"], pauta_demo(), EQUIPO)
        self.assertEqual([p["id"] for p in r["protocolos"]], ["prot-a", "prot-b"])

    def test_un_protocolo_da_mas_de_una_pauta(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(id="pauta-otra", nombre="Otra tarea"), EQUIPO)
        self.assertEqual([p["id"] for p in catalogo.pautas_de(self.cx, "prot-a")], [CORREA, "pauta-otra"])

    def test_sin_protocolo_o_con_uno_que_no_existe_la_pauta_no_se_crea(self):
        with self.assertRaises(ReglaDeNegocio):
            catalogo.crear_pauta_de(self.cx, [], pauta_demo(), EQUIPO)
        with self.assertRaises(db.NoExiste):
            catalogo.crear_pauta_de(self.cx, ["prot-a", "nada"], pauta_demo(), EQUIPO)
        self.assertEqual(catalogo.listar_pautas(self.cx), [])

    def test_la_version_siguiente_hereda_la_atribucion(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.crear_pauta(self.cx, pauta_demo(version=2))
        self.assertEqual([p["id"] for p in catalogo.protocolos_de(self.cx, CORREA)], ["prot-a"])

    def test_una_pauta_que_ya_existe_se_atribuye_y_repetirlo_no_cambia_nada(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        catalogo.atribuir(self.cx, CORREA, "prot-b", EQUIPO)
        r = catalogo.atribuir(self.cx, CORREA, "prot-b", EQUIPO)
        self.assertEqual([p["id"] for p in r["protocolos"]], ["prot-b"])

    def test_un_protocolo_se_puede_cargar_ya_atribuido_a_pautas(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        p = catalogo.crear_protocolo(self.cx, protocolo("prot-c", pautas=[CORREA]), EQUIPO)
        self.assertEqual([x["id"] for x in p["pautas"]], [CORREA])
        with self.assertRaises(db.NoExiste):
            catalogo.crear_protocolo(self.cx, protocolo("prot-d", pautas=["pauta-fantasma"]), EQUIPO)
        with self.assertRaises(db.NoExiste):
            catalogo.leer_protocolo(self.cx, "prot-d")

    def test_una_pauta_con_ot_no_queda_sin_protocolo(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a", "prot-b"], pauta_demo(), EQUIPO)
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        catalogo.quitar_atribucion(self.cx, CORREA, "prot-b")
        with self.assertRaises(ReglaDeNegocio):
            catalogo.quitar_atribucion(self.cx, CORREA, "prot-a")
        with self.assertRaises(db.NoExiste):
            catalogo.quitar_atribucion(self.cx, CORREA, "prot-b")


class ElClientePideOt(Base):
    def setUp(self):
        super().setUp()
        catalogo.crear_protocolo(self.cx, protocolo(), EQUIPO)

    def test_solo_ve_pautas_aprobadas_y_atribuidas(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.crear_pauta(self.cx, pauta_demo(id="pauta-suelta"))
        catalogo.aprobar_pauta(self.cx, "pauta-suelta", 1, "supervisor:X")
        self.assertEqual(catalogo.pautas_disponibles(self.cx), [])
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        lista = catalogo.pautas_disponibles(self.cx)
        self.assertEqual([(p["id"], p["version"], [x["id"] for x in p["protocolos"]]) for p in lista], [(CORREA, 1, ["prot-a"])])

    def test_la_ot_sale_de_la_ultima_version_aprobada_y_dice_de_que_protocolos(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        catalogo.crear_pauta(self.cx, pauta_demo(version=2))  # nadie la aprobó todavía
        r = catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        self.assertEqual((r["ot"], r["version"], [p["id"] for p in r["protocolos"]]), ("ot-0001", 1, ["prot-a"]))
        self.assertEqual(catalogo.pautas_disponibles(self.cx)[0]["version"], 1)
        self.assertEqual(db.eventos(self.cx, "ot-0001")[0].actor, "cliente:planta")

    def test_el_servicio_le_pone_el_id_y_no_repite(self):
        catalogo.crear_pauta_de(self.cx, ["prot-a"], pauta_demo(), EQUIPO)
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        catalogo.abrir_ot(self.cx, "ot-0002", CORREA, "supervisor:X")
        ids = [catalogo.generar_ot(self.cx, CORREA, "cliente:planta")["ot"] for _ in range(2)]
        self.assertEqual(ids, ["ot-0003", "ot-0004"])
        self.assertEqual(catalogo.generar_ot(self.cx, CORREA, "cliente:planta", "ot-mia")["ot"], "ot-mia")
        with self.assertRaises(ReglaDeNegocio):
            catalogo.generar_ot(self.cx, CORREA, "cliente:planta", "ot-mia")

    def test_lo_que_no_se_puede_pedir(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        with self.assertRaises(ReglaDeNegocio):  # sin aprobar
            catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        catalogo.aprobar_pauta(self.cx, CORREA, 1, "supervisor:X")
        with self.assertRaises(ReglaDeNegocio):  # aprobada, pero no sale de ningún protocolo
            catalogo.generar_ot(self.cx, CORREA, "cliente:planta")
        catalogo.atribuir(self.cx, CORREA, "prot-a", EQUIPO)
        with self.assertRaises(ReglaDeNegocio):  # sin solicitante
            catalogo.generar_ot(self.cx, CORREA, " ")
        with self.assertRaises(db.NoExiste):
            catalogo.generar_ot(self.cx, "pauta-fantasma", "cliente:planta")


class LaSemillaDeLosCasos(Base):
    def test_cada_protocolo_de_datos_tiene_su_documento_y_pautas_que_existen(self):
        pautas = {json.loads(r.read_text(encoding="utf-8"))["id"] for r in DATOS.glob("pauta-*.json")}
        for d in json.loads(SEMILLA.read_text(encoding="utf-8")):
            self.assertTrue((DATOS / d["documento"]).is_file(), d["documento"])
            self.assertTrue(d["pautas"], d["id"])
            self.assertLessEqual(set(d["pautas"]), pautas, d["id"])

    def test_deja_cada_pauta_de_datos_aprobada_y_con_al_menos_un_protocolo(self):
        r = protocolos.cargar_semilla(self.cx)
        disponibles = {p["id"]: p for p in catalogo.pautas_disponibles(self.cx)}
        self.assertEqual(sorted(disponibles), sorted(r["pautas"]))
        self.assertTrue(all(p["protocolos"] for p in disponibles.values()))

    def test_una_pauta_de_caso_sale_de_su_protocolo_y_del_de_aislamiento(self):
        protocolos.cargar_semilla(self.cx)
        self.assertEqual([p["id"] for p in catalogo.protocolos_de(self.cx, "pauta-celda-mt-01")], ["prot-aislamiento-01", "prot-celda-mt-01"])
        self.assertGreater(len(catalogo.pautas_de(self.cx, "prot-aislamiento-01")), 1)

    def test_se_puede_repetir_sin_duplicar(self):
        a = protocolos.cargar_semilla(self.cx)
        self.assertEqual(protocolos.cargar_semilla(self.cx), a)
        self.assertEqual(len(catalogo.listar_protocolos(self.cx)), len(a["protocolos"]))

    def test_el_protocolo_de_un_tercero_guarda_el_enlace_y_no_su_texto(self):
        protocolos.cargar_semilla(self.cx)
        p = catalogo.leer_protocolo(self.cx, "prot-camion-rigido-01")
        self.assertTrue(p["origen"].startswith("https://"))
        self.assertIn("no se copia su texto", p["texto"])


@unittest.skipUnless(TIENE_HTTPX, "necesita fastapi y httpx")
class PorHTTP(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)

    def test_de_cargar_el_protocolo_a_la_ot_del_cliente(self):
        c = self.c
        r = c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO})
        self.assertEqual((r.status_code, r.json()["id"]), (201, "prot-a"))
        r = c.post("/interno/protocolos/prot-a/pautas", json={"pauta": pauta_demo(), "actor": EQUIPO})
        self.assertEqual((r.status_code, r.json()["aprobada"], r.json()["protocolos"][0]["id"]), (201, False, "prot-a"))
        self.assertEqual(c.get("/cliente/pautas").json(), [])
        self.assertEqual(c.post("/cliente/ots", json={"pauta_id": CORREA, "solicitante": "cliente:planta"}).status_code, 409)
        self.assertEqual(c.post(f"/interno/pautas/{CORREA}/versiones/1/aprobar", json={"actor": "supervisor:X"}).status_code, 200)
        self.assertEqual([p["id"] for p in c.get("/cliente/pautas").json()], [CORREA])
        r = c.post("/cliente/ots", json={"pauta_id": CORREA, "solicitante": "cliente:planta"})
        self.assertEqual((r.status_code, r.json()["ot"], r.json()["version"]), (201, "ot-0001", 1))
        ots = c.get("/cliente/ots").json()
        self.assertEqual([(o["ot"], o["pauta"], o["estado_general"]) for o in ots], [("ot-0001", CORREA, "sin_asignar")])
        self.assertEqual(c.get("/ot/ot-0001").json()["paso_actual"], "p1")

    def test_el_crud_del_protocolo_y_de_la_atribucion(self):
        c = self.c
        c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO})
        c.post("/interno/protocolos", json={**protocolo("prot-b"), "actor": EQUIPO})
        self.assertEqual(c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO}).status_code, 409)
        self.assertEqual([p["id"] for p in c.get("/interno/protocolos").json()], ["prot-a", "prot-b"])
        self.assertEqual(c.put("/interno/protocolos/prot-a", json={"nombre": "Otro nombre"}).json()["nombre"], "Otro nombre")
        self.assertEqual(c.get("/interno/protocolos/prot-a").json()["texto"], "1. Cortar la energía...")
        self.assertEqual(c.get("/interno/protocolos/nada").status_code, 404)
        c.post("/pautas", json=pauta_demo())
        r = c.put(f"/interno/pautas/{CORREA}/protocolos/prot-a", json={"actor": EQUIPO})
        self.assertEqual([p["id"] for p in r.json()["protocolos"]], ["prot-a"])
        c.put(f"/interno/pautas/{CORREA}/protocolos/prot-b", json={"actor": EQUIPO})
        self.assertEqual([p["id"] for p in c.get(f"/interno/pautas/{CORREA}/protocolos").json()], ["prot-a", "prot-b"])
        self.assertEqual(c.delete("/interno/protocolos/prot-a").status_code, 409)
        self.assertEqual(c.delete(f"/interno/pautas/{CORREA}/protocolos/prot-a").status_code, 204)
        self.assertEqual(c.delete("/interno/protocolos/prot-a").status_code, 204)
        self.assertEqual(c.put(f"/interno/pautas/{CORREA}/protocolos/nada", json={"actor": EQUIPO}).status_code, 404)
        self.assertEqual(c.get("/interno/pautas/nada/protocolos").status_code, 404)

    def test_una_pauta_mal_formada_es_422_y_un_protocolo_que_no_existe_404(self):
        self.c.post("/interno/protocolos", json={**protocolo(), "actor": EQUIPO})
        mala = pauta_demo()
        del mala["pasos"][0]["sensor"]
        self.assertEqual(self.c.post("/interno/protocolos/prot-a/pautas", json={"pauta": mala, "actor": EQUIPO}).status_code, 422)
        self.assertEqual(self.c.post("/interno/protocolos/nada/pautas", json={"pauta": pauta_demo(), "actor": EQUIPO}).status_code, 404)

    def test_con_clave_de_equipo_el_servicio_interno_la_pide_y_el_del_cliente_no(self):
        clave = {"X-Clave-Equipo": "secreta"}
        with mock.patch.dict(os.environ, {"CLAVE_EQUIPO": "secreta"}):
            cuerpo = {**protocolo(), "actor": EQUIPO}
            for r in (self.c.post("/interno/protocolos", json=cuerpo), self.c.get("/interno/protocolos"), self.c.post("/interno/protocolos/semilla"),
                      self.c.post("/interno/protocolos", json=cuerpo, headers={"X-Clave-Equipo": "otra"})):
                self.assertEqual(r.status_code, 401)
            self.assertEqual(self.c.get("/interno/protocolos", headers=clave).json(), [])
            self.assertEqual(self.c.post("/interno/protocolos/semilla", headers=clave).status_code, 200)
            self.assertEqual(self.c.get("/cliente/pautas").status_code, 200)
            self.assertEqual(self.c.post("/cliente/ots", json={"pauta_id": "pauta-brazo-01", "solicitante": "cliente:planta"}).status_code, 201)

    def test_la_semilla_deja_los_casos_listos_para_el_cliente(self):
        r = self.c.post("/interno/protocolos/semilla").json()
        self.assertIn("prot-camion-rigido-01", r["protocolos"])
        self.assertEqual(sorted(p["id"] for p in self.c.get("/cliente/pautas").json()), sorted(r["pautas"]))

    def test_la_guia_del_agente_explica_los_dos_servicios(self):
        guia = self.c.get("/agente").text
        for ruta in ("/interno/protocolos", "/interno/pautas/{pauta_id}/protocolos/{protocolo_id}", "/cliente/pautas", "/cliente/ots"):
            self.assertIn(ruta, guia)


if __name__ == "__main__":
    unittest.main()
