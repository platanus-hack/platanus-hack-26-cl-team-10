"""La guía para el agente que se conecta a la API: `GET /agente` (también `/llms.txt`).

Es texto plano en Markdown, pensado para que un agente lo lea de una vez y sepa
qué llamar y en qué orden. El recorrido está escrito a mano; el catálogo de
endpoints se arma desde las rutas reales de la aplicación, así no se desfasa del
código. El esquema de cada cuerpo está en `/openapi.json`; los WebSocket no
aparecen ahí, por eso se documentan acá.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import WebSocketRoute

OCULTAS = {"/", "/agente", "/llms.txt", "/camara", "/monitor"}


def catalogo_de_rutas(app: FastAPI) -> list[tuple[str, str, str]]:
    """(método, ruta, qué hace) de cada endpoint, en el orden en que se declaran."""
    filas = []
    for r in app.routes:
        if getattr(r, "path", None) in OCULTAS:
            continue
        if isinstance(r, WebSocketRoute):
            metodo = "WS"
        elif isinstance(r, APIRoute):
            metodo = "/".join(sorted(r.methods - {"HEAD", "OPTIONS"}))
        else:
            continue
        doc = (r.endpoint.__doc__ or "").strip().split("\n\n")[0]
        que = " ".join(doc.split()) or r.endpoint.__name__.replace("_", " ")
        filas.append((metodo, r.path, que))
    return filas


def guia(app: FastAPI, base: str) -> str:
    base = base.rstrip("/")
    ws = base.replace("https://", "wss://").replace("http://", "ws://")
    rutas = "\n".join(f"| `{m}` | `{p}` | {q} |" for m, p, q in catalogo_de_rutas(app))
    return f"""# Factum · API de mantenimiento verificado

Guía para el agente que se conecta. Base: `{base}` · esquemas: `{base}/openapi.json` · explorador: `{base}/docs`.
Sin autenticación: es un servidor de demo. Todo el contenido va en español y en JSON, salvo el video.

## Qué es

Un operario ejecuta una orden de trabajo (OT) siguiendo una pauta, paso a paso. El edge (sensores y
cámara de la estación) manda lecturas y video. La API atribuye cada lectura a la OT en curso, decide
qué paso queda verificado, abre y resuelve alertas, y lo registra todo en una bitácora que solo agrega.

## Las reglas que no se rompen

1. El orden lo impone la API: solo se evalúa el paso actual de la OT.
2. Un paso de sensor nunca se cierra hablando: lo cierra la lectura del sensor.
3. La bitácora solo agrega: no hay forma de editar ni borrar un evento (405).
4. Una OT solo nace de una pauta aprobada por una persona.
5. Una alerta no se borra: cuando su condición desaparece entra un evento `alerta_resuelta`.

## Recorrido mínimo

```bash
curl -X POST {base}/pauta/demo                      # carga y aprueba la pauta del demo
curl -X POST {base}/ot/ot-1/abrir                   # abre la OT desde esa pauta
curl -X POST {base}/ot/ot-1/sesion -H 'content-type: application/json' \\
     -d '{{"edge_id":"edge-1","operario":"operario:A"}}'   # une la OT con su edge
curl -X POST {base}/edge/edge-1/lecturas -H 'content-type: application/json' \\
     -d '[{{"sensor_id":"reed_bloqueo","valor":"cerrado","seq":1}}]'   # el edge manda una lectura
curl {base}/ot/ot-1                                 # estado por paso
curl {base}/ot/ot-1/calificacion                    # ok · warning · error, con avisos activos
curl {base}/ot/ot-1/eventos                         # la bitácora
```

Sensores de la pauta del demo: `reed_bloqueo` (`cerrado` · `abierto`), `guarda` (`abierta` · `cerrada`),
`energia` (`viva` · `cortada`). Un valor numérico (por ejemplo `vibracion`) pasa además por la detección
de anomalías. La regla de seguridad vigente: `guarda = abierta` con `energia = viva` abre una alerta de
nivel `error`, y se resuelve sola cuando cualquiera de los dos sensores se corrige.

## En vivo: `WS {ws}/ot/{{ot_id}}/stream?desde=<id>`

Conéctate y solo escucha; no hay que mandar nada. El primer mensaje es el snapshot y después llega
cada cambio. Para reconectar sin perder bitácora, vuelve con `desde` = el último `evento.id` que viste.

| `tipo` | Cuándo llega | Campos |
|---|---|---|
| `snapshot` | Al conectar | `estado` (pasos y `paso_actual`), `calificacion`, `alertas_activas`, `sesion`, `video`, `sensores`, `bitacora` |
| `lectura` | Cada lectura del edge de la OT | `edge_id`, `sensor_id`, `valor`, `ts` |
| `evento` | Cada fila nueva de la bitácora | `evento` con `id`, `tipo`, `paso_id`, `estado`, `capa`, `detalle`, `evidencia`, `calificacion` |
| `calificacion_ot` | Después de cada lectura o declaración | `calificacion` con `nivel`, `certeza`, `capa`, `motivos`, `avisos` |
| `sesion` | Al abrir una sesión | `sesion`, `video` |

`evento.tipo`: `ot_abierta` · `declaracion` · `veredicto` · `alerta` · `alerta_resuelta` · `relevo_entregado` ·
`relevo_recibido`. `evento.estado`: `verificado` · `no_verificado` · `en_conflicto`.

**Los avisos.** `calificacion.avisos` es la lista de lo que está mal AHORA, lo más grave primero. Un aviso
existe mientras venga en esa lista: cuando el sensor se corrige, el siguiente `calificacion_ot` ya no lo
trae y entra un evento `alerta_resuelta` cuya `evidencia.resuelve` es el `id` de la alerta que cierra.

**La calificación.** `nivel` es `ok`, `warning` o `error`; `certeza` va de 0 a 1. Solo la capa 1 (sensores y
reglas) llega a `error`. La capa 2 (anomalía de señal) y la capa 3 (cámara) llegan a lo más a `warning`.

## Video

- Entrada: `WS {ws}/edge/{{edge_id}}/video`, un JPEG por mensaje binario (máximo 2 MB, hasta 10 por segundo).
  Un cuadro inválido devuelve `{{"error": ...}}` y no corta la conexión. Por HTTP: `POST /edge/{{edge_id}}/cuadro`
  con el JPEG como cuerpo.
- Salida: `GET /edge/{{edge_id}}/video.mjpg` (MJPEG, sirve en un `<img>`), `GET /edge/{{edge_id}}/cuadro.jpg`
  (el último cuadro) y `GET /edge/{{edge_id}}/video` (si hay video, su edad y sus cuadros por segundo).
- Un paso de cámara se juzga con el último cuadro al llamar `POST /ot/{{ot_id}}/declarar`; el cuadro queda
  como evidencia del veredicto.
- Páginas listas: `{base}/camara` (el celular como cámara del edge) y `{base}/monitor` (video, avisos y bitácora).

## Errores

| Código | Cuerpo | Qué significa |
|---|---|---|
| 404 | `{{"no_existe": "..."}}` | La OT, pauta, evento o sesión no existe |
| 409 | `{{"regla": "..."}}` | Lo pedido choca con una regla de negocio; el texto dice cuál |
| 422 | `{{"detail": ...}}` o `{{"cuadro": "..."}}` | El cuerpo está mal formado o el cuadro no es un JPEG válido |
| 405 | — | Se intentó editar o borrar algo que solo se lee (la bitácora) |

## Todos los endpoints

| Método | Ruta | Qué hace |
|---|---|---|
{rutas}
"""
