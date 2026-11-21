"""Eléctrica: cada patrón de ejecución contra la barrera que lo decide. Casos de uso.

Correr:  python3 -m unittest tests.test_electrica
Mantenimiento de interruptor en celda de media tensión, pauta datos/pauta-celda-mt.json. Cada test corre su escenario de app/escenarios.py en la caja aislada
y comprueba lo esperado (con su fuente en el escenario) más lo que importa en el oficio.
Ver knowledge/projects/escenarios-por-industria/PRD.md.
"""

import unittest
from dataclasses import replace

from app.escenarios import buscar, correr


class InterruptorEnCeldaDeMediaTension(unittest.TestCase):
    def corre(self, patron, escenario=None):
        r = correr(escenario or buscar(f"ELE-{patron}"))
        self.assertIsNone(r["error"])
        fallas = {k: (c["esperado"], c["obtenido"]) for k, c in r["comparacion"].items() if not c["cumple"]}
        self.assertEqual(fallas, {}, r["entonces"])
        return r

    def avisos(self, r):
        return " · ".join(e["detalle"] for e in r["bitacora"] if e["tipo"] == "alerta")

    def test_a0_el_mantenimiento_bien_hecho_de_la_celda_no_da_ninguna_falsa_alarma(self):
        self.assertIsNone(self.corre("A0")["obtenido"]["paso_actual"])

    def test_a1_abrir_el_seccionador_verifica_el_corte_sin_que_el_operario_hable(self):
        self.assertEqual(self.corre("A1")["obtenido"]["estados"]["p1"], "verificado")

    def test_a2_decir_seccionador_abierto_despues_del_sensor_no_abre_conflicto_en_el_bloqueo(self):
        self.assertEqual(self.corre("A2")["obtenido"]["estados"]["p2"], "no_verificado")

    def test_a3_decir_seccionador_abierto_antes_del_sensor_interrumpe_y_despues_se_verifica(self):
        self.assertEqual(self.corre("A3")["obtenido"]["estados"]["p1"], "verificado")

    def test_a4_decir_seccionador_abierto_con_el_seccionador_cerrado_queda_en_conflicto(self):
        self.assertEqual(self.corre("A4")["obtenido"]["estados"]["p1"], "en_conflicto")

    def test_a5_decir_mando_bloqueado_sin_abrir_el_seccionador_deja_el_corte_en_conflicto(self):
        self.assertEqual(self.corre("A5")["obtenido"]["paso_actual"], "p1")

    def test_b1_bloquear_el_mando_sin_abrir_el_seccionador_no_avanza_y_avisa_el_orden(self):
        self.assertIn("ORDEN INVERTIDO", self.avisos(self.corre("B1")))

    def test_b2_bloquear_el_mando_y_abrir_el_seccionador_despues_queda_en_la_bitacora(self):
        self.assertIn("antes de «Abrir el interruptor y el seccionador»", self.avisos(self.corre("B2")))

    def test_b3_poner_a_tierra_con_tension_presente_interrumpe(self):
        self.assertIn("PUESTA A TIERRA CON TENSIÓN PRESENTE", self.avisos(self.corre("B3")))

    def test_c1_cerrar_el_seccionador_durante_el_trabajo_avisa_que_el_corte_se_perdio(self):
        self.assertIn("CONTROL PERDIDO", self.avisos(self.corre("C1")))

    def test_c2_cerrar_el_seccionador_con_tierras_y_tension_interrumpe(self):
        self.assertIn("CIERRE CON TIERRAS PUESTAS", self.avisos(self.corre("C2")))

    def test_d1_el_seccionador_que_repite_abierto_da_un_solo_veredicto(self):
        self.assertEqual(self.corre("D1")["obtenido"]["verificados_por_paso"], {"p1": 1})

    def test_d3_si_el_candado_deja_de_reportar_la_ot_baja_a_warning(self):
        self.assertIn("sin lecturas de candado_mando", " ".join(self.corre("D3")["obtenido"]["avisos"]))

    def test_f1_la_camara_confirma_la_senalizacion_con_confianza_alta(self):
        self.assertEqual(self.corre("F1")["obtenido"]["nivel"], "ok")

    def test_f2_con_confianza_baja_la_senalizacion_se_verifica_pero_pide_que_alguien_mire(self):
        r = self.corre("F2")
        self.assertEqual((r["obtenido"]["nivel"], r["obtenido"]["interrupciones"]), ("warning", 0))

    def test_f3_si_la_camara_dice_que_no_la_senalizacion_queda_en_conflicto_sin_interrumpir(self):
        self.assertEqual(self.corre("F3")["obtenido"]["interrupciones"], 0)

    def test_f4_sin_video_la_senalizacion_no_se_verifica_aunque_el_juez_diga_que_si(self):
        r = self.corre("F4")
        self.assertIn("sin video reciente", " ".join(e["detalle"] for e in r["bitacora"]))

    def test_f5_si_la_camara_aprueba_la_senalizacion_pero_hay_peligro_manda_el_sensor(self):
        self.assertEqual(self.corre("F5")["obtenido"]["nivel"], "error")

    def test_g1_un_pico_de_temperatura_avisa_una_vez_y_se_resuelve(self):
        r = self.corre("G1")
        self.assertEqual(r["obtenido"]["nivel_maximo"], "warning")

    def test_g2_un_escalon_de_temperatura_que_se_sostiene_mantiene_el_aviso(self):
        self.assertEqual(self.corre("G2")["obtenido"]["alertas_abiertas"], 1)

    def test_g3_una_deriva_de_temperatura_se_detecta(self):
        self.assertGreaterEqual(self.corre("G3")["obtenido"]["anomalias"], 1)

    def test_g4_el_ruido_normal_de_temperatura_no_da_falsas_alarmas(self):
        self.assertEqual(self.corre("G4")["obtenido"]["anomalias"], 0)

    def test_g5_un_sensor_de_temperatura_pegado_avisa_como_falla_del_sensor(self):
        r = self.corre("G5")
        self.assertIn("pegado", self.avisos(r))

    def test_poner_tierra_sin_haber_verificado_ausencia_de_tension_avisa_el_orden(self):
        e = replace(buscar("ELE-A0"),
                    pasos=[{"lee": [["seccionador", "abierto"], ["candado_mando", "cerrado"], ["tierra", "puesta"]]}],
                    espera={"desviaciones_de_orden": 1, "alertas_seguridad": {"min": 1}})
        r = self.corre("A0", e)
        self.assertIn("antes de «Verificar ausencia de tensión»", self.avisos(r))

    def test_reponer_el_servicio_con_las_tierras_puestas_interrumpe(self):
        e = replace(buscar("ELE-A0"),
                    pasos=[{"lee": [["seccionador", "abierto"], ["candado_mando", "cerrado"], ["tension", "ausente"],
                                    ["tierra", "puesta"], ["seccionador", "cerrado"]]}],
                    espera={"alertas_seguridad": 1, "controles_deshechos": 1, "nivel": "error"})
        self.assertIn("CIERRE CON TIERRAS PUESTAS", self.avisos(self.corre("A0", e)))


if __name__ == "__main__":
    unittest.main()
