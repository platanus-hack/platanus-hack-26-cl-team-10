"""El CRUD con las reglas de negocio adentro. Casos de uso, sin HTTP.

Correr:  python3 -m unittest discover tests
"""

import json
import unittest

from app import catalogo, db
from app.catalogo import ReglaDeNegocio
from app.protocolos import PAUTA_DEMO


def pauta_demo(version=1, **cambios):
    d = json.loads(PAUTA_DEMO.read_text(encoding="utf-8"))
    d["version"] = version
    d.update(cambios)
    return d


class Base(unittest.TestCase):
    def setUp(self):
        self.cx = db.conectar(":memory:")
        catalogo.preparar(self.cx)


class PautaVersionada(Base):
    def test_una_pauta_nueva_nace_en_la_version_1_y_sin_aprobar(self):
        r = catalogo.crear_pauta(self.cx, pauta_demo())
        self.assertEqual(r["version"], 1)
        self.assertFalse(r["aprobada"])

    def test_cambiar_una_pauta_es_crear_la_version_siguiente(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        catalogo.crear_pauta(self.cx, pauta_demo(version=2, nombre="Cambio de rodillo, v2"))
        self.assertEqual([v["version"] for v in catalogo.versiones(self.cx, "pauta-correa-ct-01")], [1, 2])
        self.assertEqual(catalogo.leer_pauta(self.cx, "pauta-correa-ct-01")["version"], 2)
        self.assertEqual(catalogo.leer_pauta(self.cx, "pauta-correa-ct-01", 1)["version"], 1)

    def test_no_se_escribe_encima_de_una_version(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        with self.assertRaises(ReglaDeNegocio):
            catalogo.crear_pauta(self.cx, pauta_demo(version=1))

    def test_no_se_salta_versiones(self):
        with self.assertRaises(ReglaDeNegocio):
            catalogo.crear_pauta(self.cx, pauta_demo(version=3))

    def test_dos_pasos_con_el_mismo_orden_no_se_aceptan(self):
        d = pauta_demo()
        d["pasos"][1]["orden"] = d["pasos"][0]["orden"]
        with self.assertRaises(ReglaDeNegocio):
            catalogo.crear_pauta(self.cx, d)

    def test_un_paso_de_sensor_sin_sensor_no_se_acepta(self):
        d = pauta_demo()
        d["pasos"][0]["sensor"] = None
        with self.assertRaises(ValueError):
            catalogo.crear_pauta(self.cx, d)


class Aprobacion(Base):
    def setUp(self):
        super().setUp()
        catalogo.crear_pauta(self.cx, pauta_demo())

    def test_la_aprueba_una_persona(self):
        r = catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "supervisor:X")
        self.assertTrue(r["aprobada"])
        self.assertEqual(catalogo.versiones(self.cx, "pauta-correa-ct-01")[0]["aprobada_por"], "supervisor:X")

    def test_el_sistema_no_puede_aprobar(self):
        with self.assertRaises(ReglaDeNegocio):
            catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "sistema")

    def test_no_se_aprueba_dos_veces(self):
        catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "supervisor:X")
        with self.assertRaises(ReglaDeNegocio):
            catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "supervisor:Y")


class LaOTNaceDeUnaPautaAprobada(Base):
    def setUp(self):
        super().setUp()
        catalogo.crear_pauta(self.cx, pauta_demo())

    def test_sin_aprobar_no_hay_ot(self):
        with self.assertRaises(ReglaDeNegocio):
            catalogo.abrir_ot(self.cx, "ot-1", "pauta-correa-ct-01", "supervisor:X")

    def test_aprobada_si_y_guarda_la_version_que_ejecuta(self):
        catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "supervisor:X")
        catalogo.crear_pauta(self.cx, pauta_demo(version=2))
        r = catalogo.abrir_ot(self.cx, "ot-1", "pauta-correa-ct-01", "supervisor:X", version=1)
        self.assertEqual(r["version"], 1)
        self.assertEqual(catalogo.listar_ots(self.cx)[0]["paso_actual"], "p1")

    def test_la_ultima_version_sin_aprobar_no_se_ejecuta_aunque_la_anterior_si(self):
        catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "supervisor:X")
        catalogo.crear_pauta(self.cx, pauta_demo(version=2))
        with self.assertRaises(ReglaDeNegocio):
            catalogo.abrir_ot(self.cx, "ot-1", "pauta-correa-ct-01", "supervisor:X")

    def test_no_se_abre_dos_veces_la_misma_ot(self):
        catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "supervisor:X")
        catalogo.abrir_ot(self.cx, "ot-1", "pauta-correa-ct-01", "supervisor:X")
        with self.assertRaises(ReglaDeNegocio):
            catalogo.abrir_ot(self.cx, "ot-1", "pauta-correa-ct-01", "supervisor:X")


class EventosSoloSeLeen(Base):
    def test_un_evento_se_lee_por_su_id(self):
        catalogo.crear_pauta(self.cx, pauta_demo())
        catalogo.aprobar_pauta(self.cx, "pauta-correa-ct-01", 1, "supervisor:X")
        catalogo.abrir_ot(self.cx, "ot-1", "pauta-correa-ct-01", "supervisor:X")
        ev = catalogo.leer_evento(self.cx, 1)
        self.assertEqual(ev.ot_id, "ot-1")

    def test_ningun_archivo_de_la_app_edita_ni_borra_eventos(self):
        import re
        from pathlib import Path

        app = Path(catalogo.__file__).parent
        prohibido = re.compile(r"(UPDATE\s+eventos|DELETE\s+FROM\s+eventos)", re.IGNORECASE)
        culpables = [f.name for f in app.glob("*.py") if prohibido.search(f.read_text(encoding="utf-8"))]
        self.assertEqual(culpables, [])


if __name__ == "__main__":
    unittest.main()
