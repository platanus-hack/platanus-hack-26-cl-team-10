"""La referencia de la API: el OpenAPI ordenado y su página con Scalar (`GET /referencia`).

FastAPI arma el OpenAPI desde las rutas. Acá se ordena para que sirva de documentación:
cada ruta en su grupo, el login y la clave del equipo como esquemas de seguridad (así la
página deja probar con un token), los errores con su cuerpo y, en lo que usa un cliente,
un ejemplo de cada respuesta.

Qué pide cada ruta se deduce de lo que la ruta lee, no de su nombre: la que recibe la
cabecera `Authorization` pide token, y la que recibe `X-Clave-Equipo`, la clave.
`tests/test_referencia.py` comprueba contra el servidor que lo declarado acá se cumple.

Hay dos documentos: el completo (`/openapi.json`) y el de un cliente
(`/referencia/clientes.json`), que deja fuera el servicio interno, la estación y el demo.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from scalar_fastapi import AgentScalarConfig, OpenAPISource, get_scalar_api_reference

from app.guia import ERRORES

TITULO = "Factum · flujos operacionales verificables"
VERSION = "0.1.0"
# Se fija la versión: en esta página se pega un token, y un script sin versión cambia solo.
SCALAR_JS = "https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.82.1"
PAGINAS = {"/", "/ensayo", "/camara", "/monitor", "/analisis", "/casos", "/agente"}
# Junto al código y no en datos/: desplegar.sh sube app/ entero, y de datos/ solo una lista de archivos.
EJEMPLOS = json.loads(Path(__file__).with_name("referencia_ejemplos.json").read_text())

ENTRAR, CLIENTE, EJECUCION, ESTACION = "Entrar", "Pedir y asignar OT", "Ejecución abierta del demo", "Estación"
EJECUTAR, MEJORA = "Ejecutar la OT", "Reportes, mejora y métricas"
INTERNO, INTERNO_CLIENTES = "Interno · protocolos y pautas", "Interno · clientes y personas"
ABIERTAS, ESCENARIOS, SIN_GRUPO = "Abiertas del demo", "Escenarios", "Sin clasificar"

GRUPOS = {
    ENTRAR: "El login. Una persona entra con su usuario y su clave y recibe un token que dura 12 horas. "
            "El token va en cada llamada como `Authorization: Bearer <token>`.",
    CLIENTE: "Lo que hace una empresa cliente con su token. El supervisor pide OT de las pautas que su empresa "
             "tiene habilitadas y las asigna; el operador ve las suyas. Cada empresa ve solo lo suyo: una OT de "
             "otra empresa responde 404.",
    EJECUTAR: "El operario ejecuta su OT con su token: la une a una estación, ve el paso en curso, declara, deja "
              "observaciones y entrega el turno; el supervisor puede confirmar un paso que la evidencia no vio. Quien "
              "actúa sale del token, no del cuerpo, y queda así en la bitácora.",
    MEJORA: "Lo que la empresa saca de cada ejecución. El reporte de cada OT se arma desde su bitácora, por paso y "
            "con evidencia, sin que lo redacte un modelo. El operario deja observaciones mientras trabaja; con ellas y "
            "con las desviaciones de cada paso nacen propuestas para mejorar la pauta, que el supervisor valida, y "
            "cuando sale la versión nueva se comprueba si el paso dejó de desviarse. Las métricas se leen de la "
            "bitácora al pedirlas, por pauta, equipo, paso o día, nunca por persona.",
    EJECUCION: "Lo mismo que «Ejecutar la OT», sin token: quien llama dice quién es en `actor`, y sirven para la OT "
               "de cualquier empresa. Las usan la pantalla del demo y el banco `/casos` mientras pasan a las rutas con "
               "login. No son parte del servicio al cliente.",
    ESTACION: "El edge: los sensores y la cámara de una estación, y la sesión que une una estación con la OT "
              "que ejecuta. Quitarle una estación a otra OT, o soltarla, pide la clave del equipo.",
    INTERNO: "Del equipo de Factum, con la clave del equipo. Acá se carga el protocolo de un cliente, se crean "
             "sus pautas, se atribuyen y se aprueban. Un cliente no usa estas rutas.",
    INTERNO_CLIENTES: "Del equipo de Factum, con la clave del equipo. Las empresas, sus personas con su clave, "
                      "y qué pautas puede pedir cada empresa.",
    ABIERTAS: "Rutas anteriores al login, que usan la pantalla del demo y el banco `/casos`. No piden nada: "
              "crean pautas sin protocolo, abren OT sin empresa y listan las OT de todos. No son parte del "
              "servicio al cliente. Brecha anotada en los ADR 0011 y 0012.",
    ESCENARIOS: "El banco por industria: cada forma de ejecutar un paso, corrida en una caja aislada que no "
                "toca la bitácora del servidor.",
}
PARA_CLIENTES = (ENTRAR, CLIENTE, EJECUTAR, MEJORA)

# La primera regla que calza decide el grupo. Una ruta que no calza con ninguna queda en
# «Sin clasificar», y la prueba falla hasta que alguien le ponga grupo.
_REGLAS = [(re.compile(patron), grupo) for patron, grupo in (
    (r"/(auth/.+|yo)", ENTRAR),
    (r"/cliente/(mejoras|metricas).*|/cliente/ots/\{ot_id\}/reporte", MEJORA),
    (r"/cliente/ots/\{ot_id\}/(sesion|pasos.*|declarar|observaciones|relevo/.+|eventos)", EJECUTAR),
    (r"/cliente/.+", CLIENTE),
    (r"/interno/(clientes|personas).*", INTERNO_CLIENTES),
    (r"/interno/.+", INTERNO),
    (r"/ot/\{ot_id\}/(abrir|asignar)", ABIERTAS),
    (r"/ot/\{ot_id\}/sesion", ESTACION),
    (r"/(ot/\{ot_id\}.*|eventos/.+)", EJECUCION),
    (r"/(edge/.+|sensores|sesiones|detector|clave)", ESTACION),
    (r"/(pautas.*|pauta/demo|ots|supervisor/.+)", ABIERTAS),
    (r"/(escenarios.*|industrias)", ESCENARIOS),
)]

TITULOS = {
    "POST /auth/entrar": "Entrar con usuario y clave",
    "POST /auth/salir": "Cerrar la sesión",
    "GET /yo": "Quién soy",
    "GET /cliente/pautas": "Pautas que la empresa puede pedir",
    "POST /cliente/ots": "Pedir una OT",
    "GET /cliente/ots": "Listar las OT",
    "GET /cliente/ots/{ot_id}": "Leer una OT",
    "POST /cliente/ots/{ot_id}/asignar": "Asignar una OT a un operador",
    "POST /cliente/ots/{ot_id}/sesion": "Unir la OT a una estación",
    "GET /cliente/operadores": "Operadores de la empresa",
    "GET /cliente/personas": "Nombres de las personas de la empresa",
    "POST /cliente/ots/{ot_id}/observaciones": "Dejar una observación",
    "GET /cliente/ots/{ot_id}/pasos": "Pasos de la OT y el paso en curso",
    "POST /cliente/ots/{ot_id}/declarar": "Declarar un paso",
    "POST /cliente/ots/{ot_id}/pasos/{paso_id}/confirmar": "Confirmar un paso contra la evidencia",
    "POST /cliente/ots/{ot_id}/relevo/entregar": "Entregar el turno",
    "POST /cliente/ots/{ot_id}/relevo/recibir": "Recibir el turno",
    "GET /cliente/ots/{ot_id}/eventos": "Bitácora de la OT",
    "GET /cliente/ots/{ot_id}/reporte": "Reporte de la OT",
    "GET /interno/inventario": "Inventario del servidor",
    "POST /interno/pautas/validar": "Validar una pauta sin guardarla",
    "GET /cliente/mejoras": "Propuestas de mejora de las pautas",
    "POST /cliente/mejoras/{propuesta_id}/revision": "Aceptar o descartar una propuesta",
    "GET /cliente/metricas": "Resumen de la empresa",
    "GET /cliente/metricas/pautas": "Métricas por pauta",
    "GET /cliente/metricas/pautas/{pauta_id}/pasos": "Métricas por paso de una pauta",
    "GET /cliente/metricas/equipos": "Métricas por equipo",
    "GET /cliente/metricas/serie": "Métricas en el tiempo",
    "GET /interno/mejoras": "Propuestas de mejora de todas las empresas",
    "GET /ot/{ot_id}": "Estado de la OT, paso por paso",
    "POST /ot/{ot_id}/declarar": "Declarar un paso",
    "POST /ot/{ot_id}/pasos/{paso_id}/confirmar": "Confirmar un paso por una persona",
    "GET /ot/{ot_id}/calificacion": "Calificación y avisos activos",
    "GET /ot/{ot_id}/alertas": "Alertas abiertas",
    "GET /ot/{ot_id}/eventos": "Bitácora de la OT",
    "GET /eventos/{evento_id}": "Leer un evento de la bitácora",
    "POST /ot/{ot_id}/relevo/entregar": "Entregar el turno",
    "POST /ot/{ot_id}/relevo/recibir": "Recibir el turno",
    "POST /ot/{ot_id}/preguntar": "Preguntarle a la bitácora",
}

# Los errores que cada ruta del login y del cliente puede devolver, además del 401 que se
# deduce de la seguridad. La prueba provoca cada uno.
ERRORES_DE = {
    "POST /auth/entrar": (401,),
    "POST /cliente/ots": (403, 409),
    "GET /cliente/ots/{ot_id}": (404,),
    "POST /cliente/ots/{ot_id}/asignar": (403, 404, 409),
    "POST /cliente/ots/{ot_id}/sesion": (403, 404, 409),
    "GET /cliente/operadores": (403,),
    "POST /cliente/ots/{ot_id}/observaciones": (404, 409),
    "GET /cliente/mejoras": (403,),
    "POST /cliente/mejoras/{propuesta_id}/revision": (403, 404, 409),
    "GET /cliente/metricas": (403,),
    "GET /cliente/metricas/pautas/{pauta_id}/pasos": (403, 404),
    "GET /cliente/ots/{ot_id}/pasos": (404,),
    "POST /cliente/ots/{ot_id}/declarar": (403, 404, 409),
    "POST /cliente/ots/{ot_id}/pasos/{paso_id}/confirmar": (404, 409),
    "POST /cliente/ots/{ot_id}/relevo/entregar": (403, 404, 409),
    "POST /cliente/ots/{ot_id}/relevo/recibir": (403, 404, 409),
    "GET /cliente/ots/{ot_id}/eventos": (404,),
    "GET /cliente/ots/{ot_id}/reporte": (404,),
}

_CUERPOS = {
    401: ("ErrorLogin", "login", "Falta el token, no existe o venció; o el usuario y la clave no calzan."),
    403: ("ErrorPermiso", "permiso", "La persona entró, pero su rol o su empresa no la dejan."),
    404: ("ErrorNoExiste", "no_existe", "No existe, o no es de la empresa de quien pregunta."),
    409: ("ErrorRegla", "regla", "Lo pedido choca con una regla de negocio; el texto dice cuál."),
}
_ERROR_CLAVE = ("ErrorClave", "clave", "Falta la clave del equipo en la cabecera `X-Clave-Equipo`, o no es la correcta.")

_SEGURIDAD = {
    "Token": {"type": "http", "scheme": "bearer", "bearerFormat": "opaco",
              "description": "El `token` que devuelve `POST /auth/entrar`. Dura 12 horas y `POST /auth/salir` lo cierra."},
    "ClaveEquipo": {"type": "apiKey", "in": "header", "name": "X-Clave-Equipo",
                    "description": "La clave del equipo de Factum. Un cliente no la tiene ni la necesita. "
                                   "`GET /clave` dice si este servidor la pide."},
}

_COMUN = f"""
## Errores

Todo error trae un cuerpo JSON con una sola llave, que dice de qué clase es.

{ERRORES}

## En vivo

`WS /ot/{{ot_id}}/stream?desde=<id>` manda el estado de la OT al conectar y después cada cambio: lecturas, eventos
de la bitácora y la calificación. OpenAPI no describe WebSocket, así que sus mensajes están en la guía
[`/agente`](/agente), junto con el video del edge.
"""

INTRO_CLIENTES = f"""Factum es el copiloto de tus operarios. Los acompaña mientras ejecutan una orden de trabajo (OT): comprueba
cada paso de su pauta con sensores y cámara, y les avisa en el momento si se saltan uno. Como está en cada trabajo, todo
queda registrado con su evidencia en una bitácora que solo agrega: el reporte no se escribe ni omite nada, la pauta
mejora con cada ejecución y la operación sabe que cada trabajo se hizo bien sin poner un supervisor encima de cada uno.

Este documento es el de una empresa cliente. El completo, con el servicio interno y la estación, se elige arriba.

## Del protocolo a la OT

1. **Protocolo.** El documento de la empresa. Lo carga el equipo de Factum.
2. **Pauta.** Los pasos comprobables que salen de ese protocolo. La arma y la aprueba el equipo de Factum, y la
   habilita para la empresa.
3. **OT.** La pide un supervisor de la empresa, desde una pauta habilitada, cada vez que hay que ejecutar la tarea.

Una empresa no crea protocolos ni pautas por esta API. Pide OT de las pautas de `GET /cliente/pautas`, y una OT
siempre nace de una pauta aprobada que sale de un protocolo.

## Entrar

El equipo de Factum entrega a cada persona su usuario y su clave. `POST /auth/entrar` devuelve un `token`, que va
en cada llamada como `Authorization: Bearer <token>`. Dura 12 horas y `POST /auth/salir` lo cierra. En esta página
se pega una vez en «Authentication» y sirve para probar todas las rutas.

## Qué hace cada rol

| Rol | Qué puede |
|---|---|
| Supervisor | Ver las pautas habilitadas, pedir OT, ver todas las OT de su empresa y asignarlas a un operador; validar las propuestas de mejora y leer las métricas |
| Operador | Ver las OT que tiene asignadas, unir una a una estación, ejecutarla y dejar observaciones |

## El recorrido

1. El supervisor mira `GET /cliente/pautas` y pide la OT con `POST /cliente/ots`.
2. El supervisor elige a quién con `GET /cliente/operadores` y la asigna con `POST /cliente/ots/{{ot_id}}/asignar`.
3. El operador la ve en `GET /cliente/ots` y la une a su estación con `POST /cliente/ots/{{ot_id}}/sesion`.
4. El operador ejecuta: `GET /cliente/ots/{{ot_id}}/pasos` dice el paso en curso, los sensores de la estación cierran
   los pasos que miden, y `POST /cliente/ots/{{ot_id}}/declarar` cierra los que dependen de la cámara o de la palabra.
   Deja lo que vio en `POST /cliente/ots/{{ot_id}}/observaciones` y, si no termina, entrega el turno con
   `POST /cliente/ots/{{ot_id}}/relevo/entregar`; otro operador lo recibe con `.../relevo/recibir`.
5. Cualquiera de los dos sigue el avance y la calificación en `GET /cliente/ots/{{ot_id}}`. Al terminar,
   `GET /cliente/ots/{{ot_id}}/reporte` da el reporte armado desde la bitácora, en JSON o en Markdown.
6. El supervisor mide en `GET /cliente/metricas` y sus detalles por pauta, paso, equipo y día, y valida las
   propuestas de `GET /cliente/mejoras`. Lo que acepta lo lleva el equipo de Factum a la versión siguiente de la
   pauta, y la misma propuesta dice después si el paso dejó de desviarse.

Las métricas y las propuestas agrupan por pauta, equipo, paso y día, nunca por persona: Factum mira el paso, no a
quien lo ejecuta. El reporte de una OT sí nombra a quienes la ejecutaron, como una notificación de cierre.

Todo este recorrido pide token. Las rutas sin login de `/ot/{{ot_id}}/...` que aparecen en el documento completo son de la
pantalla del demo, y no las usa un cliente.
{_COMUN}"""

INTRO_COMPLETA = f"""Todas las rutas de la API de Factum, por grupo. El documento «Para clientes», que se elige arriba, trae solo lo
que usa una empresa y explica el recorrido.

## Quién usa qué

| Grupo | Quién | Qué pide |
|---|---|---|
| Entrar, Pedir y asignar OT, Ejecutar la OT, Reportes, mejora y métricas | Las personas de una empresa cliente | Token de `POST /auth/entrar` |
| Ejecución abierta del demo | La pantalla del demo y el banco `/casos` | Nada (brecha del ADR-0012, hasta que pasen a las rutas con login) |
| Estación | El edge y la interfaz | Nada, salvo la clave del equipo para quitarle una estación a otra OT |
| Interno | El equipo de Factum | La clave del equipo, en `X-Clave-Equipo` |
| Abiertas del demo, Escenarios | La pantalla del demo y el banco `/casos` | Nada |

Si el servidor no tiene `CLAVE_EQUIPO` definida, como en local, la clave del equipo no se pide.
{_COMUN}"""


def grupo_de(ruta: str) -> str:
    return next((grupo for patron, grupo in _REGLAS if patron.fullmatch(ruta)), SIN_GRUPO)


def _titulo(nombre: str) -> str:
    texto = re.sub(r"\b[oO]ts?\b", "OT", nombre.replace("_", " ").capitalize())
    return texto.replace("esion", "esión").replace("atribucion", "atribución")


def _error(codigo: int, cuerpo: tuple[str, str, str], cabeceras: dict | None = None) -> dict:
    esquema, _, descripcion = cuerpo
    r = {"description": descripcion,
         "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{esquema}"}}}}
    if cabeceras:
        r["headers"] = cabeceras
    return r


def _ordenar_operacion(op: dict, ruta: APIRoute, metodo: str) -> None:
    clave = f"{metodo} {ruta.path}"
    op["operationId"] = ruta.name
    op["summary"] = TITULOS.get(clave) or _titulo(ruta.name)
    op["tags"] = [grupo_de(ruta.path)]

    cabeceras = {p["name"].lower() for p in op.get("parameters", []) if p["in"] == "header"}
    resto = [p for p in op.get("parameters", []) if not (p["in"] == "header" and p["name"].lower() in ("authorization", "x-clave-equipo"))]
    op.pop("parameters", None)
    if resto:
        op["parameters"] = resto

    respuestas = op["responses"]
    if "authorization" in cabeceras:
        op["security"] = [{"Token": []}]
        respuestas["401"] = _error(401, _CUERPOS[401], {"WWW-Authenticate": {"schema": {"type": "string"}, "description": "`Bearer`"}})
    elif "x-clave-equipo" in cabeceras:
        # `_solo_equipo` la exige siempre; las demás rutas la piden solo si la estación está ocupada.
        exigida = "_solo_equipo" in ruta.endpoint.__code__.co_names
        op["security"] = [{"ClaveEquipo": []}] if exigida else [{"ClaveEquipo": []}, {}]
        respuestas["401"] = _error(401, _ERROR_CLAVE)
    for codigo in ERRORES_DE.get(clave, ()):
        respuestas.setdefault(str(codigo), _error(codigo, _CUERPOS[codigo]))

    for codigo, r in respuestas.items():
        if r.get("description") == "Successful Response":
            r["description"] = "Sin contenido" if codigo == "204" else "Correcto"
        elif r.get("description") == "Validation Error":
            r["description"] = "El cuerpo o un parámetro está mal formado."

    ejemplo = EJEMPLOS.get(clave, {})
    if "pedido" in ejemplo:
        op["requestBody"]["content"]["application/json"]["example"] = ejemplo["pedido"]
    if "respuesta" in ejemplo:
        ok = next(r for codigo, r in respuestas.items() if codigo.startswith("2"))
        ok["content"]["application/json"]["example"] = ejemplo["respuesta"]


def completa(app: FastAPI) -> dict:
    """El OpenAPI de toda la API. Se arma una vez y queda en `app.openapi_schema`."""
    if app.openapi_schema:
        return app.openapi_schema
    rutas = [r for r in app.routes if isinstance(r, APIRoute) and r.include_in_schema and r.path not in PAGINAS]
    doc = get_openapi(title=TITULO, version=VERSION, description=INTRO_COMPLETA, routes=rutas,
                      tags=[{"name": nombre, "description": descripcion} for nombre, descripcion in GRUPOS.items()])
    componentes = doc.setdefault("components", {})
    componentes["securitySchemes"] = deepcopy(_SEGURIDAD)
    for esquema, llave, descripcion in (*_CUERPOS.values(), _ERROR_CLAVE):
        componentes.setdefault("schemas", {})[esquema] = {
            "type": "object", "title": esquema, "description": descripcion, "required": [llave],
            "properties": {llave: {"type": "string", "description": "El motivo, en palabras."}}}
    for ruta in rutas:
        for metodo in ruta.methods - {"HEAD", "OPTIONS"}:
            _ordenar_operacion(doc["paths"][ruta.path][metodo.lower()], ruta, metodo)
    app.openapi_schema = doc
    return doc


def _esquemas_usados(doc: dict) -> set[str]:
    usados: set[str] = set()
    pendientes = set(re.findall(r"#/components/schemas/([^\"]+)", json.dumps(doc["paths"])))
    while pendientes:
        nombre = pendientes.pop()
        usados.add(nombre)
        pendientes |= set(re.findall(r"#/components/schemas/([^\"]+)", json.dumps(doc["components"]["schemas"][nombre]))) - usados
    return usados


def para_clientes(app: FastAPI) -> dict:
    """El mismo documento, con solo lo que usa una empresa cliente: entrar, su servicio y la ejecución de la OT."""
    doc = deepcopy(completa(app))
    doc["info"]["description"] = INTRO_CLIENTES
    doc["tags"] = [t for t in doc["tags"] if t["name"] in PARA_CLIENTES]
    doc["paths"] = {
        ruta: operaciones for ruta, operaciones in (
            (ruta, {m: op for m, op in operaciones.items() if op["tags"][0] in PARA_CLIENTES})
            for ruta, operaciones in doc["paths"].items()) if operaciones}
    usados = _esquemas_usados(doc)
    doc["components"]["schemas"] = {n: e for n, e in doc["components"]["schemas"].items() if n in usados}
    doc["components"]["securitySchemes"] = {"Token": _SEGURIDAD["Token"]}
    return doc


def pagina(openapi_url: str = "/openapi.json", clientes_url: str = "/referencia/clientes.json") -> HTMLResponse:
    """La página de Scalar con los dos documentos. No guarda el token ni manda telemetría."""
    return get_scalar_api_reference(
        title="Factum · referencia de la API",
        sources=[OpenAPISource(title="Para clientes", slug="clientes", url=clientes_url, default=True),
                 OpenAPISource(title="Completa", slug="completa", url=openapi_url)],
        scalar_js_url=SCALAR_JS, scalar_favicon_url="", telemetry=False, persist_auth=False,
        agent=AgentScalarConfig(disabled=True), hide_client_button=True, show_developer_tools="never",
        default_open_all_tags=True)
