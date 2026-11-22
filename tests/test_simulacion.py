"""La simulación de la mejora continua y las pruebas de recurrencia (app/simulacion.py, app/recurrencia.py).

Correr:  uv run python -m unittest tests.test_simulacion
El eval completo, con miles de repeticiones, es scripts/simular_mejora.py; acá van las versiones chicas de cada
afirmación, con semilla fija, para que un cambio que las rompa se note.
"""

import dataclasses
import unittest

from app import recurrencia
from app import simulacion as S
from app.protocolos import DATOS, desde_json

PAUTA = desde_json(DATOS / "pauta-polin-demo.json")


class LasPruebas(unittest.TestCase):
    def test_binomial_y_fisher_dan_lo_que_dan_a_mano(self):
        self.assertAlmostEqual(recurrencia.cola_binomial(2, 10, 0.05), 1 - 0.95**10 - 10 * 0.05 * 0.95**9)
        self.assertEqual(recurrencia.cola_binomial(0, 10, 0.3), 1.0)
        # 5 de 10 antes y 0 de 10 después: C(10,0)·C(10,5) / C(20,5) = 252 / 15504
        self.assertAlmostEqual(recurrencia.fisher_baja((10, 5), (10, 0)), 252 / 15504)

    def test_holm_rechaza_en_orden_y_se_detiene_en_el_primero_que_no_alcanza(self):
        self.assertEqual(recurrencia.holm({"a": 0.001, "b": 0.03, "c": 0.04}), {"a": True, "b": False, "c": False})
        self.assertEqual(recurrencia.holm({"a": 0.001, "b": 0.02, "c": 0.04}), {"a": True, "b": True, "c": True})

    def test_una_baja_con_pocas_ot_no_es_una_mejora(self):
        self.assertEqual(recurrencia.comprobar_cambio((3, 2), (1, 0))["resultado"], "sin_evidencia")
        self.assertEqual(recurrencia.comprobar_cambio((50, 15), (50, 3))["resultado"], "mejoro")
        self.assertEqual(recurrencia.comprobar_cambio((50, 15), (50, 15))["resultado"], "se_repite")
        self.assertEqual(recurrencia.comprobar_cambio((50, 15), (0, 0))["resultado"], "sin_datos")

    def test_sin_senales_en_el_resto_la_base_no_queda_en_cero(self):
        r = recurrencia.recurrentes({"p1": 1, "p2": 0, "p3": 0}, 5)
        self.assertFalse(r["p1"]["recurrente"])
        self.assertGreater(r["p1"]["tasa_del_resto"], 0)


class LaFidelidad(unittest.TestCase):
    def test_cada_conducta_deja_en_la_bitacora_real_la_senal_que_se_espera(self):
        for perfil, paso in (("olvido", "p2"), ("presion", "p6"), ("apuro", "p4"), ("equipo", "p2"), ("impracticable", "p7")):
            with self.subTest(perfil=perfil):
                f = S.fidelidad(S.Simulador(PAUTA).correr(12, [S.Patron(perfil, paso, 0.5)], ruido=0.05, semilla=3))
                self.assertGreater(f["esperadas"], 0)
                self.assertEqual((f["faltan"], f["sobran"]), ([], []))

    def test_saltarse_un_paso_que_la_evidencia_no_ve_se_rechaza_en_vez_de_contarse_como_no_detectado(self):
        self.assertIsNone(S.senal_esperada(PAUTA, "p3", "saltar"))
        with self.assertRaises(ValueError):
            S.Simulador(PAUTA).correr(1, [S.Patron("olvido", "p3", 0.5)])

    def test_sacar_el_candado_antes_de_alejarse_cae_como_control_perdido_en_el_candado(self):
        self.assertEqual(S.senal_esperada(PAUTA, "p6", "saltar"), ("p2", "control"))
        self.assertEqual(S.senal_esperada(PAUTA, "p2", "saltar"), ("p3", "orden"))

    def test_acercarse_con_el_motor_encendido_cae_como_seguridad_en_apagar_el_motor(self):
        estacion = desde_json(DATOS / "pauta-polin-estacion.json")
        self.assertEqual(S.senales_esperadas(estacion, "e1", "saltar"), [("e1", "seguridad")])
        f = S.fidelidad(S.Simulador(estacion).correr(12, [S.Patron("presion", "e1", 0.5)], ruido=0.05, semilla=8))
        self.assertGreater(f["esperadas"], 0)
        self.assertEqual((f["faltan"], f["sobran"]), ([], []))

    def test_la_misma_semilla_con_el_factor_en_cero_es_la_misma_ot_sin_esa_conducta(self):
        patrones = [S.Patron("olvido", "p2", 0.5)]
        v1 = S.Simulador(PAUTA).correr(20, patrones, ruido=0.1, semilla=5)
        v2 = S.Simulador(PAUTA).correr(20, patrones, ruido=0.1, semilla=5, factores={"olvido": 0})
        self.assertTrue(any(v["perfil"] == "olvido" for v in v1.verdad))
        self.assertFalse(any(v["perfil"] == "olvido" for v in v2.verdad))
        ruido = lambda c: {(v["ot"], v["paso"]) for v in c.verdad if v["perfil"] == "ruido" and v["paso"] not in ("p2", "p3")}
        self.assertEqual(ruido(v1), ruido(v2))


class ElCriterio(unittest.TestCase):
    def test_con_solo_ruido_la_regla_de_dos_ot_propone_casi_siempre_y_la_recurrencia_casi_nunca(self):
        r = S.montecarlo_criterio(8, 20, 0.05, repeticiones=300, semilla=1)
        self.assertGreater(r["minimo"]["falsa_propuesta"], 0.8)
        self.assertLess(r["recurrencia"]["falsa_propuesta"], 0.08)

    def test_con_50_ot_la_recurrencia_encuentra_un_paso_al_30_por_ciento(self):
        r = S.montecarlo_criterio(8, 50, 0.05, 0.3, repeticiones=200, semilla=2)
        self.assertGreater(r["recurrencia"]["detecta"], 0.9)

    def test_una_version_sin_efecto_no_mejora_aunque_baje_por_azar(self):
        r = S.montecarlo_validacion(20, 0.3, 1.0, repeticiones=400, semilla=3)
        self.assertGreater(r["ingenua"], 0.3)
        self.assertLess(r["fisher"], 0.08)


class ElAvisoEnVivo(unittest.TestCase):
    def test_a_la_tercera_ot_que_se_salta_apagar_el_motor_el_supervisor_recibe_la_recomendacion(self):
        estacion = desde_json(DATOS / "pauta-polin-estacion.json")
        sim = S.Simulador(estacion, cliente="oculta-sim")
        sim.correr(3, [S.Patron("presion", "e1", 1.0)], semilla=1)
        avisos = sim.corrida.avisos()
        self.assertEqual([(a["numero"], a["paso"]) for a in avisos], [(3, "e1")])
        p = next(p for p in sim.corrida.propuestas() if p["paso"] == "e1")
        self.assertEqual(p["detectada"]["ot"], sim.corrida.ots[2])
        ev = sim.cx.execute("SELECT detalle FROM eventos WHERE tipo = 'propuesta_pauta'").fetchone()
        self.assertIn("«Apagar el motor»", ev["detalle"])
        self.assertNotIn("operario:sim", ev["detalle"])  # cuenta OT y operarios distintos, nunca nombra a nadie

    def test_se_avisa_una_sola_vez_por_propuesta(self):
        estacion = desde_json(DATOS / "pauta-polin-estacion.json")
        sim = S.Simulador(estacion, cliente="oculta-sim")
        sim.correr(8, [S.Patron("presion", "e1", 1.0)], semilla=1)
        self.assertEqual(len(sim.corrida.avisos()), 1)

    def test_sin_empresa_no_hay_a_quien_avisar(self):
        sim = S.Simulador(desde_json(DATOS / "pauta-polin-estacion.json"))
        sim.correr(4, [S.Patron("presion", "e1", 1.0)], semilla=1)
        self.assertEqual(sim.corrida.avisos(), [])

    def test_con_alfa_del_aviso_el_ruido_casi_no_avisa_aunque_se_mire_despues_de_cada_ot(self):
        from app import mejora

        laxo = S.montecarlo_aviso(7, 50, 0.05, None, 0.05, repeticiones=200, semilla=1)
        estricto = S.montecarlo_aviso(7, 50, 0.05, None, mejora.ALFA_AVISO, repeticiones=200, semilla=1)
        self.assertGreater(laxo["falso_aviso"], 0.1)
        self.assertLess(estricto["falso_aviso"], 0.08)


class DePuntaAPunta(unittest.TestCase):
    def test_el_olvido_recurrente_se_marca_y_con_la_verificacion_de_therp_la_v2_mejora(self):
        sim = S.Simulador(PAUTA)
        patrones = [S.Patron("olvido", "p2", 0.4)]
        sim.correr(40, patrones, ruido=0.05, semilla=11)
        recurrentes = [p["paso"] for p in sim.corrida.propuestas() if p["recurrencia"]["recurrente"]]
        self.assertEqual(recurrentes, ["p3"])  # el olvido de p2 deja la alerta de orden en el paso que se adelantó
        sim.versionar(dataclasses.replace(PAUTA, version=2))
        sim.correr(40, patrones, ruido=0.05, semilla=12, factores={"olvido": S.PERFILES["olvido"].efecto_v2})
        p3 = next(p for p in sim.corrida.propuestas() if p["version"] == 1 and p["paso"] == "p3")
        self.assertEqual((p3["estado"], p3["validacion"]["resultado"]), ("superada", "mejoro"))

    def test_el_sensor_que_falla_manda_a_revisar_el_sensor(self):
        sim = S.Simulador(PAUTA)
        sim.correr(30, [S.Patron("equipo", "p2", 0.4)], semilla=4)
        p2 = next(p for p in sim.corrida.propuestas() if p["paso"] == "p2")
        self.assertTrue(p2["recurrencia"]["recurrente"])
        self.assertIn("revisar el sensor", p2["sugerencia"])


if __name__ == "__main__":
    unittest.main()
