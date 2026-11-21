"""La calificación por capa, como casos de uso. Sin HTTP ni hardware.

Correr:  python3 -m unittest discover tests
"""

import unittest

from app.contratos import Capa, Estado, Evento, TipoEvento, Veredicto
from app.protocolos import desde_json
from app.reglas import evaluar
from app.scoring import Nivel, calificar, calificar_evento, calificar_ot, capa1, capa2, capa3, peor

PAUTA = desde_json()
P1 = PAUTA.paso("p1")  # sensor reed_bloqueo
P3 = PAUTA.paso("p3")  # cámara
P6 = PAUTA.paso("p6")  # confirmación


def veredicto_evento(paso_id, v):
    return Evento(ot_id="ot-1", tipo=TipoEvento.VEREDICTO, ts="t", actor="sistema",
                  paso_id=paso_id, estado=v.estado, capa=v.capa, evidencia=v.evidencia,
                  detalle=v.detalle)


class Capa1_Determinista(unittest.TestCase):
    def test_el_sensor_cierra_el_paso_y_es_ok_con_certeza_total(self):
        c = calificar(evaluar(P1, None, {"reed_bloqueo": "cerrado"}))
        self.assertIs(c.nivel, Nivel.OK)
        self.assertEqual(c.certeza, 1.0)
        self.assertEqual(c.capa, 1)

    def test_el_operario_dice_que_bloqueo_y_el_sensor_no_es_error(self):
        c = calificar(evaluar(P1, "bloqueo puesto", {"reed_bloqueo": "abierto"}))
        self.assertIs(c.nivel, Nivel.ERROR)

    def test_una_lectura_vieja_baja_la_certeza_y_avisa(self):
        c = capa1(evaluar(P1, None, {"reed_bloqueo": "cerrado"}), edad_lectura_s=8)
        self.assertIs(c.nivel, Nivel.WARNING)
        self.assertAlmostEqual(c.certeza, 0.4)

    def test_un_sensor_muerto_no_da_certeza(self):
        c = capa1(evaluar(P1, None, {"reed_bloqueo": "cerrado"}), edad_lectura_s=30)
        self.assertEqual(c.certeza, 0.0)


class Capa2_Senales(unittest.TestCase):
    NORMAL = [2.0, 2.1, 1.9, 2.0, 2.2, 1.8, 2.0, 2.1, 1.9, 2.0, 2.05, 1.95]

    def test_sin_historia_suficiente_no_juzga(self):
        c = capa2("vibracion", [2.0, 2.1], 9.0)
        self.assertIs(c.nivel, Nivel.OK)
        self.assertLess(c.certeza, 1.0)

    def test_un_valor_normal_es_ok(self):
        self.assertIs(capa2("vibracion", self.NORMAL, 2.05).nivel, Nivel.OK)

    def test_un_pico_de_vibracion_es_warning_y_nunca_error(self):
        c = capa2("vibracion", self.NORMAL, 6.0)
        self.assertIs(c.nivel, Nivel.WARNING)
        self.assertEqual(c.capa, 2)

    def test_un_sensor_sin_variacion_que_cambia_avisa(self):
        plano = [20.0] * 12
        self.assertIs(capa2("temperatura", plano, 20.0).nivel, Nivel.OK)
        self.assertIs(capa2("temperatura", plano, 23.0).nivel, Nivel.WARNING)

    def test_la_resolucion_del_sensor_no_es_anomalia(self):
        # DHT22: pasos de 0,1 °C sobre una historia plana
        self.assertIs(capa2("temp_c", [25.2] * 12, 25.3).nivel, Nivel.OK)
        # HC-SR04: ±2 cm de ruido normal a 1,8 m
        ultra = [178.1, 177.9, 178.0, 178.1, 178.0, 177.8, 178.2, 178.0, 178.1, 177.9, 178.0, 178.0]
        self.assertIs(capa2("dist_cm", ultra, 180.1).nivel, Nivel.OK)
        self.assertIs(capa2("dist_cm", ultra, 30.0).nivel, Nivel.WARNING)  # una mano sí

    def test_la_alerta_de_capa2_en_la_bitacora_es_warning(self):
        ev = Evento(ot_id="ot-1", tipo=TipoEvento.ALERTA, ts="t", actor="sistema",
                    capa=Capa.APRENDIZAJE, detalle="vibración alta", evidencia={"certeza": 0.8})
        c = calificar_evento(ev)
        self.assertIs(c.nivel, Nivel.WARNING)
        self.assertEqual(c.certeza, 0.8)


class Capa3_Camara(unittest.TestCase):
    def test_la_camara_confirma_con_confianza_alta(self):
        c = capa3(evaluar(P3, None, {}, juez_camara=lambda _: (True, 0.9)))
        self.assertIs(c.nivel, Nivel.OK)
        self.assertEqual(c.certeza, 0.9)

    def test_la_camara_confirma_con_confianza_baja_pide_mirar(self):
        c = capa3(evaluar(P3, None, {}, juez_camara=lambda _: (True, 0.55)))
        self.assertIs(c.nivel, Nivel.WARNING)

    def test_el_conflicto_de_camara_es_warning_porque_no_interrumpe(self):
        c = calificar(evaluar(P3, "rodillo listo", {}, juez_camara=lambda _: (False, 0.9)))
        self.assertIs(c.nivel, Nivel.WARNING)

    def test_sin_juez_conectado_no_hay_certeza(self):
        c = calificar(evaluar(P3, None, {}, juez_camara=None))
        self.assertIs(c.nivel, Nivel.WARNING)
        self.assertEqual(c.certeza, 0.0)


class Confirmacion(unittest.TestCase):
    def test_la_palabra_del_operario_cierra_y_queda_dicho(self):
        c = calificar(evaluar(P6, "la correa paró", {}))
        self.assertIs(c.nivel, Nivel.OK)
        self.assertIsNone(c.capa)
        self.assertIn("persona", " ".join(c.motivos))


class LaOTCompleta(unittest.TestCase):
    def test_una_ot_recien_abierta_es_ok(self):
        self.assertIs(calificar_ot([], {}).nivel, Nivel.OK)

    def test_guarda_abierta_con_energia_viva_es_error_mientras_dure(self):
        self.assertIs(calificar_ot([], {"guarda": "abierta", "energia": "viva"}).nivel, Nivel.ERROR)
        self.assertIs(calificar_ot([], {"guarda": "cerrada", "energia": "viva"}).nivel, Nivel.OK)

    def test_el_peor_paso_manda(self):
        evs = [
            veredicto_evento("p1", evaluar(P1, None, {"reed_bloqueo": "cerrado"})),
            veredicto_evento("p3", evaluar(P3, None, {}, juez_camara=lambda _: (True, 0.5))),
        ]
        self.assertIs(calificar_ot(evs, {}).nivel, Nivel.WARNING)

    def test_el_ultimo_veredicto_de_cada_paso_reemplaza_al_anterior(self):
        evs = [
            veredicto_evento("p1", evaluar(P1, "listo", {"reed_bloqueo": "abierto"})),
            veredicto_evento("p1", evaluar(P1, None, {"reed_bloqueo": "cerrado"})),
        ]
        self.assertIs(calificar_ot(evs, {}).nivel, Nivel.OK)

    def test_a_igual_gravedad_gana_la_de_menor_certeza(self):
        a = capa3(Veredicto(Estado.VERIFICADO, Capa.MODELO, "a", {"confianza": 0.6}))
        b = capa3(Veredicto(Estado.VERIFICADO, Capa.MODELO, "b", {"confianza": 0.3}))
        self.assertEqual(peor([a, b]).motivos[0], "b")


if __name__ == "__main__":
    unittest.main()
