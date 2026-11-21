"""La matriz de escenarios como un todo: completa, con fuentes, aislada y sin brechas olvidadas.

Correr:  python3 -m unittest tests.test_escenarios
Los casos de uso de cada industria están en test_mineria.py, test_electrica.py y
test_construccion.py. Acá: un escenario sin brecha tiene que cumplir lo esperado, y uno
con brecha tiene que seguir sin cumplirlo; si alguien la cierra, este test avisa que hay
que quitar la marca. Ver knowledge/projects/escenarios-por-industria/PRD.md.
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


class CadaIndustriaTieneSusCasosDeUso(unittest.TestCase):
    """Los tests por industria (test_mineria, test_electrica, test_construccion) cubren cada patrón."""

    def test_cada_archivo_de_industria_prueba_cada_patron(self):
        import re
        from pathlib import Path

        carpeta = Path(__file__).parent
        for archivo, industria in [("test_mineria.py", "MIN"), ("test_electrica.py", "ELE"), ("test_construccion.py", "CON")]:
            texto = (carpeta / archivo).read_text(encoding="utf-8")
            cubiertos = set(re.findall(r"def test_([a-g]\d)_", texto))
            with self.subTest(industria):
                self.assertEqual(sorted({p.codigo.lower() for p in PATRONES} - cubiertos), [])


if __name__ == "__main__":
    unittest.main()
