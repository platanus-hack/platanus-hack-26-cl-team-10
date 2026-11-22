"""Mejora continua de las pautas y métricas de la empresa (ADR-0014). Casos de uso, por HTTP.

Correr:  uv run --with httpx python -m unittest tests.test_mejora_y_metricas
"""

import importlib.util
import json
import unittest

from app import db, protocolos

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None

SUPERVISORA, OPERADORA, OPERADOR = "carla.munoz@oculta.example", "ana.rojas@oculta.example", "bruno.diaz@oculta.example"
PROPUESTA_DE_LA_SEMILLA = "pauta-polin-demo:v1:p3"
OTS_DE_LA_SEMILLA = len(json.loads((protocolos.DATOS / "ots-semilla.json").read_text())["ots"])


@unittest.skipUnless(TIENE_HTTPX, "requiere fastapi y httpx")
class Base(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app import api
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.accesos = {a["usuario"]: a["clave"] for a in self.c.post("/interno/ots/semilla").json()["accesos"]}
        self.carla, self.ana, self.bruno = (self.cabecera(u) for u in (SUPERVISORA, OPERADORA, OPERADOR))

    def cabecera(self, usuario, clave=None):
        r = self.c.post("/auth/entrar", json={"usuario": usuario, "clave": clave or self.accesos[usuario]})
        self.assertEqual(r.status_code, 200)
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def otra_empresa(self):
        self.c.post("/interno/clientes", json={"id": "otra", "nombre": "Otra Minera"})
        clave = self.c.post("/interno/clientes/otra/personas", json={
            "id": "supervisor:otra", "nombre": "Pedro", "usuario": "pedro@otra.example", "rol": "supervisor"}).json()["clave"]
        return self.cabecera("pedro@otra.example", clave)

    def ot_asignada(self, operador="operario:1", pauta="pauta-polin-demo"):
        ot = self.c.post("/cliente/ots", json={"pauta_id": pauta}, headers=self.carla).json()["ot"]
        self.c.post(f"/cliente/ots/{ot}/asignar", json={"operador": operador}, headers=self.carla)
        return ot

    def ejecutar_hasta_p3(self, ot, cabecera, edge):
        """Corta la energía, pone el candado y se acerca, en orden: los sensores cierran los tres pasos."""
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": edge}, headers=cabecera).status_code, 200)
        lecturas = [{"sensor_id": s, "valor": v, "seq": i} for i, (s, v) in enumerate(
            [("energia", "cortada"), ("bloqueo", "puesto"), ("operario", "presente")], 1)]
        self.c.post(f"/edge/{edge}/lecturas", json=lecturas)
        self.c.delete(f"/edge/{edge}/sesion")


class LaObservacionDelOperario(Base):
    def test_el_operario_deja_lo_que_vio_y_queda_en_la_bitacora_a_su_nombre_sin_cerrar_ningun_paso(self):
        ot = self.ot_asignada()
        antes = self.c.get(f"/ot/{ot}").json()
        r = self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.ana,
                        json={"texto": "  el candado no entra en el punto de bloqueo  ", "categoria": "pauta", "paso_id": "p2"})
        self.assertEqual(r.status_code, 201)
        ev = r.json()
        self.assertEqual((ev["tipo"], ev["actor"], ev["paso_id"], ev["declarado"], ev["estado"]),
                         ("observacion", "operario:1", "p2", "el candado no entra en el punto de bloqueo", None))
        self.assertEqual(ev["evidencia"], {"tipo": "observacion", "categoria": "pauta"})
        self.assertEqual(self.c.get(f"/ot/{ot}").json(), antes)
        self.assertIn("observacion", [e["tipo"] for e in self.c.get(f"/ot/{ot}/eventos").json()])

    def test_el_supervisor_tambien_observa_y_sin_paso_tambien_sirve(self):
        ot = self.ot_asignada()
        r = self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.carla, json={"texto": "falta luz en la estación", "categoria": "equipo"})
        self.assertEqual((r.status_code, r.json()["actor"], r.json()["paso_id"]), (201, "supervisor:oculta", None))

    def test_sin_texto_con_un_paso_ajeno_o_sobre_una_ot_que_no_es_suya_no_entra(self):
        ot = self.ot_asignada()
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.ana, json={"texto": "   "}).status_code, 409)
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.ana,
                                     json={"texto": "x", "paso_id": "p99"}).status_code, 404)
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.bruno, json={"texto": "x"}).status_code, 404)
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.otra_empresa(), json={"texto": "x"}).status_code, 404)
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.ana,
                                     json={"texto": "x", "categoria": "chisme"}).status_code, 422)
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/observaciones", json={"texto": "x"}).status_code, 401)


class LaMejoraContinua(Base):
    def propuesta(self, cabecera=None, pid=PROPUESTA_DE_LA_SEMILLA):
        return next((p for p in self.c.get("/cliente/mejoras", headers=cabecera or self.carla).json() if p["id"] == pid), None)

    def test_de_la_semilla_nace_una_propuesta_con_dos_ot_y_dos_operarios(self):
        p = self.propuesta()
        self.assertEqual((p["pauta"], p["version"], p["paso"], p["estado"]), ("pauta-polin-demo", 1, "p3", "abierta"))
        self.assertEqual((p["ots_con_senal"], p["operarios_distintos"]), (2, 2))
        self.assertEqual((p["senales"]["orden"], p["senales"]["observacion"]), (1, 1))
        self.assertIn("punto de bloqueo", p["observaciones"][0]["texto"])
        self.assertEqual([x["id"] for x in p["protocolos"]], ["prot-maqueta-01"])

    def test_una_sola_ot_con_senal_no_es_una_propuesta(self):
        for p in self.c.get("/cliente/mejoras", headers=self.carla).json():
            if p["tipo"] == "desviacion":  # las de conformidad salen de la pauta misma, sin OT
                self.assertGreaterEqual(p["ots_con_senal"], 2, p["id"])
        ids = {p["id"] for p in self.c.get("/cliente/mejoras", headers=self.carla).json()}
        self.assertNotIn("pauta-correa-ct-01:v1:p1", ids)

    def test_una_observacion_de_equipo_no_alimenta_la_pauta(self):
        ot = self.ot_asignada()
        for cabecera in (self.ana, self.carla):
            self.c.post(f"/cliente/ots/{ot}/observaciones", headers=cabecera, json={"texto": "suena", "categoria": "equipo", "paso_id": "p4"})
        self.assertNotIn("pauta-polin-demo:v1:p4", {p["id"] for p in self.c.get("/cliente/mejoras", headers=self.carla).json()})

    def test_el_supervisor_valida_descartar_pide_nota_y_puede_cambiar_de_opinion(self):
        ruta = f"/cliente/mejoras/{PROPUESTA_DE_LA_SEMILLA}/revision"
        self.assertEqual(self.c.post(ruta, json={"decision": "descartar"}, headers=self.carla).status_code, 409)
        r = self.c.post(ruta, json={"decision": "descartar", "nota": "es un caso del demo"}, headers=self.carla)
        self.assertEqual((r.status_code, r.json()["estado"], r.json()["revision"]["nota"]), (200, "descartada", "es un caso del demo"))
        r = self.c.post(ruta, json={"decision": "aceptar", "nota": "mejor sí"}, headers=self.carla)
        self.assertEqual((r.json()["estado"], r.json()["revision"]["por"]), ("aceptada", "supervisor:oculta"))
        self.assertEqual([p["id"] for p in self.c.get("/cliente/mejoras?estado=aceptada", headers=self.carla).json()], [PROPUESTA_DE_LA_SEMILLA])
        self.assertEqual(self.c.get("/cliente/mejoras?estado=descartada", headers=self.carla).json(), [])

    def test_solo_el_supervisor_de_la_empresa_ve_y_valida(self):
        self.assertEqual(self.c.get("/cliente/mejoras", headers=self.ana).status_code, 403)
        self.assertEqual(self.c.post(f"/cliente/mejoras/{PROPUESTA_DE_LA_SEMILLA}/revision", json={"decision": "aceptar"},
                                     headers=self.ana).status_code, 403)
        pedro = self.otra_empresa()
        self.assertEqual(self.c.get("/cliente/mejoras", headers=pedro).json(), [])
        self.assertEqual(self.c.post(f"/cliente/mejoras/{PROPUESTA_DE_LA_SEMILLA}/revision", json={"decision": "aceptar"},
                                     headers=pedro).status_code, 404)

    def test_el_ciclo_completo_de_la_propuesta_a_la_version_nueva_que_deja_de_desviarse(self):
        self.c.post(f"/cliente/mejoras/{PROPUESTA_DE_LA_SEMILLA}/revision", json={"decision": "aceptar", "nota": "poner el bloqueo junto al tablero"}, headers=self.carla)

        aceptadas = self.c.get("/interno/mejoras").json()
        self.assertEqual([(m["id"], m["cliente"]["id"]) for m in aceptadas], [(PROPUESTA_DE_LA_SEMILLA, "oculta")])

        pauta = {**json.loads((protocolos.DATOS / "pauta-polin-demo.json").read_text()), "version": 2}
        pauta["pasos"][1]["instruccion"] = "Pon tu candado en el punto de bloqueo junto al tablero, antes de acercarte."
        r = self.c.post("/interno/protocolos/prot-correa-01/pautas", json={"pauta": pauta, "actor": "equipo:factum"})
        self.assertEqual((r.status_code, r.json()["version"]), (201, 2))
        self.assertEqual(self.c.post("/interno/pautas/pauta-polin-demo/versiones/2/aprobar", json={"actor": "supervisor:factum"}).status_code, 200)

        p = self.propuesta()
        self.assertEqual((p["estado"], p["validacion"]["resultado"], p["validacion"]["ejecuciones"]), ("aplicada", "sin_datos", 0))
        self.assertEqual(self.c.post(f"/cliente/mejoras/{PROPUESTA_DE_LA_SEMILLA}/revision", json={"decision": "descartar", "nota": "x"},
                                     headers=self.carla).status_code, 409)

        sin_ejecutar = self.ot_asignada()
        self.assertEqual(self.propuesta()["validacion"]["ejecuciones"], 0, sin_ejecutar)

        ot = self.ot_asignada()
        self.ejecutar_hasta_p3(ot, self.ana, "edge-mejora")
        self.assertEqual(self.c.get(f"/cliente/ots/{ot}", headers=self.carla).json()["version"], 2)
        v = self.propuesta()["validacion"]
        # bajó a 0 de 1, pero una OT no alcanza para decir que mejoró: puede ser azar (app/recurrencia.py)
        self.assertEqual((v["version_nueva"], v["ejecuciones"], v["ots_con_senal"], v["resultado"]), (2, 1, 0, "sin_evidencia"))

    def test_si_en_la_version_nueva_el_paso_se_sigue_desviando_lo_dice(self):
        pauta = {**json.loads((protocolos.DATOS / "pauta-polin-demo.json").read_text()), "version": 2}
        self.c.post("/interno/protocolos/prot-correa-01/pautas", json={"pauta": pauta, "actor": "equipo:factum"})
        self.c.post("/interno/pautas/pauta-polin-demo/versiones/2/aprobar", json={"actor": "supervisor:factum"})
        ot = self.ot_asignada()
        self.c.post(f"/cliente/ots/{ot}/observaciones", headers=self.ana,
                    json={"texto": "sigue quedando a dos pasos", "categoria": "pauta", "paso_id": "p3"})
        v = self.propuesta()
        self.assertEqual((v["estado"], v["validacion"]["resultado"]), ("superada", "se_repite"))


class LasMetricas(Base):
    def test_el_resumen_cuadra_con_la_semilla(self):
        m = self.c.get("/cliente/metricas", headers=self.carla).json()
        self.assertEqual(m["ots"]["total"], OTS_DE_LA_SEMILLA)
        self.assertEqual(sum(m["ots"]["por_estado"].values()), OTS_DE_LA_SEMILLA)
        self.assertEqual(m["ots"]["por_estado"]["completa"], m["cumplimiento"]["completas"])
        self.assertEqual(m["pasos"]["verificados"], sum(m["pasos"]["por_evidencia"].values()))
        self.assertEqual(m["desviaciones"]["total"], sum(m["desviaciones"]["por_clase"].values()))
        self.assertEqual(m["observaciones"]["total"], 4)
        # 2 por desviaciones (acercarse antes del candado, y encender la cinta sin alejarse) y 4 de conformidad: el rodillo
        # junta aislar y bloquear y no comprueba energía cero, a la LOTO del escritorio le falta apagar el motor y a la
        # de la estación, el candado (ADR-0016)
        self.assertEqual(m["mejoras"]["abierta"], 6)
        self.assertGreater(m["desviaciones"]["por_clase"]["seguridad"], 0)

    def test_un_paso_confirmado_por_persona_cuenta_como_desviacion_y_la_ot_deja_de_estar_limpia(self):
        ot = self.ot_asignada()
        antes = self.c.get("/cliente/metricas", headers=self.carla).json()
        r = self.c.post(f"/ot/{ot}/pasos/p1/confirmar", json={"actor": "operario:1", "motivo": "el sensor de energía está caído"})
        self.assertEqual(r.status_code, 200)
        despues = self.c.get("/cliente/metricas", headers=self.carla).json()
        self.assertEqual(despues["desviaciones"]["por_clase"]["persona"], antes["desviaciones"]["por_clase"]["persona"] + 1)
        self.assertEqual(despues["pasos"]["por_evidencia"]["persona"], antes["pasos"]["por_evidencia"]["persona"] + 1)
        pasos = self.c.get("/cliente/metricas/pautas/pauta-polin-demo/pasos", headers=self.carla).json()
        self.assertEqual(pasos[0]["paso"], "p1")
        self.assertEqual(pasos[0]["por_clase"]["persona"], 1)

    def test_por_pauta_y_por_equipo_se_ordenan_como_se_pide(self):
        por_desviaciones = self.c.get("/cliente/metricas/pautas", headers=self.carla).json()
        self.assertEqual([p["desviaciones"] for p in por_desviaciones], sorted((p["desviaciones"] for p in por_desviaciones), reverse=True))
        por_ots = self.c.get("/cliente/metricas/equipos?orden=ots&limite=3", headers=self.carla).json()
        self.assertEqual(len(por_ots), 3)
        self.assertEqual([e["ots"] for e in por_ots], sorted((e["ots"] for e in por_ots), reverse=True))
        cumplimiento = [p["cumplimiento"]["porcentaje"] for p in
                        self.c.get("/cliente/metricas/pautas?orden=cumplimiento", headers=self.carla).json()]
        con_dato = [x for x in cumplimiento if x is not None]
        self.assertEqual(con_dato, sorted(con_dato))
        self.assertEqual(cumplimiento[:len(con_dato)], con_dato)
        self.assertEqual(self.c.get("/cliente/metricas/pautas?orden=nombre", headers=self.carla).status_code, 422)
        self.assertEqual(self.c.get("/cliente/metricas/pautas?limite=0", headers=self.carla).status_code, 422)

    def test_por_equipo_trae_lo_que_observaron_de_la_maquina(self):
        equipos = {e["equipo"]: e for e in self.c.get("/cliente/metricas/equipos", headers=self.carla).json()}
        self.assertIn("polín 14", equipos["correa CT-01, estación de polines 14"]["observaciones_del_equipo"][0]["texto"])

    def test_por_paso_va_en_el_orden_de_la_pauta_o_por_desviaciones(self):
        en_orden = self.c.get("/cliente/metricas/pautas/pauta-polin-demo/pasos", headers=self.carla).json()
        self.assertEqual([p["orden"] for p in en_orden], list(range(1, 9)))
        desviados = self.c.get("/cliente/metricas/pautas/pauta-polin-demo/pasos?orden=desviaciones", headers=self.carla).json()
        self.assertEqual(desviados[0]["paso"], "p3")
        self.assertEqual(self.c.get("/cliente/metricas/pautas/pauta-polin-demo/pasos?version=9", headers=self.carla).status_code, 404)

    def test_la_serie_no_tiene_huecos_y_suma_lo_mismo_que_el_resumen(self):
        serie = self.c.get("/cliente/metricas/serie", headers=self.carla).json()
        dias = [s["periodo"] for s in serie]
        self.assertEqual(dias, sorted(dias))
        self.assertEqual(sum(s["ots_abiertas"] for s in serie), OTS_DE_LA_SEMILLA)
        resumen = self.c.get("/cliente/metricas", headers=self.carla).json()
        alertas = sum(resumen["desviaciones"]["por_clase"][c] for c in ("seguridad", "orden", "control"))
        self.assertEqual(sum(s["desviaciones"] for s in serie), alertas)
        semanas = self.c.get("/cliente/metricas/serie?intervalo=semana", headers=self.carla).json()
        self.assertEqual(sum(s["ots_abiertas"] for s in semanas), OTS_DE_LA_SEMILLA)
        meses = self.c.get("/cliente/metricas/serie?intervalo=mes", headers=self.carla).json()
        self.assertEqual(sum(s["ots_abiertas"] for s in meses), OTS_DE_LA_SEMILLA)
        self.assertTrue(all(s["periodo"].endswith("-01") for s in meses), meses)

    def test_el_periodo_filtra_por_el_dia_en_que_se_abrio_la_ot(self):
        serie = self.c.get("/cliente/metricas/serie", headers=self.carla).json()
        ultimo = serie[-1]["periodo"]
        m = self.c.get(f"/cliente/metricas?desde={ultimo}&hasta={ultimo}", headers=self.carla).json()
        self.assertEqual(m["ots"]["total"], serie[-1]["ots_abiertas"])
        self.assertEqual(self.c.get("/cliente/metricas?desde=2026-11-20&hasta=2026-11-01", headers=self.carla).status_code, 422)
        self.assertEqual(self.c.get("/cliente/metricas?desde=ayer", headers=self.carla).status_code, 422)

    def test_solo_el_supervisor_y_solo_lo_de_su_empresa(self):
        for ruta in ("/cliente/metricas", "/cliente/metricas/pautas", "/cliente/metricas/equipos",
                     "/cliente/metricas/serie", "/cliente/metricas/pautas/pauta-polin-demo/pasos"):
            self.assertEqual(self.c.get(ruta, headers=self.ana).status_code, 403, ruta)
            self.assertEqual(self.c.get(ruta).status_code, 401, ruta)
        pedro = self.otra_empresa()
        self.assertEqual(self.c.get("/cliente/metricas", headers=pedro).json()["ots"]["total"], 0)
        self.assertEqual(self.c.get("/cliente/metricas/pautas", headers=pedro).json(), [])
        self.assertEqual(self.c.get("/cliente/metricas/pautas/pauta-polin-demo/pasos", headers=pedro).status_code, 404)

    def test_nada_de_las_metricas_ni_de_las_propuestas_nombra_a_un_operario(self):
        for ruta in ("/cliente/metricas", "/cliente/metricas/pautas", "/cliente/metricas/equipos", "/cliente/metricas/serie",
                     "/cliente/metricas/pautas/pauta-polin-demo/pasos", "/cliente/mejoras"):
            texto = self.c.get(ruta, headers=self.carla).text
            for quien in ("operario:1", "operario:2", "Ana Rojas", "Bruno Díaz"):
                self.assertNotIn(quien, texto, ruta)


if __name__ == "__main__":
    unittest.main()


class ElAvisoAlSupervisor(Base):
    """Apenas un paso se vuelve recurrente, la recomendación le llega al supervisor (servicios._vigilar_patrones)."""

    def acercarse_con_el_motor_encendido(self, i):
        ot = self.ot_asignada(pauta="pauta-polin-estacion")
        edge = f"edge-aviso-{i}"
        self.assertEqual(self.c.post(f"/cliente/ots/{ot}/sesion", json={"edge_id": edge}, headers=self.ana).status_code, 200)
        lecturas = [("energia", "viva"), ("operario", "ausente"), ("operario", "presente"),
                    ("energia", "cortada")]
        self.c.post(f"/edge/{edge}/lecturas", json=[{"sensor_id": s, "valor": v} for s, v in lecturas])
        self.c.delete(f"/edge/{edge}/sesion")
        return ot

    def detectadas(self):
        return [p for p in self.c.get("/cliente/mejoras", headers=self.carla).json() if p["detectada"] and p["tipo"] == "desviacion"]

    def test_a_la_cuarta_ot_que_se_acerca_sin_apagar_el_motor_aparece_la_recomendacion(self):
        # La versión ya trae 4 OT de la semilla sin esa desviación. Con el α repartido entre las miradas
        # (mejora.alfa_en_vivo) el aviso llega a la cuarta OT seguida que se salta el paso: con 8 OT en la versión,
        # 4 de 4 nuevas con señal y el resto limpio ya no puede ser azar.
        nuevas = [self.acercarse_con_el_motor_encendido(i) for i in range(3)]
        self.assertEqual(self.detectadas(), [], nuevas)
        cuarta = self.acercarse_con_el_motor_encendido(3)
        [p] = self.detectadas()
        self.assertEqual((p["paso"], p["titulo"], p["detectada"]["ot"]), ("e1", "Apagar el motor", cuarta))
        self.assertGreaterEqual(p["senales"]["seguridad"], 3)
        eventos = self.c.get(f"/cliente/ots/{cuarta}/eventos", headers=self.carla).json()
        aviso = next(e for e in eventos if e["tipo"] == "propuesta_pauta")
        self.assertIn("«Apagar el motor»", aviso["detalle"])
        self.assertNotIn("Ana", aviso["detalle"])
        # una cuarta OT no repite el aviso
        self.acercarse_con_el_motor_encendido(3)
        self.assertEqual(len(self.detectadas()), 1)


class LaEscaladaQuedaFirme(Base):
    def test_una_propuesta_escalada_sigue_escalada_aunque_la_validacion_oscile(self):
        from app import api, mejora

        pid = PROPUESTA_DE_LA_SEMILLA
        antes = next(p for p in self.c.get("/cliente/mejoras", headers=self.carla).json() if p["id"] == pid)
        self.assertFalse(antes["escalar"])
        mejora.registrar_escaladas(api.cx, [{**antes, "escalar": True}], "oculta")
        despues = next(p for p in self.c.get("/cliente/mejoras", headers=self.carla).json() if p["id"] == pid)
        self.assertTrue(despues["escalar"])
        self.assertIn("la pauta no es la causa", despues["sugerencia"])


class ElCambioDePolinConElProtocoloCorto(Base):
    """El recorrido del demo (datos/pauta-polin-corto.json): la OT llega entregada después de «Apagar el sistema»; quien
    recibe el turno saca el polín rojo, pone el verde y enciende sin alejarse. La pauta no pide alejarse: lo propone
    Factum, cuando la alerta de esta OT se suma a las de las tres OT anteriores de la semilla."""

    OT, EDGE, PROPUESTA = "ot-1022", "edge-corto", "pauta-polin-corto:v1:c4"
    CAMBIO = "Agrega «Alejarte del equipo» antes de «Encender el sistema»"

    def leer(self, sensor, valor):
        r = self.c.post(f"/edge/{self.EDGE}/lecturas", json=[{"sensor_id": sensor, "valor": valor}]).json()[0]
        return [e["detalle"] for e in r["eventos"] if e["tipo"] == "alerta"]

    def ver(self, *clases):
        from app import api
        from app.servicios import DETECCIONES_MIN

        s = api.servicios
        s.video._detecciones[self.EDGE].clear()
        for _ in range(DETECCIONES_MIN):
            s._ultimo_juicio.clear()
            s.recibir_detecciones(self.EDGE, {"clases": ["soda can", "red soda can", "green soda can"], "objetos": [
                {"clase": c, "conf": 0.9, "caja": [0, 0, 1, 1]} for c in clases]})

    def paso(self):
        return self.c.get(f"/ot/{self.OT}").json()["paso_actual"]

    def resumen(self):
        return [r for r in self.c.get("/cliente/mejoras/resumen", headers=self.carla).json() if r["pauta"] == "pauta-polin-corto"]

    def test_recibe_el_turno_enciende_sin_alejarse_y_factum_propone_el_paso_que_falta(self):
        ot = next(o for o in self.c.get("/cliente/ots", headers=self.carla).json() if o["ot"] == self.OT)
        self.assertEqual((ot["estado_general"], ot["cerrados"], ot["operador"]), ("entregada", 1, None))
        # la historia ya juntó tres OT con la alerta, pero con cuatro en la versión todavía puede ser azar: no se avisó
        self.assertEqual(self.resumen(), [])

        self.assertEqual(self.c.post(f"/cliente/ots/{self.OT}/relevo/recibir", headers=self.ana).status_code, 200)
        self.assertEqual(self.c.post(f"/cliente/ots/{self.OT}/sesion", json={"edge_id": self.EDGE}, headers=self.ana).status_code, 200)
        self.assertEqual(self.leer("energia", "cortada") + self.leer("operario", "presente"), [])
        self.assertEqual(self.paso(), "c2")
        self.ver("red soda can", "soda can")
        self.assertEqual(self.paso(), "c2")  # el rojo sigue en la cinta
        self.ver("soda can")
        self.assertEqual(self.paso(), "c3")
        self.ver("soda can", "green soda can")
        self.assertEqual(self.paso(), "c4")

        [alerta] = self.leer("energia", "viva")  # enciende con la mano todavía en la cinta
        self.assertTrue(alerta.startswith("PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO. Alejarse"), alerta)
        self.assertEqual(self.paso(), "c4")  # y «Encender» no se cierra
        self.assertEqual(self.leer("energia", "viva"), [])
        self.assertEqual(self.paso(), "c4")
        self.leer("operario", "ausente")
        self.leer("energia", "viva")  # el edge repite la lectura del motor: ahora sí
        self.assertIsNone(self.paso())

        p = next(m for m in self.c.get("/cliente/mejoras", headers=self.carla).json() if m["id"] == self.PROPUESTA)
        self.assertEqual((p["detectada"]["ot"], p["ots_con_senal"], p["aplicable"]), (self.OT, 4, True))
        [r] = self.resumen()
        self.assertEqual([c["que"] for c in r["cambios"]], [self.CAMBIO])
        reporte = self.c.get(f"/cliente/ots/{self.OT}/reporte?formato=markdown", headers=self.carla).text
        self.assertIn(f"**{self.CAMBIO}**", reporte)
        self.assertIn("## Relevos", reporte)

        v = self.c.post("/cliente/pautas/pauta-polin-corto/mejoras/aplicar", headers=self.carla).json()["version"]
        self.assertEqual((v["version"], v["comprobacion"]["valida"]), (2, True))
        from app import api
        pasos = db.leer_pauta(api.cx, "pauta-polin-corto", 2).en_orden
        self.assertEqual([(s.id, s.titulo) for s in pasos[3:]], [("c4", "Alejarte del equipo"), ("c5", "Encender el sistema")])
        self.assertEqual((pasos[3].sensor.id, pasos[3].sensor.espera, pasos[3].control_critico), ("operario", "ausente", True))

    def test_con_la_pauta_que_ya_pide_alejarse_la_propuesta_sigue_reescribiendo_el_paso(self):
        from app import api, sugerencias

        # La versión vigente: la pauta de la estación se sigue versionando y este caso no depende de cuál sea.
        version = db.leer_pauta(api.cx, "pauta-polin-estacion").version
        p = {"id": "x", "tipo": "desviacion", "pauta": "pauta-polin-estacion", "version": version, "paso": "e7", "ots": [],
             "senales": {"seguridad": 2}, "aplicable": True, "por_que_no": None}
        self.assertEqual([c["tipo"] for c in sugerencias.borrador(api.cx, p)["cambios"]], ["reescribe"])
