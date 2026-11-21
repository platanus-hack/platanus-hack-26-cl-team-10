"""Las tres reglas que más cambian el código, de LOGICA.md, como pruebas.

Correr:  python3 -m unittest discover tests
Sin dependencias: la lógica no sabe de HTTP ni de hardware, por eso se puede.
"""

import unittest

from app.contratos import Estado, Evento, TipoEvento
from app.protocolos import desde_json
from app.reglas import (
    estados_desde_eventos,
    evaluar,
    paso_actual,
    propuesta_de_mejora,
    reglas_seguridad,
)

PAUTA = desde_json()
P1 = PAUTA.paso("p1")  # bloqueo: sensor, control crítico
P3 = PAUTA.paso("p3")  # rodillo: cámara
P6 = PAUTA.paso("p6")  # prueba: confirmación


class Regla1_UnPasoDeSensorNuncaSeCierraHablando(unittest.TestCase):
    def test_declarar_sin_sensor_no_cierra(self):
        v = evaluar(P1, "bloqueo puesto", {"reed_bloqueo": "abierto"})
        self.assertIs(v.estado, Estado.EN_CONFLICTO)
        self.assertEqual(v.capa, 1)

    def test_el_sensor_si_cierra(self):
        v = evaluar(P1, None, {"reed_bloqueo": "cerrado"})
        self.assertIs(v.estado, Estado.VERIFICADO)

    def test_la_confirmacion_si_se_cierra_hablando(self):
        v = evaluar(P6, "la correa paró en dos segundos", {})
        self.assertIs(v.estado, Estado.VERIFICADO)
        self.assertIsNone(v.capa)  # y queda constancia de que fue una persona


class Regla2_ElTercerEstadoExiste(unittest.TestCase):
    def test_conflicto_no_es_no_verificado(self):
        con_declaracion = evaluar(P1, "listo", {"reed_bloqueo": "abierto"})
        sin_declaracion = evaluar(P1, None, {"reed_bloqueo": "abierto"})
        self.assertIs(con_declaracion.estado, Estado.EN_CONFLICTO)
        self.assertIs(sin_declaracion.estado, Estado.NO_VERIFICADO)

    def test_el_paso_en_conflicto_sigue_siendo_el_actual(self):
        estados = {"p1": Estado.EN_CONFLICTO}
        self.assertEqual(paso_actual(PAUTA, estados).id, "p1")

    def test_el_conflicto_se_hereda_en_la_proyeccion(self):
        evs = [
            Evento(ot_id="ot-1", tipo=TipoEvento.VEREDICTO, ts="t1", actor="sistema",
                   paso_id="p1", estado=Estado.EN_CONFLICTO, detalle="x"),
        ]
        self.assertIs(estados_desde_eventos(evs)["p1"], Estado.EN_CONFLICTO)


class Regla3_SoloLaCapa1Interrumpe(unittest.TestCase):
    def test_el_conflicto_de_sensor_interrumpe(self):
        v = evaluar(P1, "bloqueo puesto", {"reed_bloqueo": "abierto"})
        self.assertTrue(v.interrumpe)

    def test_el_conflicto_de_camara_no_interrumpe(self):
        v = evaluar(P3, "rodillo instalado", {}, juez_camara=lambda _: (False, 0.9))
        self.assertIs(v.estado, Estado.EN_CONFLICTO)
        self.assertFalse(v.interrumpe)  # se muestra, no suena

    def test_guarda_abierta_con_energia_viva(self):
        alertas = reglas_seguridad({"guarda": "abierta", "energia": "viva"})
        self.assertEqual(len(alertas), 1)
        self.assertTrue(alertas[0].interrumpe)
        self.assertEqual(alertas[0].capa, 1)

    def test_guarda_abierta_con_energia_cortada_no_alerta(self):
        self.assertEqual(reglas_seguridad({"guarda": "abierta", "energia": "cortada"}), [])


class PropuestaDeMejora(unittest.TestCase):
    def _conflicto(self, ot, paso):
        return Evento(ot_id=ot, tipo=TipoEvento.VEREDICTO, ts="t", actor="sistema",
                      paso_id=paso, estado=Estado.EN_CONFLICTO, detalle="x")

    def test_una_desviacion_suelta_no_es_propuesta(self):
        self.assertEqual(propuesta_de_mejora([self._conflicto("ot-1", "p2")]), [])

    def test_la_misma_desviacion_en_dos_ots_si(self):
        props = propuesta_de_mejora([self._conflicto("ot-1", "p2"), self._conflicto("ot-2", "p2")])
        self.assertEqual(len(props), 1)
        self.assertEqual(props[0]["paso_id"], "p2")

    def _veredicto(self, ot, paso, minuto, estado=Estado.VERIFICADO, evidencia=None):
        return Evento(ot_id=ot, tipo=TipoEvento.VEREDICTO, ts=f"2026-11-21T10:{minuto:02d}:00+00:00",
                      actor="sistema", paso_id=paso, estado=estado, evidencia=evidencia, detalle="x")

    def test_el_paso_que_se_lleva_mas_de_la_mitad_del_tiempo_es_propuesta_con_sus_numeros(self):
        evs = []
        for ot in ("ot-1", "ot-2"):
            evs += [self._veredicto(ot, "p1", 0), self._veredicto(ot, "p2", 2),
                    self._veredicto(ot, "p3", 5, Estado.NO_VERIFICADO),  # un intento fallido no cierra
                    self._veredicto(ot, "p3", 22), self._veredicto(ot, "p4", 24)]
        props = propuesta_de_mejora(evs)
        self.assertEqual([p["paso_id"] for p in props], ["p3"])
        self.assertEqual(props[0]["segundos"], 20 * 60)  # desde el cierre de p2, no desde el intento fallido
        self.assertEqual(props[0]["parte_del_tiempo"], 0.83)
        self.assertEqual(props[0]["reintentos"], 1.0)
        self.assertEqual(props[0]["veces"], 0)

    def test_una_sola_ot_lenta_no_es_propuesta(self):
        evs = [self._veredicto("ot-1", "p1", 0), self._veredicto("ot-1", "p2", 2),
               self._veredicto("ot-1", "p3", 40), self._veredicto("ot-1", "p4", 42)]
        self.assertEqual(propuesta_de_mejora(evs), [])

    def test_el_paso_que_cierra_una_persona_en_dos_ots_apunta_al_sensor(self):
        persona = {"tipo": "persona", "motivo": "x"}
        props = propuesta_de_mejora([self._veredicto(ot, "p1", 0, evidencia=persona) for ot in ("ot-1", "ot-2")])
        self.assertEqual(props[0]["por_persona"], 2)
        self.assertIn("sensor", props[0]["nota"])
        self.assertIsNone(props[0]["segundos"])  # el primer paso de una OT no tiene desde dónde medirse


if __name__ == "__main__":
    unittest.main()
