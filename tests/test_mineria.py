"""Minería: cada patrón de ejecución contra la barrera que lo decide. Casos de uso.

Correr:  python3 -m unittest tests.test_mineria
Cambio de rodillo en la correa CT-01, pauta datos/pauta-correa.json. Cada test corre su escenario de app/escenarios.py en la caja aislada
y comprueba lo esperado (con su fuente en el escenario) más lo que importa en el oficio.
Ver knowledge/projects/escenarios-por-industria/PRD.md.
"""

import unittest
from dataclasses import replace

from app.escenarios import buscar, correr


class CambioDeRodilloEnCorrea(unittest.TestCase):
    def corre(self, patron, escenario=None):
        r = correr(escenario or buscar(f"MIN-{patron}"))
        self.assertIsNone(r["error"])
        fallas = {k: (c["esperado"], c["obtenido"]) for k, c in r["comparacion"].items() if not c["cumple"]}
        self.assertEqual(fallas, {}, r["entonces"])
        return r

    def avisos(self, r):
        return " · ".join(e["detalle"] for e in r["bitacora"] if e["tipo"] == "alerta")

    def test_a0_el_cambio_de_rodillo_bien_hecho_no_da_ninguna_falsa_alarma(self):
        r = self.corre("A0")
        self.assertIsNone(r["obtenido"]["paso_actual"])

    def test_a1_el_candado_cerrado_verifica_el_bloqueo_sin_que_el_operario_hable(self):
        self.assertEqual(self.corre("A1")["obtenido"]["estados"]["p1"], "verificado")

    def test_a2_decir_bloqueo_puesto_despues_del_sensor_no_abre_conflicto_en_la_guarda(self):
        r = self.corre("A2")
        self.assertEqual(r["obtenido"]["estados"]["p2"], "no_verificado")

    def test_a3_decir_bloqueo_puesto_antes_del_sensor_interrumpe_y_despues_se_verifica(self):
        r = self.corre("A3")
        self.assertEqual((r["obtenido"]["conflictos"], r["obtenido"]["estados"]["p1"]), (1, "verificado"))

    def test_a4_decir_bloqueo_puesto_con_el_candado_abierto_deja_el_bloqueo_en_conflicto(self):
        self.assertEqual(self.corre("A4")["obtenido"]["estados"]["p1"], "en_conflicto")

    def test_a5_decir_guarda_retirada_sin_haber_bloqueado_deja_el_bloqueo_en_conflicto(self):
        self.assertEqual(self.corre("A5")["obtenido"]["paso_actual"], "p1")

    def test_b1_abrir_la_guarda_sin_bloquear_no_avanza_y_avisa_el_orden(self):
        self.assertIn("ORDEN INVERTIDO", self.avisos(self.corre("B1")))

    def test_b2_abrir_la_guarda_y_bloquear_despues_queda_en_la_bitacora(self):
        r = self.corre("B2")
        self.assertIn("antes de «Cortar la energía y bloquear con candado»", self.avisos(r))

    def test_b3_abrir_la_guarda_con_energia_viva_sin_bloquear_interrumpe(self):
        self.assertIn("GUARDA ABIERTA CON ENERGÍA VIVA", self.avisos(self.corre("B3")))

    def test_c1_sacar_el_candado_con_la_guarda_abierta_avisa_que_el_control_se_perdio(self):
        self.assertIn("CONTROL PERDIDO", self.avisos(self.corre("C1")))

    def test_c2_sacar_el_candado_y_energizar_con_la_guarda_abierta_interrumpe(self):
        self.assertIn("GUARDA ABIERTA CON ENERGÍA VIVA", self.avisos(self.corre("C2")))

    def test_d1_el_reed_que_repite_cerrado_da_un_solo_veredicto(self):
        self.assertEqual(self.corre("D1")["obtenido"]["verificados_por_paso"], {"p1": 1})

    def test_d3_si_la_guarda_deja_de_reportar_la_ot_baja_a_warning(self):
        self.assertIn("sin lecturas de guarda", " ".join(self.corre("D3")["obtenido"]["avisos"]))

    def test_f1_la_camara_confirma_el_rodillo_con_confianza_alta(self):
        self.assertEqual(self.corre("F1")["obtenido"]["nivel"], "ok")

    def test_f2_con_confianza_baja_el_rodillo_se_verifica_pero_pide_que_alguien_mire(self):
        r = self.corre("F2")
        self.assertEqual((r["obtenido"]["nivel"], r["obtenido"]["interrupciones"]), ("warning", 0))

    def test_f3_si_la_camara_dice_que_no_el_rodillo_queda_en_conflicto_sin_interrumpir(self):
        self.assertEqual(self.corre("F3")["obtenido"]["interrupciones"], 0)

    def test_f4_sin_video_el_rodillo_no_se_verifica_aunque_el_juez_diga_que_si(self):
        r = self.corre("F4")
        self.assertIn("sin video reciente", " ".join(e["detalle"] for e in r["bitacora"]))

    def test_f5_si_la_camara_aprueba_el_rodillo_pero_hay_peligro_manda_el_sensor(self):
        self.assertEqual(self.corre("F5")["obtenido"]["nivel"], "error")

    def test_g1_un_pico_de_vibracion_avisa_una_vez_y_se_resuelve(self):
        r = self.corre("G1")
        self.assertEqual(r["obtenido"]["nivel_maximo"], "warning")

    def test_g2_un_escalon_de_vibracion_que_se_sostiene_mantiene_el_aviso(self):
        self.assertEqual(self.corre("G2")["obtenido"]["alertas_abiertas"], 1)

    def test_g3_una_deriva_de_vibracion_se_detecta(self):
        self.assertGreaterEqual(self.corre("G3")["obtenido"]["anomalias"], 1)

    def test_g4_el_ruido_normal_de_vibracion_no_da_falsas_alarmas(self):
        self.assertEqual(self.corre("G4")["obtenido"]["anomalias"], 0)

    def test_g5_un_sensor_de_vibracion_pegado_avisa_como_falla_del_sensor(self):
        r = self.corre("G5")
        self.assertIn("pegado", self.avisos(r))

    def test_sacar_el_candado_en_su_paso_no_es_un_control_perdido(self):
        base = buscar("MIN-A0")
        r = self.corre("A0", base)
        self.assertNotIn("CONTROL PERDIDO", self.avisos(r))

    def test_cerrar_la_guarda_por_una_alerta_durante_el_cambio_no_es_orden_invertido(self):
        e = replace(buscar("MIN-F5"), espera={"desviaciones_de_orden": 0})
        pasos = [*e.pasos, {"lee": [["guarda", "cerrada"]]}]
        self.corre("F5", replace(e, pasos=pasos))


if __name__ == "__main__":
    unittest.main()
