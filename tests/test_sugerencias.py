"""Las mejoras sugeridas: el cambio que propone cada propuesta, en el reporte, y la versión siguiente que arma Factum.

Correr:  uv run --with httpx python -m unittest tests.test_sugerencias
"""

import copy
import os
import unittest
from unittest import mock
from urllib.parse import quote

from app import sugerencias
from tests import test_recorrido_interno as recorrido
from tests.test_recorrido_interno import CLAVE, PROTOCOLO, TIENE_HTTPX, V1, paso


@unittest.skipUnless(TIENE_HTTPX, "falta httpx o fastapi")
class LasMejorasSugeridas(recorrido.DelProtocoloALaMejoraContinua):
    test_del_protocolo_a_la_version_que_deja_de_desviarse = None

    def setUp(self):
        super().setUp()
        self.sin_key = mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""})
        self.sin_key.start()
        self.c.post("/interno/protocolos", json=PROTOCOLO, headers=CLAVE)
        self.c.post("/interno/protocolos/prot-prueba-01/pautas", json={"pauta": V1, "actor": "equipo:factum"}, headers=CLAVE)
        self.c.post("/pautas/pauta-prueba-01/versiones/1/aprobar", json={"actor": "equipo:pancho"}, headers=CLAVE)
        self.c.put("/interno/clientes/oculta/pautas/pauta-prueba-01", headers=CLAVE)

    def tearDown(self):
        self.sin_key.stop()
        super().tearDown()

    def borrador(self, m, quien=None):
        return self.c.get(f"/cliente/mejoras/{quote(m['id'], safe='')}/borrador", headers=quien or self.carla)

    def conformidad(self):
        return next(m for m in self.mejoras() if m["tipo"] == "conformidad")

    def desviacion(self, n=3):
        ots = [self.ot(acercarse_con_energia=True) for _ in range(n)]
        return ots, next(m for m in self.mejoras() if m["tipo"] == "desviacion" and m["paso"] == "p1")

    def test_la_falta_de_un_control_agrega_su_paso_donde_le_toca(self):
        b = self.borrador(self.conformidad())
        self.assertEqual(b.status_code, 200, b.text)
        b = b.json()
        self.assertEqual((b["aplicable"], b["desde_version"], b["version"], b["redactado_por"]), (True, 1, 2, "codigo"))
        [c] = b["cambios"]
        self.assertEqual((c["tipo"], c["paso"], c["antes"]), ("agrega", "p3", None))
        self.assertEqual(c["despues"]["titulo"], "Comprobar energía cero")
        self.assertEqual((c["despues"]["tipo_evidencia"], c["despues"]["cumple"]), ("confirmacion", ["prot-prueba-01:A3"]))
        self.assertTrue(b["comprobacion"]["valida"])
        self.assertEqual(b["comprobacion"]["conformidad_despues"]["hallazgos"], [])

    def test_dos_controles_en_un_paso_se_separan(self):
        juntos = copy.deepcopy(V1) | {"id": "pauta-prueba-02"}
        juntos["pasos"][0]["cumple"] = ["prot-prueba-01:A1", "prot-prueba-01:A2"]
        juntos["pasos"][1].pop("cumple")
        juntos["pasos"].insert(2, paso(3, "Probar que no arranca", critico=True, cumple=["A3"], tipo="confirmacion"))
        for i, p in enumerate(juntos["pasos"], 1):
            p["id"], p["orden"] = f"p{i}", i
        self.c.post("/interno/protocolos/prot-prueba-01/pautas", json={"pauta": juntos, "actor": "equipo:factum"}, headers=CLAVE)
        self.c.post("/pautas/pauta-prueba-02/versiones/1/aprobar", json={"actor": "equipo:pancho"}, headers=CLAVE)
        self.c.put("/interno/clientes/oculta/pautas/pauta-prueba-02", headers=CLAVE)
        [m] = [m for m in self.mejoras("pauta-prueba-02") if m["conformidad"]["tipo"] == "juntos"]
        b = self.borrador(m).json()
        [c] = b["cambios"]
        self.assertEqual((c["tipo"], c["paso"], c["despues"]["cumple"]), ("separa", "p2", ["prot-prueba-01:A2"]))
        self.assertTrue(b["comprobacion"]["valida"], b["comprobacion"])

    def test_una_desviacion_reescribe_el_paso_y_cita_sus_ot(self):
        ots, m = self.desviacion()
        self.assertEqual((m["ots"], m["aplicable"], m["por_que_no"]), (sorted(ots), True, None))
        b = self.borrador(m).json()
        [c] = b["cambios"]
        self.assertEqual((c["tipo"], c["paso"], c["antes"]["titulo"]), ("reescribe", "p1", "Cortar la energía"))
        self.assertIn("No sigas al paso siguiente hasta que energia marque cortada", c["despues"]["instruccion"])
        self.assertEqual(c["despues"]["tipo_evidencia"], "sensor")
        self.assertTrue(all(o in c["porque"] for o in ots))
        self.assertTrue(b["comprobacion"]["valida"])

    def test_el_modelo_solo_reescribe_texto_y_no_cita_ot_ajenas(self):
        _, m = self.desviacion()
        bueno = {"cambios": [{"indice": 0, "titulo": "Cortar la energía", "instruccion": "Corta la energía y espera que "
                              "el sensor marque cortada.", "porque": f"En {m['ots'][0]} se adelantó."}]}
        ajeno = {"cambios": [{**bueno["cambios"][0], "porque": "En ot-9999 se adelantó."}]}
        de_mas = {"cambios": [{**bueno["cambios"][0], "tipo_evidencia": "confirmacion"}]}
        with mock.patch.object(sugerencias.cerebro, "configurado", return_value=True):
            for respuesta, esperado in ((bueno, sugerencias.cerebro.MODELO_POR_DEFECTO), (ajeno, "codigo"), (de_mas, "codigo")):
                with mock.patch.object(sugerencias.cerebro, "_pedir", return_value=respuesta):
                    b = self.borrador(m).json()
                self.assertEqual(b["redactado_por"], esperado, respuesta)
                self.assertEqual(b["cambios"][0]["despues"]["tipo_evidencia"], "sensor")

    def test_el_reporte_trae_las_mejoras_en_que_aporto_la_ot(self):
        ots, m = self.desviacion()
        r = self.c.get(f"/cliente/ots/{ots[0]}/reporte", headers=self.carla).json()
        por_id = {x["propuesta"]: x for x in r["mejoras"]}
        self.assertIn(m["id"], por_id)
        self.assertIn(self.conformidad()["id"], por_id)
        self.assertEqual(por_id[self.conformidad()["id"]]["cambios_resumen"],
                         ["Agrega «Comprobar energía cero» después de «Poner tu candado»"])
        self.assertTrue(por_id[m["id"]]["cambios_resumen"][0].startswith("Reescribe «Cortar la energía»"))
        md = self.c.get(f"/cliente/ots/{ots[0]}/reporte?formato=markdown", headers=self.carla).text
        self.assertIn("## Mejoras sugeridas", md)
        self.assertIn("Nada de este reporte lo redactó un modelo.", md)
        self.assertEqual(self.c.get(f"/cliente/ots/{ots[0]}/reporte", headers=self.ana).json()["mejoras"], [])
        otra = self.ot(acercarse_con_energia=False)
        en_otra = {x["propuesta"] for x in self.c.get(f"/cliente/ots/{otra}/reporte", headers=self.carla).json()["mejoras"]}
        self.assertNotIn(m["id"], en_otra)

    def test_factum_arma_la_version_siguiente_con_las_aceptadas(self):
        _, desv = self.desviacion()
        conf = self.conformidad()
        r = self.c.post("/interno/pautas/pauta-prueba-01/version-siguiente", json={"actor": "equipo:factum"}, headers=CLAVE)
        self.assertEqual(r.status_code, 409, r.text)
        for m in (conf, desv):
            self.c.post(f"/cliente/mejoras/{quote(m['id'], safe='')}/revision", json={"decision": "aceptar", "nota": ""},
                        headers=self.carla)
        r = self.c.post("/interno/pautas/pauta-prueba-01/version-siguiente", json={"actor": "equipo:factum"}, headers=CLAVE)
        self.assertEqual(r.status_code, 201, r.text)
        v = r.json()
        self.assertEqual((v["version"], v["desde_version"]), (2, 1))
        self.assertEqual(set(v["propuestas"]), {conf["id"], desv["id"]})
        self.assertEqual(sorted(c["tipo"] for c in v["cambios"]), ["agrega", "reescribe"])
        self.assertEqual(self.c.post("/interno/pautas/pauta-prueba-01/version-siguiente", json={"actor": "equipo:factum"},
                                     headers=CLAVE).status_code, 409)
        self.assertEqual(self.c.post("/pautas/pauta-prueba-01/versiones/2/aprobar", json={"actor": "equipo:pancho"},
                                     headers=CLAVE).status_code, 200)
        estados = {m["id"]: m["estado"] for m in self.mejoras()}
        self.assertEqual((estados[conf["id"]], estados[desv["id"]]), ("aplicada", "aplicada"))
        self.assertEqual(self.c.post("/interno/pautas/pauta-prueba-01/version-siguiente", json={"actor": "x"}).status_code, 401)

    def test_la_propuesta_de_otra_empresa_no_se_ve(self):
        m = self.conformidad()
        self.assertEqual(self.borrador(m, self.ana).status_code, 403)
        self.assertEqual(self.c.get("/cliente/mejoras/no-existe/borrador", headers=self.carla).status_code, 404)


if __name__ == "__main__":
    unittest.main()
