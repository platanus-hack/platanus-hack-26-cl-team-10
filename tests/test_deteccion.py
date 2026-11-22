"""Capa 2 de cámara: el modelo del edge cierra pasos cuando está seguro; si no, decide el juez.

Correr:  python3 -m unittest discover tests
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from app import db
from app.contratos import Capa, Estado, Paso, TipoEvento
from app.protocolos import PAUTA_DEMO, desde_json
from app.reglas import por_deteccion
from app.servicios import DETECCIONES_MIN, Servicios
from app.video import Video

LOTO = desde_json(PAUTA_DEMO.parent / "pauta-loto.json")
BLOQUEO = LOTO.paso("l2")       # mouse presente
SIN_LAPIZ = LOTO.paso("l5")     # pencil ausente


CLASES = ["mouse", "pencil"]


def det(*objetos, clases=CLASES):
    return {"modelo": "yolo", "clases": clases,
            "objetos": [{"clase": c, "conf": p, "caja": [0, 0, 1, 1]} for c, p in objetos]}


class Contrato(unittest.TestCase):
    def test_la_pauta_loto_trae_su_deteccion(self):
        self.assertEqual(BLOQUEO.deteccion.clase, "mouse")
        self.assertFalse(SIN_LAPIZ.deteccion.presente)

    def test_deteccion_solo_en_pasos_de_camara(self):
        with self.assertRaises(ValueError):
            Paso.desde_dict({"id": "x", "orden": 1, "titulo": "t", "instruccion": "i", "tipo_evidencia": "sensor",
                             "capa_minima": 1, "sensor": {"id": "s", "espera": "v"},
                             "deteccion": {"clase": "mouse"}})

    def test_la_deteccion_sobrevive_a_la_base(self):
        cx = db.conectar(":memory:")
        db.guardar_pauta(cx, LOTO)
        self.assertEqual(db.leer_pauta(cx, LOTO.id).paso("l2").deteccion, BLOQUEO.deteccion)


class Capa2Camara(unittest.TestCase):
    def test_seguro_en_todos_los_cuadros_verifica_en_capa_2(self):
        v = por_deteccion(BLOQUEO, [det(("mouse", 0.95))] * 5)
        self.assertIs(v.estado, Estado.VERIFICADO)
        self.assertEqual(v.capa, Capa.APRENDIZAJE)
        self.assertEqual(v.evidencia["confianza"], 0.95)

    def test_un_cuadro_dudoso_basta_para_no_decidir(self):
        self.assertIsNone(por_deteccion(BLOQUEO, [det(("mouse", 0.95))] * 4 + [det(("mouse", 0.6))]))

    def test_retirado_es_que_ningun_cuadro_lo_ve(self):
        self.assertIs(por_deteccion(SIN_LAPIZ, [det(("mouse", 0.9))] * 5).estado, Estado.VERIFICADO)
        self.assertIsNone(por_deteccion(SIN_LAPIZ, [det()] * 4 + [det(("pencil", 0.4))]))

    def test_un_detector_que_no_busca_la_clase_no_puede_decir_que_no_esta(self):
        # con pautas de cualquier proceso, el detector puede no conocer el objeto: no verlo no dice nada
        self.assertIsNone(por_deteccion(SIN_LAPIZ, [det(("mouse", 0.9), clases=["mouse"])] * 5))
        self.assertIsNone(por_deteccion(SIN_LAPIZ, [det()] * 4 + [det(clases=None)]))

    def test_sin_detecciones_o_sin_campo_no_decide(self):
        self.assertIsNone(por_deteccion(BLOQUEO, []))
        correa = desde_json()
        self.assertIsNone(por_deteccion(correa.paso("p3"), [det(("mouse", 0.99))] * 5))


class CierreEnVivo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cx = db.conectar(":memory:")
        db.guardar_pauta(self.cx, LOTO)
        db.abrir_ot(self.cx, "ot-1", LOTO, "supervisor:X")
        self.juez_llamado = []
        self.s = Servicios(self.cx, video=Video(Path(self.tmp.name)),
                           juez=lambda p, c: self.juez_llamado.append(p) or (True, 0.9))
        self.s.iniciar_sesion("ot-1", "edge-1", "operario:A")
        self.s.recibir_lectura("edge-1", "operario", "presente")  # cierra l1 (sensor)
        self.s.video.recibir("edge-1", b"\xff\xd8cuadro\xff\xd9")

    def tearDown(self):
        self.tmp.cleanup()

    def veredictos(self, paso_id):
        return [e for e in db.eventos(self.cx, "ot-1") if e.tipo is TipoEvento.VEREDICTO and e.paso_id == paso_id]

    def mandar(self, n, *objetos):
        for _ in range(n):
            self.s._ultimo_juicio.clear()  # en la prueba no se espera el medio segundo entre juicios
            self.s.recibir_detecciones("edge-1", {"clases": CLASES,
                                                  "objetos": [{"clase": c, "conf": p, "caja": [0, 0, 1, 1]}
                                                              for c, p in objetos]})

    def test_el_bloqueo_se_cierra_solo_cuando_el_modelo_esta_seguro(self):
        self.mandar(DETECCIONES_MIN - 1, ("mouse", 0.95))
        self.assertEqual(self.veredictos("l2"), [])  # todavía pocas detecciones
        self.mandar(1, ("mouse", 0.95))
        v = self.veredictos("l2")
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].capa, Capa.APRENDIZAJE)
        self.assertTrue(v[0].evidencia["cuadro"])  # el cuadro quedó como evidencia
        self.assertEqual(self.juez_llamado, [])  # el VLM no se usó

    def test_si_el_modelo_duda_y_el_operario_declara_decide_el_juez(self):
        self.mandar(DETECCIONES_MIN + 2, ("mouse", 0.5))
        self.assertEqual(self.veredictos("l2"), [])
        r = self.s.declarar("ot-1", "operario:A", "bloqueo puesto")
        self.assertEqual(r["capa"], Capa.MODELO)
        self.assertEqual(len(self.juez_llamado), 1)

    def test_si_no_se_puede_guardar_la_foto_el_paso_igual_se_cierra(self):
        # en la VM, datos/evidencias quedó como enlace roto y el mkdir tiraba FileExistsError
        def falla(*_):
            raise FileExistsError("datos/evidencias")
        self.s.video.guardar_evidencia = falla
        self.mandar(DETECCIONES_MIN, ("mouse", 0.95))
        v = self.veredictos("l2")
        self.assertEqual(len(v), 1)
        self.assertIsNone(v[0].evidencia["cuadro"])

    def test_solo_el_paso_actual(self):
        self.mandar(DETECCIONES_MIN, ("pencil", 0.95))  # l4 es de lápiz, pero el actual es l2
        self.assertEqual(self.veredictos("l4"), [])

    def test_el_edge_sabe_que_clases_pide_la_ot_que_ejecuta(self):
        self.assertEqual(self.s.clases_de_edge("edge-1"), {"ot": "ot-1", "clases": ["mouse", "pencil"]})
        self.assertEqual(self.s.clases_de_edge("edge-libre"), {"ot": None, "clases": []})

    def test_las_clases_del_detector_llegan_con_la_deteccion(self):
        self.mandar(1, ("mouse", 0.95))
        self.assertEqual(self.s.video.ultimas_detecciones("edge-1")["clases"], CLASES)


class ElModeloDelServidor(unittest.TestCase):
    def test_se_exporta_con_las_clases_que_piden_las_pautas(self):
        ruta = PAUTA_DEMO.parents[1] / "edge" / "exportar_onnx.py"
        spec = importlib.util.spec_from_file_location("exportar_onnx", ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)  # no importa ultralytics hasta exportar
        self.assertEqual(modulo.clases_de(sorted(PAUTA_DEMO.parent.glob("pauta-*.json"))), ["mouse", "pencil", "red soda can", "soda can"])

    def test_la_escena_de_entrenamiento_etiqueta_lo_que_quedo_a_la_vista(self):
        import numpy as np

        spec = importlib.util.spec_from_file_location("entrenar", PAUTA_DEMO.parents[1] / "edge" / "entrenar.py")
        entrenar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entrenar)  # no importa ultralytics hasta entrenar
        recorte, mascara = np.full((40, 20, 3), 255, np.uint8), np.full((40, 20), 255, np.uint8)
        # de pie y entero: 100 px de alto y 50 de ancho en el centro de un cuadro de 400 x 200
        fondo = np.zeros((200, 400, 3), np.uint8)
        caja = entrenar.pegar(fondo, recorte, mascara, 100, 0, 200, 100)
        for v, esperado in zip(caja, (0.5, 0.5, 50 / 400, 100 / 200)):
            self.assertAlmostEqual(v, esperado, delta=0.01)
        self.assertEqual(fondo[100, 200].tolist(), [255, 255, 255])
        # acostado y a medias fuera del borde izquierdo: la caja es solo la mitad que se ve
        cx, _, ancho, alto = entrenar.pegar(np.zeros((200, 400, 3), np.uint8), recorte, mascara, 100, 90, 0, 100)
        self.assertAlmostEqual(cx - ancho / 2, 0, delta=0.01)
        self.assertAlmostEqual(ancho, 50 / 400, delta=0.01)
        self.assertAlmostEqual(alto, 50 / 200, delta=0.02)
        self.assertIsNone(entrenar.pegar(fondo, recorte, mascara, 100, 0, -500, 100))
        self.assertAlmostEqual(entrenar.iou((0.5, 0.5, 0.2, 0.2), (0.6, 0.5, 0.2, 0.2)), 1 / 3)


if __name__ == "__main__":
    unittest.main()
