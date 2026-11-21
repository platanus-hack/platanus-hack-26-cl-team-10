"""Las herramientas de las barreras 2 y 3: la simulación de detectores y el eval del juez de cámara.

Correr:  python3 -m unittest tests.test_barreras
"""

import importlib.util
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "scripts" / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


class LaSimulacionDeCapa2ComparaDetectores(unittest.TestCase):
    def setUp(self):
        self.sim = cargar("simular_capa2")

    def test_informa_cada_detector_en_cada_industria(self):
        texto, resumen = self.sim.tabla(semillas=2)
        for s in self.sim.SENALES:
            for d in self.sim.detectores(s):
                self.assertIn((s.industria, d.nombre), resumen)
        self.assertIn("Falsas alarmas", texto)

    def test_la_historia_que_aprende_de_la_falla_suelta_un_escalon_y_la_de_hoy_no(self):
        _, r = self.sim.tabla(semillas=4)
        self.assertLess(r[("Minería", self.sim.MADAntes.nombre)]["cubre"], 0.6)
        self.assertGreater(r[("Minería", self.sim.MADActual.nombre)]["cubre"], 0.9)

    def test_con_un_ciclo_de_trabajo_el_detector_de_hoy_no_alcanza_y_el_cusum_contra_el_ciclo_si(self):
        _, r = self.sim.tabla(semillas=4)
        for industria in ("Eléctrica", "Construcción"):
            with self.subTest(industria):
                self.assertLess(r[(industria, self.sim.MADActual.nombre)]["cubre"], 0.5)
                self.assertGreater(r[(industria, self.sim.CUSUMSinCiclo.nombre)]["cubre"], 0.9)

    def test_la_linea_base_cubre_dos_ciclos_de_trabajo(self):
        for s in self.sim.SENALES:
            if s.ciclo_amplitud:
                self.assertGreaterEqual(s.calibracion, 2 * s.ciclo_periodo)


class ElEvalDeCapa3MideLoQueImporta(unittest.TestCase):
    def setUp(self):
        import json

        self.ev = cargar("evaluar_capa3")
        self.casos = [json.loads(x) for x in self.ev.CASOS.read_text(encoding="utf-8").splitlines() if x.strip()]

    def test_hay_escenas_buenas_y_malas_en_las_tres_industrias(self):
        for industria in ("MIN", "ELE", "CON"):
            esperadas = {c["respuesta_esperada"] for c in self.casos if c["industria"] == industria}
            self.assertEqual(esperadas, {True, False})

    def test_un_juez_que_dice_que_si_a_todo_acepta_todos_los_errores(self):
        r = self.ev.evaluar(lambda pregunta, cuadro: (True, 0.55), self.casos)
        informe = self.ev.informe(r, "siempre-si")
        negativos = sum(1 for c in self.casos if not c["respuesta_esperada"])
        self.assertIn(f"| Falsa aceptación (sí a un paso mal hecho) | {negativos}/{negativos} (100 %) |", informe)

    def test_sin_imagenes_lo_dice_en_vez_de_aparentar(self):
        r = self.ev.evaluar(lambda pregunta, cuadro: (cuadro is not None, 0.9), self.casos)
        if not any(x["con_imagen"] for x in r):
            self.assertIn("Ningún caso tiene imagen todavía", self.ev.informe(r, "honesto"))


if __name__ == "__main__":
    unittest.main()
