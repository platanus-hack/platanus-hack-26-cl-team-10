"""Construcción: cada patrón de ejecución contra la barrera que lo decide. Casos de uso.

Correr:  python3 -m unittest tests.test_construccion
Cambio de manguera hidráulica en excavadora, pauta datos/pauta-excavadora.json. Cada test corre su escenario de app/escenarios.py en la caja aislada
y comprueba lo esperado (con su fuente en el escenario) más lo que importa en el oficio.
Ver knowledge/projects/escenarios-por-industria/PRD.md.
"""

import unittest
from dataclasses import replace

from app.escenarios import buscar, correr


class MangueraHidraulicaEnExcavadora(unittest.TestCase):
    def corre(self, patron, escenario=None):
        r = correr(escenario or buscar(f"CON-{patron}"))
        self.assertIsNone(r["error"])
        fallas = {k: (c["esperado"], c["obtenido"]) for k, c in r["comparacion"].items() if not c["cumple"]}
        self.assertEqual(fallas, {}, r["entonces"])
        return r

    def avisos(self, r):
        return " · ".join(e["detalle"] for e in r["bitacora"] if e["tipo"] == "alerta")

    def test_a0_el_cambio_de_manguera_bien_hecho_no_da_ninguna_falsa_alarma(self):
        self.assertIsNone(self.corre("A0")["obtenido"]["paso_actual"])

    def test_a1_bajar_los_implementos_verifica_el_paso_sin_que_el_operario_hable(self):
        self.assertEqual(self.corre("A1")["obtenido"]["estados"]["p1"], "verificado")

    def test_a2_decir_implementos_abajo_despues_del_sensor_no_abre_conflicto_en_el_motor(self):
        self.assertEqual(self.corre("A2")["obtenido"]["estados"]["p2"], "no_verificado")

    def test_a3_decir_implementos_abajo_antes_del_sensor_interrumpe_y_despues_se_verifica(self):
        self.assertEqual(self.corre("A3")["obtenido"]["estados"]["p1"], "verificado")

    def test_a4_decir_implementos_abajo_con_los_implementos_arriba_queda_en_conflicto(self):
        self.assertEqual(self.corre("A4")["obtenido"]["estados"]["p1"], "en_conflicto")

    def test_a6_un_supervisor_confirma_los_implementos_abajo_con_el_sensor_danado(self):
        self.assertEqual(self.corre("A6")["obtenido"]["nivel"], "warning")

    def test_a5_decir_motor_apagado_sin_bajar_los_implementos_deja_el_paso_1_en_conflicto(self):
        self.assertEqual(self.corre("A5")["obtenido"]["paso_actual"], "p1")

    def test_b1_apagar_el_motor_con_los_implementos_arriba_no_avanza_y_avisa_el_orden(self):
        self.assertIn("ORDEN INVERTIDO", self.avisos(self.corre("B1")))

    def test_b2_apagar_el_motor_y_bajar_los_implementos_despues_queda_en_la_bitacora(self):
        self.assertIn("antes de «Bajar los implementos al suelo»", self.avisos(self.corre("B2")))

    def test_b3_una_persona_bajo_los_implementos_levantados_interrumpe(self):
        self.assertIn("PERSONA BAJO LOS IMPLEMENTOS LEVANTADOS", self.avisos(self.corre("B3")))

    def test_c1_levantar_los_implementos_durante_la_reparacion_avisa_que_el_control_se_perdio(self):
        self.assertIn("CONTROL PERDIDO", self.avisos(self.corre("C1")))

    def test_c2_levantar_los_implementos_con_una_persona_en_la_zona_interrumpe(self):
        self.assertIn("PERSONA BAJO LOS IMPLEMENTOS LEVANTADOS", self.avisos(self.corre("C2")))

    def test_d1_el_sensor_de_implementos_que_repite_da_un_solo_veredicto(self):
        self.assertEqual(self.corre("D1")["obtenido"]["verificados_por_paso"], {"p1": 1})

    def test_d3_si_el_motor_deja_de_reportar_la_ot_baja_a_warning(self):
        self.assertIn("sin lecturas de motor", " ".join(self.corre("D3")["obtenido"]["avisos"]))

    def test_f1_la_camara_confirma_la_manguera_con_confianza_alta(self):
        self.assertEqual(self.corre("F1")["obtenido"]["nivel"], "ok")

    def test_f2_con_confianza_baja_la_manguera_se_verifica_pero_pide_que_alguien_mire(self):
        r = self.corre("F2")
        self.assertEqual((r["obtenido"]["nivel"], r["obtenido"]["interrupciones"]), ("warning", 0))

    def test_f3_si_la_camara_dice_que_no_la_manguera_queda_en_conflicto_sin_interrumpir(self):
        self.assertEqual(self.corre("F3")["obtenido"]["interrupciones"], 0)

    def test_f4_sin_video_la_manguera_no_se_verifica_aunque_el_juez_diga_que_si(self):
        r = self.corre("F4")
        self.assertIn("sin video reciente", " ".join(e["detalle"] for e in r["bitacora"]))

    def test_f5_si_la_camara_aprueba_la_manguera_pero_hay_peligro_manda_el_sensor(self):
        self.assertEqual(self.corre("F5")["obtenido"]["nivel"], "error")

    def test_g1_un_pico_de_temperatura_del_aceite_avisa_una_vez_y_se_resuelve(self):
        r = self.corre("G1")
        self.assertEqual(r["obtenido"]["nivel_maximo"], "warning")

    def test_g2_un_escalon_de_temperatura_del_aceite_que_se_sostiene_mantiene_el_aviso(self):
        self.assertEqual(self.corre("G2")["obtenido"]["alertas_abiertas"], 1)

    def test_g3_una_deriva_de_temperatura_del_aceite_se_detecta(self):
        self.assertGreaterEqual(self.corre("G3")["obtenido"]["anomalias"], 1)

    def test_g4_el_ruido_normal_de_temperatura_del_aceite_no_da_falsas_alarmas(self):
        self.assertEqual(self.corre("G4")["obtenido"]["anomalias"], 0)

    def test_g5_un_sensor_de_temperatura_del_aceite_pegado_avisa_como_falla_del_sensor(self):
        r = self.corre("G5")
        self.assertIn("pegado", self.avisos(r))

    def test_arrancar_el_motor_en_la_prueba_final_no_es_un_control_perdido(self):
        self.assertNotIn("CONTROL PERDIDO", self.avisos(self.corre("A0")))

    def test_volver_a_dar_presion_antes_de_cambiar_la_manguera_avisa_que_el_control_se_perdio(self):
        e = replace(buscar("CON-A0"),
                    pasos=[{"lee": [["implementos", "en_suelo"], ["motor", "apagado"], ["palanca_seguridad", "bloqueada"],
                                    ["presion_hidraulica", "aliviada"], ["presion_hidraulica", "con_presion"]]}],
                    espera={"controles_deshechos": 1, "nivel": "error"})
        self.assertIn("«Aliviar la presión hidráulica» se deshizo", self.avisos(self.corre("A0", e)))


if __name__ == "__main__":
    unittest.main()
