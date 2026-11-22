"""Lo que llega del edge, atribuido a la OT que ejecuta el operario. Casos de uso.

Correr:  python3 -m unittest discover tests
El streaming por WebSocket se prueba aparte en test_stream.py (necesita httpx).
"""

import unittest

from app import db
from app.bus import Bus, canal_ot
from app.contratos import Capa, Estado, Evento, TipoEvento
from app.protocolos import desde_json
from app.servicios import Servicios


class BusDePrueba(Bus):
    def __init__(self):
        super().__init__()
        self.mensajes: list[tuple[str, dict]] = []

    def publicar(self, canal, mensaje):
        self.mensajes.append((canal, mensaje))


class Base(unittest.TestCase):
    def setUp(self):
        self.cx = db.conectar(":memory:")
        pauta = desde_json()
        db.guardar_pauta(self.cx, pauta)
        db.abrir_ot(self.cx, "ot-1", pauta, "supervisor:X")
        db.abrir_ot(self.cx, "ot-2", pauta, "supervisor:X")
        self.bus = BusDePrueba()
        self.s = Servicios(self.cx, self.bus)

    def de_tipo(self, ot_id, tipo):
        return [e for e in db.eventos(self.cx, ot_id) if e.tipo is tipo]

    def alertas(self, ot_id, clase):
        """Las alertas de una clase: seguridad, orden, control, senal o pegado."""
        return [e for e in self.de_tipo(ot_id, TipoEvento.ALERTA)
                if (e.evidencia or {}).get("clave", "").startswith(f"{clase}:")]


class SinSesion(Base):
    def test_una_lectura_sin_ot_en_curso_no_toca_ninguna_bitacora(self):
        r = self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.assertIsNone(r["ot"])
        self.assertEqual(self.de_tipo("ot-1", TipoEvento.ALERTA), [])
        self.assertEqual(self.de_tipo("ot-2", TipoEvento.ALERTA), [])


class Atribucion(Base):
    def setUp(self):
        super().setUp()
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")

    def test_la_lectura_va_a_la_ot_del_edge_y_a_ninguna_otra(self):
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        r = self.s.recibir_lectura("edge-1", "energia", "viva")
        self.assertEqual(r["ot"], "ot-1")
        self.assertEqual(len(self.alertas("ot-1", "seguridad")), 1)
        self.assertEqual(self.de_tipo("ot-2", TipoEvento.ALERTA), [])

    def test_otro_edge_no_se_mezcla(self):
        self.s.iniciar_sesion("ot-2", "edge-2", "operario:B")
        self.s.recibir_lectura("edge-2", "reed_bloqueo", "cerrado")
        self.assertEqual(self.de_tipo("ot-1", TipoEvento.VEREDICTO), [])
        self.assertEqual(len(self.de_tipo("ot-2", TipoEvento.VEREDICTO)), 1)

    def test_iniciar_sesion_en_una_ot_que_no_existe_falla(self):
        with self.assertRaises(KeyError):
            self.s.iniciar_sesion("ot-99", "edge-1", "operario:A")


class ElSensorCierraElPaso(Base):
    def setUp(self):
        super().setUp()
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")

    def test_el_bloqueo_se_verifica_sin_que_el_operario_hable(self):
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado")
        veredictos = self.de_tipo("ot-1", TipoEvento.VEREDICTO)
        self.assertEqual(len(veredictos), 1)
        self.assertEqual(veredictos[0].paso_id, "p1")
        self.assertIs(veredictos[0].estado, Estado.VERIFICADO)

    def test_la_lectura_de_otro_paso_no_adelanta_la_pauta(self):
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.assertEqual(self.de_tipo("ot-1", TipoEvento.VEREDICTO), [])

    def test_la_misma_lectura_repetida_no_duplica_el_veredicto(self):
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado")
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado")
        self.assertEqual(len(self.de_tipo("ot-1", TipoEvento.VEREDICTO)), 1)

    def test_con_el_bloqueo_cerrado_la_guarda_cierra_el_paso_siguiente(self):
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        pasos = [e.paso_id for e in self.de_tipo("ot-1", TipoEvento.VEREDICTO)]
        self.assertEqual(pasos, ["p1", "p2"])


class AlertaDeSeguridad(Base):
    def setUp(self):
        super().setUp()
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")

    def test_entra_una_vez_mientras_dura_la_condicion(self):
        self.s.recibir_lectura("edge-1", "energia", "viva")
        for _ in range(3):
            self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.assertEqual(len(self.alertas("ot-1", "seguridad")), 1)
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "error")

    def test_si_la_condicion_vuelve_entra_otra_vez(self):
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.s.recibir_lectura("edge-1", "guarda", "cerrada")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.assertEqual(len(self.alertas("ot-1", "seguridad")), 2)


class LecturaDuplicada(Base):
    def test_el_edge_reenvia_tras_un_corte_y_no_se_cuenta_dos_veces(self):
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado", seq=41)
        r = self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado", seq=41)
        self.assertTrue(r["duplicada"])


class AnomaliaDeSenal(Base):
    def setUp(self):
        super().setUp()
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")
        for v in [2.0, 2.1, 1.9, 2.0, 2.2, 1.8, 2.0, 2.1, 1.9, 2.0, 2.05, 1.95]:
            self.s.recibir_lectura("edge-1", "vibracion", str(v))

    def test_un_pico_entra_como_alerta_de_capa2_una_sola_vez(self):
        self.s.recibir_lectura("edge-1", "vibracion", "6.5")
        self.s.recibir_lectura("edge-1", "vibracion", "6.8")
        alertas = self.de_tipo("ot-1", TipoEvento.ALERTA)
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0].capa, Capa.APRENDIZAJE)
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "warning")

    def test_cuando_la_senal_vuelve_a_lo_normal_la_ot_vuelve_a_ok(self):
        self.s.recibir_lectura("edge-1", "vibracion", "6.5")
        self.s.recibir_lectura("edge-1", "vibracion", "2.0")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")

    def test_la_temperatura_de_la_sala_puede_repetirse_sin_que_el_sensor_este_pegado(self):
        for _ in range(15):
            self.s.recibir_lectura("edge-1", "temp_c", "25.8")
            self.s.recibir_lectura("edge-1", "vibracion", "2.0")
        # la regla sigue para los demás sensores
        self.assertEqual([a.evidencia["sensor"] for a in self.alertas("ot-1", "pegado")], ["vibracion"])

    def test_la_distancia_no_se_compara_con_su_historia(self):
        # Cambia cada vez que alguien se mueve, y el edge ya la lee como «operario presente o ausente».
        for v in [102.1, 101.8, 102.4, 102.0, 102.3, 101.9, 102.1, 102.2, 101.7, 102.0, 102.1, 102.3]:
            self.s.recibir_lectura("edge-1", "dist_cm", str(v))
        self.s.recibir_lectura("edge-1", "dist_cm", "148.9")
        self.assertEqual(self.alertas("ot-1", "senal"), [])
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")

    def test_una_alerta_de_distancia_que_quedo_abierta_se_cierra_con_la_lectura_siguiente(self):
        # La dejó abierta un servidor anterior, y la distancia sigue lejos de su historia: sola no se cerraría.
        for v in [102.1, 101.8, 102.4, 102.0, 102.3, 101.9, 102.1, 102.2, 101.7, 102.0, 102.1, 102.3]:
            self.s.recibir_lectura("edge-1", "dist_cm", str(v))
        abierta = self.s.agregar(Evento(
            ot_id="ot-1", tipo=TipoEvento.ALERTA, ts=db.ahora(), actor="sistema", capa=Capa.APRENDIZAJE,
            detalle="dist_cm = 148.9, lejos de su mediana 102.1 (22.9 desvíos)",
            evidencia={"tipo": "senal", "sensor": "dist_cm", "valor": 148.9, "certeza": 1.0, "clave": "senal:dist_cm"}))
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "warning")
        self.s.recibir_lectura("edge-1", "dist_cm", "151.1")
        resueltas = self.de_tipo("ot-1", TipoEvento.ALERTA_RESUELTA)
        self.assertEqual([r.evidencia["resuelve"] for r in resueltas], [abierta.id])
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "ok")

    def test_un_valor_no_numerico_no_pasa_por_la_capa2(self):
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.assertEqual(
            [a for a in self.de_tipo("ot-1", TipoEvento.ALERTA) if a.capa == Capa.APRENDIZAJE], []
        )


class LoQueVeLaUI(Base):
    def setUp(self):
        super().setUp()
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")

    def test_cada_evento_nuevo_sale_por_el_canal_de_su_ot_con_su_calificacion(self):
        self.bus.mensajes.clear()
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado")
        tipos = [m["tipo"] for c, m in self.bus.mensajes if c == canal_ot("ot-1")]
        self.assertEqual(tipos, ["lectura", "evento", "calificacion_ot"])
        evento = next(m for c, m in self.bus.mensajes if m["tipo"] == "evento")
        self.assertEqual(evento["evento"]["calificacion"]["nivel"], "ok")

    def test_el_snapshot_trae_estado_calificacion_sesion_y_bitacora(self):
        snap = self.s.snapshot("ot-1")
        self.assertEqual(snap["estado"]["paso_actual"], "p1")
        self.assertEqual(snap["calificacion"]["nivel"], "ok")
        self.assertEqual(snap["sesion"]["operario"], "operario:A")
        self.assertEqual(snap["bitacora"][0]["tipo"], TipoEvento.OT_ABIERTA)

    def test_al_reconectar_solo_trae_la_bitacora_que_falta(self):
        ultimo = self.s.snapshot("ot-1")["bitacora"][-1]["id"]
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "cerrado")
        nuevos = self.s.snapshot("ot-1", desde=ultimo)["bitacora"]
        self.assertEqual([e["paso_id"] for e in nuevos], ["p1"])


class ElWarningSeVaCuandoElSensorSeCorrige(Base):
    def setUp(self):
        super().setUp()
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")

    def test_la_alerta_de_seguridad_se_abre_y_se_resuelve_con_el_sensor(self):
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        c = self.s.calificacion("ot-1")
        self.assertEqual(c["nivel"], "error")
        self.assertIn("GUARDA ABIERTA CON ENERGÍA VIVA", c["avisos"][0]["motivos"][0])
        abierta = self.alertas("ot-1", "seguridad")[0]

        self.s.recibir_lectura("edge-1", "guarda", "cerrada")
        resuelta = [e for e in self.de_tipo("ot-1", TipoEvento.ALERTA_RESUELTA) if e.evidencia["resuelve"] == abierta.id]
        self.assertEqual(len(resuelta), 1)
        self.assertEqual(self.s.alertas_activas("ot-1"), {})
        c = self.s.calificacion("ot-1")
        self.assertEqual((c["nivel"], c["avisos"]), ("ok", []))

    def test_cortar_la_energia_tambien_la_resuelve(self):
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.s.recibir_lectura("edge-1", "energia", "cortada")
        self.assertEqual(len(self.de_tipo("ot-1", TipoEvento.ALERTA_RESUELTA)), 1)

    def test_el_warning_de_senal_se_va_cuando_vuelve_a_lo_normal(self):
        for v in [2.0, 2.1, 1.9, 2.0, 2.2, 1.8, 2.0, 2.1, 1.9, 2.0, 2.05, 1.95]:
            self.s.recibir_lectura("edge-1", "vibracion", str(v))
        self.s.recibir_lectura("edge-1", "vibracion", "6.5")
        self.assertEqual(self.s.calificacion("ot-1")["avisos"][0]["nivel"], "warning")
        self.s.recibir_lectura("edge-1", "vibracion", "2.0")
        resuelta = self.de_tipo("ot-1", TipoEvento.ALERTA_RESUELTA)
        self.assertEqual(resuelta[0].capa, Capa.APRENDIZAJE)
        self.assertEqual(self.s.calificacion("ot-1")["avisos"], [])

    def test_la_bitacora_muestra_la_resolucion_como_ok(self):
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        self.bus.mensajes.clear()
        self.s.recibir_lectura("edge-1", "guarda", "cerrada")
        evento = next(m["evento"] for _, m in self.bus.mensajes if m["tipo"] == "evento")
        self.assertEqual(evento["tipo"], TipoEvento.ALERTA_RESUELTA)
        self.assertEqual(evento["calificacion"]["nivel"], "ok")
        ultimo = [m for _, m in self.bus.mensajes if m["tipo"] == "calificacion_ot"][-1]
        self.assertEqual(ultimo["calificacion"]["avisos"], [])

    def test_una_alerta_abierta_sobrevive_a_un_reinicio_y_igual_se_resuelve(self):
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")
        otra = Servicios(self.cx, BusDePrueba())
        self.assertEqual([k.split(":")[0] for k in otra.alertas_activas("ot-1")], ["seguridad", "orden"])
        otra.recibir_lectura("edge-1", "guarda", "cerrada")
        self.assertEqual(otra.alertas_activas("ot-1"), {})
        self.assertEqual(len(self.alertas("ot-1", "seguridad")), 1)


class LaCalificacionSoloMiraLosSensoresDeSuEstacion(Base):
    """Los sensores son una tabla global; una OT que ningún edge ejecuta no tiene sensores de ahora."""

    def setUp(self):
        super().setUp()
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")

    def peligro_en_edge_1(self):
        self.s.recibir_lectura("edge-1", "energia", "viva")
        self.s.recibir_lectura("edge-1", "guarda", "abierta")

    def test_el_peligro_de_una_estacion_no_pone_en_error_a_otra_ot(self):
        self.peligro_en_edge_1()
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "error")
        c = self.s.calificacion("ot-2")
        self.assertEqual((c["nivel"], c["avisos"]), ("ok", []))

    def test_una_ot_sin_sesion_no_avisa_frescura_por_un_sensor_ajeno(self):
        self.s.terminar_sesion("edge-1")
        db.escribir_sensor(self.cx, "reed_bloqueo", "abierto")
        self.cx.execute("UPDATE sensores SET ts = '2026-01-01T00:00:00+00:00'")
        self.assertEqual(self.s.calificacion("ot-2")["avisos"], [])

    def test_si_la_sesion_termina_con_el_peligro_abierto_la_ot_sigue_en_error(self):
        self.peligro_en_edge_1()
        self.s.terminar_sesion("edge-1")
        db.escribir_sensor(self.cx, "guarda", "cerrada")
        c = self.s.calificacion("ot-1")
        self.assertEqual(c["nivel"], "error")
        self.assertIn("GUARDA ABIERTA CON ENERGÍA VIVA", c["avisos"][0]["motivos"][0])


class ElJuezDeCamaraMiraElCuadroDelEdge(Base):
    JPEG = b"\xff\xd8" + b"cuadro" + b"\xff\xd9"

    def setUp(self):
        import tempfile
        from pathlib import Path

        from app.video import Video

        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.recibidos = []

        def juez(pregunta, cuadro):
            self.recibidos.append(cuadro)
            return (cuadro is not None, 0.9)

        self.s = Servicios(self.cx, self.bus, Video(Path(self.tmp.name)), juez)
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")
        for sensor, valor in [("reed_bloqueo", "cerrado"), ("guarda", "abierta")]:
            self.s.recibir_lectura("edge-1", sensor, valor)

    def tearDown(self):
        self.tmp.cleanup()

    def test_con_video_el_juez_recibe_el_ultimo_cuadro_y_queda_como_evidencia(self):
        self.s.video.recibir("edge-1", self.JPEG)
        r = self.s.declarar("ot-1", "operario:A", "rodillo cambiado")
        self.assertEqual(r["paso"], "p3")
        self.assertEqual(self.recibidos, [self.JPEG])
        self.assertEqual(r["estado"], "verificado")
        self.assertTrue(r["evidencia"]["cuadro"].endswith("ot-1-p3-1.jpg"))

    def test_sin_video_no_se_le_pregunta_al_juez_y_el_paso_no_se_verifica(self):
        r = self.s.declarar("ot-1", "operario:A", "rodillo cambiado")
        self.assertEqual(self.recibidos, [])
        self.assertEqual(r["estado"], "no_verificado")
        self.assertEqual(self.s.calificacion("ot-1")["nivel"], "warning")

    def test_un_cuadro_viejo_cuenta_como_sin_video(self):
        import time

        from app.video import SEGUNDOS_GUARDADOS

        c = self.s.video.recibir("edge-1", self.JPEG)
        object.__setattr__(c, "ts", time.time() - SEGUNDOS_GUARDADOS - 1)
        self.assertEqual(self.s.declarar("ot-1", "operario:A", "rodillo cambiado")["estado"], "no_verificado")

    def test_la_pauta_completa_no_admite_mas_declaraciones(self):
        from app.catalogo import ReglaDeNegocio

        self.s.video.recibir("edge-1", self.JPEG)
        self.s.declarar("ot-1", "operario:A", "rodillo cambiado")      # p3, cámara
        self.s.recibir_lectura("edge-1", "guarda", "cerrada")          # p4 se cierra solo
        self.s.recibir_lectura("edge-1", "reed_bloqueo", "abierto")    # p5 se cierra solo
        self.s.declarar("ot-1", "operario:A", "la correa paró")        # p6, confirmación
        self.assertEqual(self.s.snapshot("ot-1")["estado"]["completa"], True)
        with self.assertRaises(ReglaDeNegocio):
            self.s.declarar("ot-1", "operario:A", "otra vez")


if __name__ == "__main__":
    unittest.main()
