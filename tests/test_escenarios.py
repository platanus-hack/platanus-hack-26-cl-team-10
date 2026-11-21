"""Escenarios por industria: cada patrón de ejecución, en cada industria, contra su barrera.

Correr:  python3 -m unittest tests.test_escenarios
Un escenario sin brecha tiene que cumplir lo esperado. Uno con brecha tiene que seguir
sin cumplirlo: si alguien la cierra, este test avisa que hay que quitar la marca y
contarlo en el PRD. Ver knowledge/projects/escenarios-por-industria/PRD.md.
"""

import unittest

from app import db
from app.escenarios import INDUSTRIAS, PATRONES, buscar, catalogo, correr


class CadaEscenarioHaceLoQueDice(unittest.TestCase):
    def test_los_que_no_tienen_brecha_cumplen_y_los_que_tienen_siguen_abiertos(self):
        for e in catalogo():
            with self.subTest(e.id):
                r = correr(e)
                self.assertIsNone(r["error"])
                fallas = {k: c for k, c in r["comparacion"].items() if not c["cumple"]}
                if e.brecha:
                    self.assertTrue(fallas, f"{e.id} ya cumple: la brecha se cerró, quita la marca")
                else:
                    self.assertEqual(fallas, {})


class LaMatrizEstaCompleta(unittest.TestCase):
    def test_cada_industria_tiene_cada_patron(self):
        ids = {e.id for e in catalogo()}
        faltan = [f"{i.codigo}-{p.codigo}" for i in INDUSTRIAS for p in PATRONES if f"{i.codigo}-{p.codigo}" not in ids]
        self.assertEqual(faltan, [])

    def test_cada_escenario_dice_de_donde_sale_lo_que_espera(self):
        self.assertEqual([e.id for e in catalogo() if not e.fuente], [])

    def test_las_pautas_de_las_tres_industrias_cumplen_el_contrato(self):
        from app import protocolos

        for i in INDUSTRIAS:
            pauta = protocolos.desde_json(i.pauta)
            self.assertIn(i.paso_camara, [p.id for p in pauta.pasos])
            self.assertEqual(pauta.paso("p1").sensor.id, i.p1.sensor)


class LaCajaEstaAislada(unittest.TestCase):
    def test_correr_un_escenario_no_toca_la_base_del_servidor(self):
        antes = db.RUTA.stat().st_mtime if db.RUTA.exists() else None
        correr(buscar("MIN-B3"))
        self.assertEqual(db.RUTA.stat().st_mtime if db.RUTA.exists() else None, antes)


class LoQueLaMatrizEncontro(unittest.TestCase):
    """Los comportamientos que motivaron la matriz, escritos como casos de uso."""

    def test_una_declaracion_tardia_hoy_interrumpe_con_un_conflicto_en_el_paso_siguiente(self):
        r = correr(buscar("MIN-A2"))
        self.assertEqual(r["obtenido"]["estados"]["p2"], "en_conflicto")
        self.assertEqual(r["obtenido"]["interrupciones"], 1)

    def test_saltarse_el_bloqueo_y_hacerlo_despues_hoy_deja_la_bitacora_limpia(self):
        r = correr(buscar("MIN-B2"))
        self.assertEqual((r["obtenido"]["alertas_capa1"], r["obtenido"]["nivel"]), (0, "ok"))

    def test_en_mineria_la_regla_de_seguridad_gana_aunque_la_camara_diga_que_si(self):
        r = correr(buscar("MIN-F5"))
        self.assertEqual(r["obtenido"]["estados"]["p3"], "verificado")
        self.assertEqual(r["obtenido"]["nivel"], "error")

    def test_la_camara_nunca_interrumpe(self):
        for i in INDUSTRIAS:
            for codigo in ("F1", "F2", "F3"):
                with self.subTest(f"{i.codigo}-{codigo}"):
                    self.assertEqual(correr(buscar(f"{i.codigo}-{codigo}"))["obtenido"]["interrupciones"], 0)


if __name__ == "__main__":
    unittest.main()
