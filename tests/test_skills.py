"""Las skills de .claude/skills/ cumplen el formato de Agent Skills y no le mienten a la API.

Si alguien cambia una ruta que una skill nombra, esta prueba falla en vez de dejar la skill
apuntando a algo que no existe (PRD de skills, CA6).

Correr:  uv run --with httpx python -m unittest tests.test_skills
"""

import importlib.util
import re
import unittest

from app import skills

TIENE_HTTPX = importlib.util.find_spec("httpx") is not None and importlib.util.find_spec("fastapi") is not None
NOMBRE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
RUTA = re.compile(r"\b(GET|POST|PUT|DELETE)\s+(?:\$FACTUM_URL)?(/[\w\-{}/.<>]+)")


def todas():
    return sorted(p.parent.name for p in skills.CARPETA.glob("*/SKILL.md"))


class ElFormato(unittest.TestCase):
    def test_estan_las_ocho(self):
        self.assertEqual(set(todas()), set(skills.DE_CLIENTE) | set(skills.INTERNAS))

    def test_cada_una_cumple_la_especificacion_de_agent_skills(self):
        for nombre in todas():
            encabezado, texto = skills.leer(nombre)
            with self.subTest(nombre):
                self.assertEqual(encabezado.get("name"), nombre)
                self.assertTrue(NOMBRE.fullmatch(nombre) and len(nombre) <= 64)
                self.assertTrue(0 < len(encabezado.get("description", "")) <= 1024)
                self.assertIn("Úsala cuando", encabezado["description"])
                self.assertLess(len(texto.splitlines()), 500)

    def test_ninguna_lleva_un_secreto(self):
        for nombre in todas():
            texto = skills.leer(nombre)[1]
            with self.subTest(nombre):
                self.assertNotRegex(texto, r"Bearer [A-Za-z0-9_\-]{20,}")
                self.assertNotRegex(texto, r'"clave"\s*:\s*"[^"$<]{6,}"')


@unittest.skipUnless(TIENE_HTTPX, "requiere fastapi y httpx")
class LasRutas(unittest.TestCase):
    def setUp(self):
        from fastapi.routing import APIRoute
        from fastapi.testclient import TestClient

        from app import api, db
        from app.servicios import Servicios

        api.cx = db.conectar(":memory:")
        api.servicios = Servicios(api.cx)
        self.c = TestClient(api.app)
        self.rutas = [(m, r.path) for r in api.app.routes if isinstance(r, APIRoute) for m in r.methods]

    def existe(self, metodo, ruta):
        ruta = ruta.split("?")[0].rstrip("/.")
        patron = lambda p: re.fullmatch(re.sub(r"\\\{[^}]+\\\}|<[^>]+>", "[^/]+", re.escape(p)), ruta)  # noqa: E731
        literal = lambda p: re.fullmatch(re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(p)), re.sub(r"<[^>]+>|\{[^}]+\}", "x", ruta))  # noqa: E731
        return any(m == metodo and (patron(p) or literal(p)) for m, p in self.rutas)

    def test_cada_ruta_que_nombra_una_skill_existe_con_ese_metodo(self):
        vistas = 0
        for nombre in todas():
            texto = skills.leer(nombre)[1]
            for metodo, ruta in RUTA.findall(texto):
                vistas += 1
                with self.subTest(skill=nombre, ruta=f"{metodo} {ruta}"):
                    self.assertTrue(self.existe(metodo, ruta), f"{nombre} nombra {metodo} {ruta}, que la API no tiene")
            for ruta in re.findall(r'curl -s(?: -X (?:POST|PUT|DELETE))? "\$FACTUM_URL(/[^"?]+)', texto):
                metodo = re.search(rf'curl -s(?: -X (\w+))? "\$FACTUM_URL{re.escape(ruta)}', texto).group(1) or "GET"
                vistas += 1
                with self.subTest(skill=nombre, curl=f"{metodo} {ruta}"):
                    self.assertTrue(self.existe(metodo, ruta), f"{nombre} llama {metodo} {ruta}, que la API no tiene")
        self.assertGreater(vistas, 30)

    def test_el_servidor_publica_las_de_cliente_y_no_las_internas(self):
        lista = self.c.get("/skills").json()
        self.assertEqual([s["name"] for s in lista], list(skills.DE_CLIENTE))
        for s in lista:
            r = self.c.get(f"/skills/{s['name']}/SKILL.md")
            self.assertEqual(r.status_code, 200)
            self.assertIn("text/markdown", r.headers["content-type"])
            self.assertEqual(r.text, skills.para_publicar(s["name"]))
            self.assertNotRegex(r.text, r"\]\(\.\./", "un enlace relativo no lleva a ninguna parte desde el servidor")
        for nombre in (*skills.INTERNAS, "no-existe", "..%2F..%2Fapp"):
            self.assertEqual(self.c.get(f"/skills/{nombre}/SKILL.md").status_code, 404, nombre)

    def test_llms_txt_es_el_indice_del_estandar(self):
        texto = self.c.get("/llms.txt").text
        lineas = texto.splitlines()
        self.assertEqual(lineas[0], "# Factum")
        self.assertTrue(lineas[2].startswith("> "))
        secciones = re.findall(r"^## (.+)$", texto, re.M)
        self.assertEqual(secciones, ["Skills", "Documentación", "Optional"])
        for nombre in skills.DE_CLIENTE:
            self.assertIn(f"[{nombre}](http://testserver/skills/{nombre}/SKILL.md): ", texto)
        self.assertIn("(http://testserver/llms-full.txt)", texto)
        self.assertEqual(self.c.get("/llms-full.txt").text, self.c.get("/agente").text)


if __name__ == "__main__":
    unittest.main()
