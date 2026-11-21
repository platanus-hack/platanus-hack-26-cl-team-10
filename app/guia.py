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

OCULTAS = {"/", "/agente", "/llms.txt", "/camara", "/monitor", "/casos", "/referencia", "/referencia/clientes.json"}

# La comparten esta guía y la referencia (app/referencia.py).
ERRORES = """| Código | Cuerpo | Qué significa |
|---|---|---|
| 401 | `{"clave": "..."}` | El edge ya ejecuta otra OT, o se lo quiere soltar, o la llamada es del servicio interno, y falta la cabecera `X-Clave-Equipo`. `GET /clave` dice si este servidor la pide y si la que mandas sirve |
| 401 | `{"login": "..."}` | El servicio para clientes no recibió un token válido: falta, no existe o venció. Entrar con `POST /auth/entrar` |
| 403 | `{"permiso": "..."}` | La persona entró, pero su rol o su empresa no la dejan: un operador que pide una OT, o una pauta que su empresa no tiene habilitada |
| 404 | `{"no_existe": "..."}` | La OT, pauta, protocolo, paso, evento o sesión no existe |
| 409 | `{"regla": "..."}` | Lo pedido choca con una regla de negocio; el texto dice cuál |
| 422 | `{"detail": ...}` o `{"cuadro": "..."}` | El cuerpo está mal formado o el cuadro no es un JPEG válido |
| 405 | — | Se intentó editar o borrar algo que solo se lee (la bitácora) |
| 500 | — | Falló el servidor. No dice nada sobre si lo pedido existe: avisar al equipo |"""


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
    return f"""# Factum · API de flujos operacionales verificables

Guía para el agente que se conecta. Base: `{base}` · esquemas: `{base}/openapi.json` · referencia para probar cada ruta: `{base}/referencia`.
El servicio para clientes (`/cliente/...`) pide login y el interno (`/interno/...`), la clave del equipo. El resto no pide nada, salvo la clave del equipo para mover un edge (ver «Clave del equipo»): es un servidor de demo. Todo el contenido va en español y en JSON, salvo el video.

## Qué es

El copiloto del operario. Un operario ejecuta una orden de trabajo (OT) siguiendo una pauta, paso a paso. El edge
(sensores y cámara de la estación) manda lecturas y video. La API atribuye cada lectura a la OT en curso, decide qué paso
queda verificado, le avisa al operario si se salta uno, abre y resuelve alertas, y lo registra todo en una bitácora que
solo agrega. De esa bitácora salen las métricas y las propuestas para mejorar la pauta.

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
de anomalías. **El edge reenvía cada sensor al menos cada 5 s, cambie o no**: si el sensor del paso en curso
calla más que eso, la OT baja a `warning`.

Reglas de seguridad, una por industria: `guarda = abierta` con `energia = viva` (minería); `tierra = puesta`
con `tension = presente`, y `seccionador = cerrado` con `tierra = puesta` (eléctrica); `zona = ocupada` con
`implementos = levantados` (construcción). Abren una alerta `error` y se resuelven solas cuando el sensor se
corrige. Además, alertas de la pauta: **orden invertido** (se cerró un paso posterior con un control crítico
pendiente) y **control perdido** (se deshizo un control crítico ya verificado). La clase de cada alerta está en
`evidencia.clave`: `seguridad:`, `orden:`, `control:`, `senal:` o `pegado:`.

**Al declarar**, manda `paso_id` con el paso que la app le mostraba al operario
(`{{"actor":"operario:A","texto":"bloqueo puesto","paso_id":"p1"}}`). Si su sensor ya lo cerró, la palabra se
registra y no se evalúa contra el paso siguiente. Un paso de cámara necesita un cuadro de los últimos 10 s.

**Si el sensor no ve lo que la persona hizo** (sensor caído, mal montado, cámara sin vista), hablar no cierra el
paso: se confirma aparte, con quién y por qué, en `POST /ot/{{ot_id}}/pasos/{{paso_id}}/confirmar`
(`{{"actor":"supervisor:B","motivo":"el reed está dañado; el candado está puesto"}}`). Solo el paso en curso. El paso
queda verificado por persona, la OT en `warning` y las reglas de seguridad siguen evaluándose con los sensores.

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

`evento.tipo`: `ot_abierta` · `ot_asignada` · `declaracion` · `veredicto` · `alerta` · `alerta_resuelta` · `relevo_entregado` ·
`relevo_recibido` · `observacion` (lo que el operario vio; no cierra ningún paso). `evento.estado`: `verificado` · `no_verificado` · `en_conflicto`.

**Los avisos.** `calificacion.avisos` es la lista de lo que está mal AHORA, lo más grave primero. Un aviso
existe mientras venga en esa lista: cuando el sensor se corrige, el siguiente `calificacion_ot` ya no lo
trae y entra un evento `alerta_resuelta` cuya `evidencia.resuelve` es el `id` de la alerta que cierra.

**La calificación.** `nivel` es `ok`, `warning` o `error`; `certeza` va de 0 a 1. Solo la capa 1 (sensores y
reglas) llega a `error`. La capa 2 (anomalía de señal) y la capa 3 (cámara) llegan a lo más a `warning`.

## Video

- Entrada: `WS {ws}/edge/{{edge_id}}/video`, un JPEG por mensaje binario (máximo 2 MB, hasta 20 por segundo).
  Un cuadro inválido devuelve `{{"error": ...}}` y no corta la conexión. Por HTTP: `POST /edge/{{edge_id}}/cuadro`
  con el JPEG como cuerpo. El servidor guarda video de hasta 8 edges a la vez: si llega uno más, sale el
  que lleva más tiempo sin transmitir.
- Salida: `GET /edge/{{edge_id}}/video.mjpg` (MJPEG, sirve en un `<img>`), `GET /edge/{{edge_id}}/cuadro.jpg`
  (el último cuadro) y `GET /edge/{{edge_id}}/video` (si hay video, su edad y sus cuadros por segundo).
- Un paso de cámara se juzga con el último cuadro al llamar `POST /ot/{{ot_id}}/declarar`; el cuadro queda
  como evidencia del veredicto.
- Páginas listas: `{base}/camara` (el celular como cámara del edge; `?edge=<id>` elige el edge) y `{base}/monitor`
  (video, avisos y bitácora).

## Probar cada caso de uso

`{base}/casos` es el banco de pruebas: una tarjeta por criterio de aceptación, que corre la secuencia real
de llamadas contra este servidor u otro, con una OT y un edge propios (`casos-…`), y muestra cada request,
cada response y los mensajes del stream. Sirve de ejemplo ejecutable de cada recorrido. Debajo, la matriz de
escenarios por industria (`GET /escenarios`): cada forma de ejecutar un paso en minería, eléctrica y
construcción, corrida en una caja aislada que no toca la bitácora de este servidor.

## Protocolos, pautas y OT: dos servicios

- **Interno (`/interno/...`)**: lo usa el equipo, una vez por protocolo. Carga el documento del cliente
  (`POST /interno/protocolos`), crea sus pautas (`POST /interno/protocolos/{{protocolo_id}}/pautas`) o atribuye
  las que ya existen (`PUT /interno/pautas/{{pauta_id}}/protocolos/{{protocolo_id}}`), y las aprueba. Un protocolo da
  una o más pautas, y una pauta puede salir de más de un protocolo. Con `CLAVE_EQUIPO` pide `X-Clave-Equipo`.
- **Para clientes (`/cliente/...`), con login**: se entra con `POST /auth/entrar` (`usuario` y `clave`) y el token
  va en cada llamada como `Authorization: Bearer <token>`; dura 12 horas y `POST /auth/salir` lo cierra. `GET /yo`
  dice quién es. Cada empresa ve solo lo suyo: `GET /cliente/pautas` lista las pautas que el equipo le habilitó, y
  `GET /cliente/ots` sus OT (el operador, solo las que tiene asignadas), cada una con su `calificacion`. El supervisor
  pide OT con `POST /cliente/ots` y las asigna a un operador de su empresa con `POST /cliente/ots/{{ot_id}}/asignar`.
  `GET /cliente/personas` da el `id`, el `nombre` y el `rol` de las personas de la empresa, a cualquiera de ellas, para
  mostrar nombres donde la bitácora guarda ids como `operario:1`. El operador une su OT a una estación con
  `POST /cliente/ots/{{ot_id}}/sesion` (`edge_id`), sin la clave del equipo: si la estación ejecuta otra OT abierta
  responde 409 y se repite con `tomar` en true; la de otra empresa no se toma (403). Las empresas, sus personas y
  sus pautas las crea el equipo en `/interno/clientes`; la clave de cada persona se genera y se ve una sola vez.
- **Ejecutar la OT con login (`/cliente/ots/{{ot_id}}/...`)**: quien actúa sale del token, no de un `actor` en el cuerpo.
  `GET .../pasos` da el paso en curso; `POST .../declarar` (`texto`, `paso_id`) es del operador que tiene la OT;
  `POST .../pasos/{{paso_id}}/confirmar` (`motivo`), del operador o del supervisor; `POST .../relevo/entregar` deja la OT
  `entregada` y otro operador de la empresa la toma con `POST .../relevo/recibir`; `GET .../eventos` es la bitácora.
  `GET .../reporte` da el reporte de la OT armado desde la bitácora, en JSON o con `formato=markdown`: cada paso con la
  evidencia que lo cerró y su `evento`, cada desviación con su clase y cuánto tardó en resolverse, y lo pendiente. Las
  rutas `/ot/{{ot_id}}/...` sin login siguen para la pantalla del demo.
- **Para escribir una pauta (`/interno`)**: `GET /interno/inventario` dice qué sensores, valores, clases del detector y
  preguntas visuales conoce el servidor, leído de la bitácora y de las pautas; `POST /interno/pautas/validar` dice, sin
  guardar, si la pauta se puede crear y qué le fallaría a la verificación.
- **Mejora continua y métricas (`/cliente/...`), con login**: el operario o el supervisor deja lo que vio con
  `POST /cliente/ots/{{ot_id}}/observaciones` (`texto`, `categoria` y, si habla de uno, `paso_id`). Cuando el mismo paso de
  la misma versión tiene señales en dos o más OT (alertas de orden o de control, conflictos, pasos confirmados por una
  persona y observaciones de `pauta` o `seguridad`), nace una propuesta en `GET /cliente/mejoras`. El supervisor la acepta
  o la descarta en `POST /cliente/mejoras/{{propuesta_id}}/revision`; las aceptadas las ve el equipo en `GET /interno/mejoras`
  y las lleva a la versión siguiente de la pauta, y la propuesta dice después en `validacion` si el paso dejó de desviarse.
  Las métricas, solo para el supervisor: `GET /cliente/metricas` (el resumen), y `/pautas`, `/pautas/{{pauta_id}}/pasos`,
  `/equipos` y `/serie` debajo, con `desde`, `hasta` y `orden`. Agrupan por pauta, equipo, paso o día, nunca por persona.

## Clave del equipo

Si el servidor tiene `CLAVE_EQUIPO`, dos llamadas piden la cabecera `X-Clave-Equipo`: `POST /ot/{{ot_id}}/sesion` cuando el
edge ya ejecuta otra OT, y `DELETE /edge/{{edge_id}}/sesion`. Un operador con login no la usa: va por `POST /cliente/ots/{{ot_id}}/sesion`. Unir un edge libre o repetir la sesión que ya tiene no la pide,
y el resto de la API tampoco, salvo el servicio interno (`/interno/...`), que la pide en cada llamada. `GET /clave` dice si este servidor la pide y si la que mandas sirve. En el navegador, el home
y el banco la guardan al abrirlos una vez con `?clave=`.

## Errores

{ERRORES}

## Todos los endpoints

| Método | Ruta | Qué hace |
|---|---|---|
{rutas}
"""
