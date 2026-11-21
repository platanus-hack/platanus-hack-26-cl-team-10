# ADR-0007 — Servicios en vivo: sesión por edge, stream por OT y calificación por capa

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

La UI tiene que ver en vivo el estado de la OT que ejecuta el operario y su bitácora, mientras el edge manda lecturas todo el tiempo. El esqueleto evaluaba un paso solo cuando el operario declaraba, y `POST /sensores` escribía cada alerta de seguridad en **todas** las OT de la base, porque no sabía cuál se estaba ejecutando. Además faltaba una forma de decir qué tan grave es lo que pasa y cuánto creerle, para pintar la pantalla y redactar la justificación.

## Decisión

1. **La OT de cada edge la fija una sesión.** El operario elige la OT en la interfaz y abre una sesión (`POST /ot/{id}/sesion`) que la une a su edge. Desde ahí cada lectura de ese edge se atribuye a esa OT y solo a esa. Sin sesión, la lectura actualiza el sensor y no toca ninguna bitácora.
2. **El servicio revisa cada lectura atribuida** (`app/servicios.py`). La alerta de seguridad entra a la bitácora cuando la condición empieza, no en cada lectura mientras dura. Si el paso actual se cierra con ese sensor, entra su veredicto sin que el operario hable; solo el paso actual y solo con su propio sensor, para que el orden siga siendo de la app (ADR-0002). Una lectura numérica fuera de lo normal entra como alerta de capa 2: se muestra y no interrumpe.
3. **Un WebSocket por OT** (`/ot/{id}/stream`). Manda primero un snapshot (estado, calificación, sesión, sensores y bitácora) y después cada lectura, evento y calificación nueva. Para reconectar sin perder bitácora, el cliente vuelve con `?desde=<último id de evento>`. El reparto es en proceso (`app/bus.py`), sin broker, porque hay una aplicación y una base (ADR-0003).
4. **La calificación se calcula, no se guarda** (`app/scoring.py`). Lee el veredicto y devuelve `ok`, `warning` o `error`, con certeza y motivos. Solo la capa 1 llega a `error`, porque es la única que interrumpe (LOGICA.md). La capa 2 y la cámara llegan a lo más a `warning`. La calificación de la OT es la del peor paso vigente más la seguridad evaluada con los sensores de ahora, así una alerta vieja no la deja en `error` para siempre. Los motivos son la entrada del modelo que redacta la justificación.
5. **Una alerta se resuelve, no se borra.** Cuando su condición desaparece (el sensor se corrige) entra un evento `alerta_resuelta` que apunta a ella en `evidencia.resuelve`, y el aviso sale de `calificacion.avisos` en el siguiente mensaje del stream. Qué alertas siguen activas se lee de la bitácora, así un reinicio no las pierde.
6. **El video entra por su propio canal** (`app/video.py`): JPEG por `WS /edge/{id}/video` o `POST /edge/{id}/cuadro`, los últimos 10 segundos en memoria por edge, y salida MJPEG en `/edge/{id}/video.mjpg`. Un paso de cámara se juzga con el último cuadro del edge de la OT, y ese cuadro queda como evidencia del veredicto. Nunca viaja por el WebSocket de la OT, para que una ráfaga de cuadros no atrase una alerta.
7. **Una guía para el agente que se conecta** en `/agente` (y `/llms.txt`): recorrido, WebSocket, errores y el catálogo de endpoints armado desde las rutas reales.

El contrato cambia en una sola cosa: `TipoEvento` suma `alerta_resuelta` (`contratos.py` y [LOGICA](../architecture/LOGICA.md)). `reglas.py` no cambia: el juez de cámara recibe el cuadro por un parámetro opcional de `verificacion.juez_camara`, y la firma `JuezCamara` sigue igual.

## Despliegue del demo

Una VM `e2-small` en `southamerica-west1` con Caddy (HTTPS automático) y la API como servicio de systemd, en `https://34-176-44-192.sslip.io`. Una VM y no Cloud Run porque la bitácora es SQLite y tiene que sobrevivir a un reinicio, y el bus y el video viven en el proceso: con una sola máquina y disco propio, las tres cosas funcionan. Se redespliega con `deploy/vm/desplegar.sh`. Sin autenticación: es un servidor de demo.

## Alternativas consideradas

- **A — Broker MQTT entre el edge y la API:** desacopla y aguanta cortes, pero suma una pieza que el demo no necesita con un solo equipo. Se revisa si llega una segunda estación o una faena sin conectividad.
- **B — Guardar la calificación en cada evento:** obliga a agregar un campo al contrato y la congela con los umbrales del momento. Calcularla al leer la deja cambiar sin migrar la bitácora.

## Consecuencias

- `GET /ot/{id}/eventos` vuelve a funcionar: usaba `vars()` sobre un dataclass con `slots` y fallaba.
- Una lectura sin sesión no alerta a nadie. En el demo, la sesión se abre al empezar la OT.
- El juez de cámara del frente 3 ya recibe el cuadro; mientras sea el stub, no lo mira.
- Los sensores siguen siendo una tabla global: con dos equipos que usen el mismo `sensor_id` se pisarían. Para el demo hay uno.

## Pendientes y no verificado

- Los umbrales de la calificación (frescura 5 s, confianza de cámara 75 %, 3,5 desvíos en capa 2) son de partida; se calibran en el ensayo. `Candidata a validar`.
- Capa 2 calibrada con sensores reales: la dispersión no baja de un piso de ruido (2 % de la mediana, mínimo 0,1). Reproduciendo 2.293 lecturas del ESP32 del demo, las alertas abiertas bajaron de 138 a 17 y las que quedan son cambios reales. `Candidata a validar` con más equipos (`app/scoring.py`).
- La justificación en texto la redacta el frente 4 sobre los motivos; hoy viajan los motivos sin redactar. `Brecha`.

## Referencias

- [ADR-0002](./0002-la-aplicacion-impone-el-orden-de-la-pauta.md), [ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md), [ADR-0004](./0004-verificacion-por-capas.md) y [LOGICA](../architecture/LOGICA.md).
