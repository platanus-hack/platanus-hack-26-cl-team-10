# La aplicación

La API de Factum: implementa [LOGICA.md](../knowledge/architecture/LOGICA.md). Correr:

```bash
uv run uvicorn app.api:app --reload   # la demo queda en http://localhost:8000 (ensayo manual en /ensayo)
python3 -m unittest discover tests    # reglas, calificación y servicios, sin dependencias
uv run --with httpx python -m unittest discover tests   # además el WebSocket de punta a punta
uv run --with pytest --with httpx pytest -q   # lo mismo con pytest
python3 scripts/recorrido_demo.py     # los cinco momentos del demo, de punta a punta
uv run python scripts/correr_casos.py http://localhost:8000   # el banco /casos en Chrome sin ventana: cuántos casos pasan
python3 scripts/simular_capa2.py      # capa 2: qué detector aguanta qué falla, por industria (señales sintéticas)
python3 scripts/evaluar_capa3.py      # capa 3: falsa aceptación y falso rechazo del juez de cámara
uv run python scripts/analizar.py pauta datos/pauta-polin.json --estacion datos/estaciones/correa-ct-01.json   # qué puede cerrar la estación y qué vale la pena analizar
uv run python scripts/analizar.py ejecuciones   # cómo se ejecutó cada pauta, paso por paso
uv run python scripts/simular_mejora.py --rapido   # el eval de la mejora continua (sin --rapido, ~11 min; escribe simulacion.md)
uv run python scripts/medir_latencia.py https://servidor   # de la lectura en el edge a la bitácora, con `medido_en`
```

## Quién toca qué

| Archivo | Dueño | Qué reemplaza |
|---|---|---|
| `protocolos.py` | Frente 1 | Lee las pautas de `datos/`. Del protocolo a la pauta no hay ruta: lo hace el equipo con la skill `reconocer-proceso` y lo comprueba `analisis.py` (ADR-0011, ADR-0015). `cargar_semilla` carga los protocolos de `datos/protocolos.json` y les atribuye las pautas de `datos/` |
| `api.py` + `estatico/` | Frente 2 | La UI de ensayo por la app del operario con voz |
| `servicios.py` + `bus.py` | Servicios | Atribuye lo del edge a la OT de la sesión y lo reparte por `/ot/{id}/stream` ([ADR-0007](../knowledge/decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md)) |
| `scoring.py` | Servicios | La calificación ok · warning · error con certeza y motivos, por capa |
| `acceso.py` | Servicios | Clientes, sus personas y el login del servicio para clientes: token Bearer, roles supervisor y operador, y qué pautas tiene habilitadas cada empresa ([ADR-0012](../knowledge/decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md)) |
| `semilla.py` | Servicios | Datos de ejemplo: los protocolos con sus pautas y 21 OT en distintos estados (`datos/ots-semilla.json`), ejecutadas contra las reglas reales. `uv run python -m app.semilla` o `POST /interno/ots/semilla`. Con `--sin-historia` carga los protocolos, las pautas y las personas, pero no crea OT de ejemplo ni habilita pautas |
| `catalogo.py` | Servicios | El CRUD de pautas, aprobaciones, OT y eventos, con las reglas de negocio como 409. También el de protocolos y su atribución a pautas (`/interno/...`, con la clave del equipo) y las OT que pide un cliente (`/cliente/...`): [ADR-0011](../knowledge/decisions/0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md) |
| `video.py` | Servicios | El video del edge: entra por `WS /edge/{id}/video`, sale como MJPEG y le da al juez de cámara el último cuadro |
| `escenarios.py` | Servicios | La matriz de industria × patrón de ejecución contra cada barrera, en una caja aislada ([ADR-0008](../knowledge/decisions/0008-escenarios-por-industria-en-una-caja-aislada.md)). Las pautas de eléctrica y construcción están en `datos/` |
| `guia.py` | Servicios | La guía para agentes en `/agente`, con el catálogo de endpoints armado desde las rutas |
| `inventario.py` | Servicios | Qué puede comprobar el servidor, leído de la base (pautas, bitácora, sensores, reglas de peligro y detector), y el validador de una pauta contra eso: V1 a V4 e I1 a I3 ([PRD de skills](../knowledge/projects/skills/PRD.md)) |
| `reporte.py` | Servicios | El reporte de una OT armado desde su bitácora, en JSON o en Markdown: cada paso con la evidencia que lo cerró y su `evento`, las desviaciones, las confirmaciones por persona, las observaciones, los relevos y lo pendiente. Para el supervisor, `mejoras` (sección «Mejoras sugeridas»): las propuestas en que aportó la OT y las de conformidad, con su cambio en una línea por paso, por qué conviene (`porque`) y cómo se sabrá si funcionó (`como_se_mide`, de `sugerencias.para_una_persona`). No lo redacta un modelo |
| `skills.py` | Servicios | Publica las skills de cliente de `.claude/skills/` en `/skills` y arma el índice `/llms.txt`; la guía completa queda en `/llms-full.txt` y `/agente`. `tests/test_skills.py` comprueba que cada ruta que nombra una skill exista |
| `mejora.py` | Servicios | La mejora continua de las pautas: propuestas por paso desde las señales de cada ejecución (`desviacion`) y desde los controles del protocolo que la pauta no cumple (`conformidad`, [ADR-0016](../knowledge/decisions/0016-una-pauta-sale-del-protocolo-que-aplica-a-su-tarea.md)); el aviso al supervisor apenas un paso es recurrente con el α del aviso (`alfa_en_vivo`, lo dispara `servicios.py`); la revisión del supervisor; la validación con la versión nueva y la escalada cuando un cambio no bajó el paso ([ADR-0014](../knowledge/decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md), [ADR-0018](../knowledge/decisions/0018-la-pauta-tiene-un-protocolo-dueno-y-cada-protocolo-itera-por-separado.md)) |
| `sugerencias.py` | Servicios | El cambio concreto de cada propuesta (`GET /cliente/mejoras/{id}/borrador`): agrega el paso del control que falta, separa dos controles juntos o reescribe el paso que se desvía, comprobado contra los controles del protocolo. Lo arma el código; con `ANTHROPIC_API_KEY`, Claude Opus 5.5 (`CEREBRO_MODELO`) puede reescribir solo el texto, y el código lo descarta si cita una OT ajena o toca otra cosa. `POST /interno/pautas/{id}/version-siguiente` junta las aceptadas en una versión sin aprobar. `GET /cliente/mejoras/resumen` arma, por pauta, la versión siguiente con todo lo que Factum ya avisó, y `POST /cliente/pautas/{id}/mejoras/aplicar` la acepta entera y la deja sin aprobar |
| `recurrencia.py` | Servicios | Si un paso se desvía más que el resto de su pauta (binomial exacta con Holm) y si una versión nueva lo bajó de verdad (Fisher exacta). Lo usa `mejora.py` en `recurrencia` y `validacion` |
| `simulacion.py` + `scripts/simular_mejora.py` | Servicios | OT simuladas con conductas erróneas por causa, por los servicios reales en memoria, y el eval de la mejora continua: fidelidad, criterio, validación y las escenas del demo ([resultados](../knowledge/projects/mejora-continua/simulacion.md)) |
| Protocolos por empresa (en `catalogo.py`) | Servicios | Un protocolo es de una empresa o de la biblioteca de Factum. `POST /interno/clientes/{cliente_id}/protocolos` (`catalogo.instanciar`) copia uno de la biblioteca con sus pautas, aprobadas y habilitadas solo para esa empresa; cada pauta tiene un protocolo dueño (`pauta_duena`) donde itera. Métricas por protocolo en `GET /cliente/metricas/protocolos` ([ADR-0018](../knowledge/decisions/0018-la-pauta-tiene-un-protocolo-dueno-y-cada-protocolo-itera-por-separado.md)) |
| `metricas.py` | Servicios | Las métricas de una empresa, leídas de la bitácora al pedirlas: resumen, por pauta, por paso, por equipo y en el tiempo. Nunca por persona |
| `referencia.py` | Servicios | La referencia para leer y probar en `/referencia`, con Scalar: ordena el OpenAPI en grupos, declara el login y la clave del equipo, y suma los errores y los ejemplos de `app/referencia_ejemplos.json`. Una ruta nueva necesita su grupo, o `tests/test_referencia.py` falla. La revisión contra los estándares está en [API](../knowledge/architecture/API.md) |
| `estatico/camara.html` · `estatico/monitor.html` | Servicios | El celular como cámara del edge, y la OT en vivo con video, avisos y bitácora |
| `estatico/simulador.html` | Servicios | El simulador en `/simulador`: la ejecución de una OT en 3D con las pautas y los operarios de la base, con OT simuladas que no se escriben. Un solo archivo, sin build; el motor de la página copia las reglas de `servicios.py`. Qué es real y qué no, en [SIMULADOR](../knowledge/architecture/SIMULADOR.md) |
| `estatico/casos.html` | Servicios | El banco de pruebas en `/casos`: una tarjeta por criterio del [PRD](../knowledge/projects/servicios-en-vivo/PRD.md), que corre su secuencia real contra el servidor elegido (local o la VM) con una OT y un edge propios, y muestra cada llamada y el stream en vivo |
| `../deploy/vm/` | Servicios | El servidor del demo: `deploy/vm/desplegar.sh` sube la rama actual a la VM sin borrar la bitácora y carga la semilla, que no toca lo que ya existe. Con `SEMILLA=sin-historia` en `/srv/factum/entorno` (la VM, desde el 2026-11-22), `instalar.sh` la corre con `--sin-historia`: sin OT de ejemplo ni pautas habilitadas, que Factum habilita a mano |
| `verificacion.py` | Frente 3 | Capa 3 de cámara con Claude Haiku 5.5 (`ANTHROPIC_API_KEY`; en la VM va en `/srv/factum/entorno`; modelo en `VLM_MODELO`; sin key queda el stub). La capa 2 de cámara (YOLO del edge) está en `reglas.por_deteccion` |
| `cerebro.py` | Frente 4 | El relevo (`redactar_resumen`) y las preguntas (`responder`) los redacta Claude Opus 5.5 con el registro completo (`ANTHROPIC_API_KEY`; modelo en `CEREBRO_MODELO`, tope en `CEREBRO_MAX_LLAMADAS`). Cada frase cita sus eventos y el código lo comprueba: si cita uno que no existe, calla un paso en conflicto o una alerta, queda el texto del código |
| `analisis.py` + `scripts/analizar.py` | Servicios | Lo que se comprueba de una pauta sin modelo: contrato, citas del protocolo, factibilidad contra una estación (`datos/estaciones/`), historia de sus OT y el criterio de qué vale la pena analizar. Lo usan las skills de `.claude/skills/` ([ADR-0015](../knowledge/decisions/0015-reconocer-procesos-con-skills-de-agente-y-un-criterio.md)) |
| `detector.py` | Servicios | YOLO en el servidor (ONNX + onnxruntime), el modo de detección por defecto |

## Dónde corre YOLO: dos modos

Las detecciones (clase, confianza y caja) entran siempre por `servicios.recibir_detecciones`, así que la capa 2, el monitor y la bitácora no cambian según el modo.

| Modo | Cómo se activa | Detecciones/s | Cuándo conviene |
|---|---|---|---|
| **Servidor** (por defecto) | `DETECTOR_ONNX` apunta a un `.onnx` (la VM lo trae en `deploy/vm/instalar.sh`) y el edge corre con `--deteccion servidor` (`edge/correr_edge_vm.command`) | ~5 en la VM `e2-standard-2` con el modelo de 416 px | El edge no puede correr modelos, o se quiere un solo modelo para todos los edges |
| **Edge** | `DETECTOR_ONNX=` vacío en `/srv/factum/entorno` y el edge con `--deteccion edge` (`edge/correr_edge_vm_yolo_local.command`) | ~18 en el Mac | El edge tiene CPU/GPU: más rápido, más preciso y no carga la VM |

- Con el detector del servidor activo, las detecciones que mande un edge se ignoran, para no mezclar dos modelos.
- **El detector busca lo que pide la pauta, además de sus clases de siempre.** En modo edge, el edge pregunta cada 2 s `GET /edge/{id}/clases` (las `deteccion.clase` de la pauta de la OT en sesión) y, si alguna no está entre las de `--clases`, arma el modelo de nuevo con ella. En modo servidor las clases quedan fijas al exportar: la misma ruta dice en `detector_no_conoce` cuáles le faltan, y hay que exportar de nuevo.
- **Un detector que no busca una clase no puede decir que el objeto ya no está.** Cada detección lleva las `clases` que el modelo buscaba, y la capa 2 solo cierra un paso `presente: false` si la clase está ahí; si no, decide el VLM cuando el operario declara.
- **Un reemplazo pide ver el repuesto.** Un paso `presente: false` puede llevar `en_su_lugar` con otra clase: se cierra cuando la primera ya no se ve y la segunda se ve con 80 % o más en toda la ventana. Sin eso, tapar la cámara cierra el paso. No cuenta objetos: con otra lata de esa clase ya a la vista, basta con sacar la primera.
- Los modelos se exportan con `edge/exportar_onnx.py --lado 416` (clases por defecto: mouse y pencil para LOTO; soda can y red soda can para los polines, que en la estación son latas; se suman las que pidan las pautas de `datos/pauta-*.json` o de `--pautas`) a `datos/modelos/` (no van al repo) y `desplegar.sh` los sube si faltan en la VM. A 416 px el lápiz baja de 0,87 a ~0,67 de confianza frente a 640 px: un paso de cámara que no llega al 80 % se cierra declarando (capa 3).
- Con ~5 detecciones/s, la ventana de la capa 2 va en `VENTANA_DETECCION_S=1.5` para juntar las 5 que pide.

## El banco de pruebas

`/casos` corre cada criterio de aceptación contra un servidor de verdad. Un criterio nuevo entra primero al PRD y a `tests/`, después al código y después a su tarjeta en `casos.html`; `tests/test_casos.py` falla si falta la tarjeta. Tres cosas que conviene saber antes de apuntarlo a la VM:

- Cada corrida deja su OT (`casos-…`) en el servidor, porque la bitácora solo agrega. Su sesión se termina y los sensores vuelven a como estaban.
- Los sensores son una tabla global: si el servidor tiene una OT en sesión que no es del banco, la página lo avisa y pide confirmación, y `scripts/correr_casos.py` exige `--con-sesiones-ajenas`.
- El caso de cámara usa un JPEG generado en el navegador, o la cámara real abriendo `/camara?edge=<el edge de la corrida>`.

Debajo de los CA está la matriz de **escenarios por industria** ([PRD](../knowledge/projects/escenarios-por-industria/PRD.md)): 24 patrones de ejecución en minería, eléctrica y construcción, contra la barrera que los decide. Sus casos de uso, con las palabras de cada oficio, están en `tests/test_mineria.py`, `tests/test_electrica.py` y `tests/test_construccion.py`. Al final de `/casos` hay una sección por industria: su trasfondo, su pauta y la arquitectura por la que pasa cada uno de esos tests (`/casos?correr=mineria&test=B2` abre uno directo). Corren en una caja aislada del servidor, así que se pueden correr en la VM sin tocar nada. Un escenario nuevo entra en `escenarios.py`; si lo que espera el producto todavía no pasa, lleva `brecha` con la razón, y `tests/test_escenarios.py` avisa cuando alguien la cierra.

## Una OT real en la estación del demo

El monitor (`/`) ejecuta las OT del dominio de negocio:

1. **Elegirla.** «OT abiertas» lista las OT que existen y no han terminado (`GET /ots`), primero las que ya tienen operador. También se puede escribir el id o entrar con `/?ot=ot-1017`; `OT-1017` y `ot-1017` son la misma.
2. **Leerla.** `GET /ot/{id}/ficha` trae lo que hace falta para ejecutarla: la empresa, quién la pidió, el operador que la tiene, los protocolos de los que sale y cada paso de su pauta con su instrucción y lo que lo cierra, en la versión que la OT ejecuta. El monitor lo muestra sobre el video, y el paso en curso lleva su instrucción. Sin la clave del equipo (donde el servidor la pide) no salen la empresa ni los nombres. El operador la lee con su token en `GET /cliente/ots/{id}/ficha`.
3. **Ejecutarla.** «Ejecutar en <edge>» une la OT a la estación a nombre de su operador (`POST /ot/{id}/sesion`), y «Declarar paso» declara a su nombre. Una OT sin operador no se ejecuta: primero la asigna su supervisor. Si la estación ejecuta otra OT sin terminar, el monitor pregunta antes de quitársela.

La semilla deja tres OT de la pauta de la estación listas para esto: `ot-1017` y `ot-1019`, la del demo, asignadas a `operario:1` (Ana Rojas), y `ot-1018` a `operario:2` (Bruno Díaz), todas pedidas por `supervisor:oculta` (Carla Muñoz). En la VM esas tres ids son las personas del equipo; con `--sin-historia` la semilla no las crea.

**«Nueva demo» también abre una OT del negocio**, para repetir el demo: `POST /interno/ots` la pide a nombre del supervisor de Oculta, la asigna a su primer operador (`operario:1`) y el monitor la une a la estación. En la bitácora queda pedida por `supervisor:oculta`, aunque el botón lo aprieta el equipo. Una OT la asigna solo un supervisor: si el actor es una persona de la base tiene que tener ese rol, y si no lo es, su id tiene que ser `supervisor` o `supervisor:<algo>`; si no, 409. Necesita la semilla cargada: sin esas personas responde 404. La pauta que ejecuta es la última aprobada en la base, así que una versión nueva de `datos/pauta-*.json` entra al repetir la semilla. `deploy/vm/desplegar.sh` la carga en cada despliegue; en local, `uv run python -m app.semilla` o `POST /interno/ots/semilla`.

## La clave del equipo

La API es pública. Con `CLAVE_EQUIPO` en el entorno del servidor, quitarle un edge a la OT que ejecuta (`POST /ot/{id}/sesion`) o soltarlo (`DELETE /edge/{id}/sesion`) pide la cabecera `X-Clave-Equipo`, y sin ella el home queda de solo lectura. Se entra una vez con `/?clave=...` y queda en el navegador; el banco la toma de `?clave=` y `scripts/correr_casos.py`, de `--clave`. Un operador de un cliente no la necesita: une su OT a una estación con su token en `POST /cliente/ots/{id}/sesion`, y para quitársela a otra OT abierta lo pide con `tomar` ([ADR-0012](../knowledge/decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md)). La interfaz (`web/`) usa esa ruta y nunca lleva la clave. Sin la variable todo queda abierto, como en local. `GET /clave` dice si el servidor la pide: conviene mirarlo después de cada despliegue.

**No se tocan sin avisar:** `contratos.py` y `reglas.py` — son el contrato entre
los cuatro, y `tests/test_reglas.py` los vigila.
