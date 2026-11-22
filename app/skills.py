"""Las skills de Factum, servidas para que un agente las encuentre (PRD de skills, sección 7).

Viven en `.claude/skills/`, donde Claude Code las carga solas (ADR-0015). El servidor publica las de
cliente: las que usa una empresa con su token contra la API. Las internas (reconocer, optimizar,
reglas y visión) trabajan sobre el repo y la clave del equipo, y quedan en el repo.

`/llms.txt` es el índice que pide el estándar llms.txt (REFERENCIAS 75): un título, un resumen en
cita y listas de enlaces. La guía completa pasa a `/llms-full.txt`, igual que `/agente`.
"""

from __future__ import annotations

import re
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent / ".claude" / "skills"
REPO = "https://github.com/platanus-hack/platanus-hack-26-cl-team-10/blob/main/"
DE_CLIENTE = ("pedir-ot", "ejecutar-ot", "reportar-ot", "medir-y-mejorar")
INTERNAS = ("reconocer-proceso", "optimizar-proceso", "regla-programatica", "solucion-vision")


def leer(nombre: str) -> tuple[dict[str, str], str]:
    """El encabezado (`name`, `description`) y el texto completo de una skill."""
    texto = (CARPETA / nombre / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    encabezado = dict(re.findall(r"^(\w[\w-]*):\s*(.+)$", m.group(1), re.M)) if m else {}
    return encabezado, texto


def para_publicar(nombre: str) -> str:
    """El texto de la skill con sus enlaces al repo hechos absolutos: servida desde /skills, un enlace
    relativo como ../../../knowledge/... no lleva a ninguna parte."""
    def absoluto(m: re.Match) -> str:
        destino = m.group(2)
        if destino.startswith(("http", "#", "$")):
            return m.group(0)
        ruta = (CARPETA / nombre / destino.split("#")[0]).resolve()
        raiz = CARPETA.parent.parent
        ancla = "#" + destino.split("#", 1)[1] if "#" in destino else ""
        return f"[{m.group(1)}]({REPO}{ruta.relative_to(raiz).as_posix()}{ancla})"
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", absoluto, leer(nombre)[1])


def publicadas(base: str) -> list[dict]:
    base = base.rstrip("/")
    return [{"name": nombre, "description": leer(nombre)[0].get("description", ""),
             "url": f"{base}/skills/{nombre}/SKILL.md"} for nombre in DE_CLIENTE]


def llms_txt(base: str) -> str:
    base = base.rstrip("/")
    skills = "\n".join(f"- [{s['name']}]({s['url']}): {s['description']}" for s in publicadas(base))
    return f"""# Factum

> Factum es el copiloto de los operarios: comprueba cada paso de una orden de trabajo (OT) con sensores, cámara y
> reglas, avisa en el momento si se salta uno, y deja todo en una bitácora que solo agrega. Una empresa cliente entra
> con usuario y clave, pide OT de sus pautas, las ejecuta, saca su reporte y sus métricas, y valida las propuestas de
> mejora de sus pautas. Todo es una API HTTP en JSON, en español.

Se entra con `POST {base}/auth/entrar` (`usuario`, `clave`) y el `token` va en cada llamada como
`Authorization: Bearer <token>`. Cada empresa ve solo lo suyo: una OT de otra responde 404.

## Skills

Cada una es una carpeta con su `SKILL.md`, en el formato de Agent Skills: qué hacer, en qué orden y qué no hacer nunca.

{skills}

## Documentación

- [Guía completa]({base}/llms-full.txt): el recorrido, los WebSocket, el video, los errores y todas las rutas, en Markdown.
- [OpenAPI para clientes]({base}/referencia/clientes.json): solo lo que usa una empresa, con ejemplos reales.
- [OpenAPI completo]({base}/openapi.json): también el servicio interno, la estación y el demo.

## Optional

- [Referencia para personas]({base}/referencia): la misma API para leer y probar en el navegador, con Scalar.
"""
