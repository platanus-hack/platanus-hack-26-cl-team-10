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
```

## Quién toca qué

| Archivo | Dueño | Qué reemplaza |
|---|---|---|
| `protocolos.py` | Frente 1 | `extraer_pasos`: PDF → pasos. Hoy devuelve `datos/pauta-correa.json`. `cargar_semilla` carga los protocolos de `datos/protocolos.json` y les atribuye las pautas de `datos/` |
| `api.py` + `estatico/` | Frente 2 | La UI de ensayo por la app del operario con voz |
| `servicios.py` + `bus.py` | Servicios | Atribuye lo del edge a la OT de la sesión y lo reparte por `/ot/{id}/stream` ([ADR-0007](../knowledge/decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md)) |
| `scoring.py` | Servicios | La calificación ok · warning · error con certeza y motivos, por capa |
| `catalogo.py` | Servicios | El CRUD de pautas, aprobaciones, OT y eventos, con las reglas de negocio como 409. También el de protocolos y su atribución a pautas (`/interno/...`, con la clave del equipo) y las OT que pide un cliente (`/cliente/...`): [ADR-0011](../knowledge/decisions/0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md) |
| `video.py` | Servicios | El video del edge: entra por `WS /edge/{id}/video`, sale como MJPEG y le da al juez de cámara el último cuadro |
| `escenarios.py` | Servicios | La matriz de industria × patrón de ejecución contra cada barrera, en una caja aislada ([ADR-0008](../knowledge/decisions/0008-escenarios-por-industria-en-una-caja-aislada.md)). Las pautas de eléctrica y construcción están en `datos/` |
| `guia.py` | Servicios | La guía para agentes en `/agente`, con el catálogo de endpoints armado desde las rutas |
| `estatico/camara.html` · `estatico/monitor.html` | Servicios | El celular como cámara del edge, y la OT en vivo con video, avisos y bitácora |
| `estatico/casos.html` | Servicios | El banco de pruebas en `/casos`: una tarjeta por criterio del [PRD](../knowledge/projects/servicios-en-vivo/PRD.md), que corre su secuencia real contra el servidor elegido (local o la VM) con una OT y un edge propios, y muestra cada llamada y el stream en vivo |
| `../deploy/vm/` | Servicios | El servidor del demo: `deploy/vm/desplegar.sh` sube la rama actual a la VM sin borrar la bitácora |
| `verificacion.py` | Frente 3 | Capa 3 de cámara con Claude Haiku 5.5 (`ANTHROPIC_API_KEY`; en la VM va en `/srv/factum/entorno`; modelo en `VLM_MODELO`; sin key queda el stub). La capa 2 de cámara (YOLO del edge) está en `reglas.por_deteccion` |
| `cerebro.py` | Frente 4 | `redactar_resumen` y `responder` por el modelo, con el registro completo |
| `detector.py` | Servicios | YOLO en el servidor (ONNX + onnxruntime), el modo de detección por defecto |

## Dónde corre YOLO: dos modos

Las detecciones (clase, confianza y caja) entran siempre por `servicios.recibir_detecciones`, así que la capa 2, el monitor y la bitácora no cambian según el modo.

| Modo | Cómo se activa | Detecciones/s | Cuándo conviene |
|---|---|---|---|
| **Servidor** (por defecto) | `DETECTOR_ONNX` apunta a un `.onnx` (la VM lo trae en `deploy/vm/instalar.sh`) y el edge corre con `--deteccion servidor` (`edge/correr_edge_vm.command`) | ~5 en la VM `e2-standard-2` con el modelo de 416 px | El edge no puede correr modelos, o se quiere un solo modelo para todos los edges |
| **Edge** | `DETECTOR_ONNX=` vacío en `/srv/factum/entorno` y el edge con `--deteccion edge` (`edge/correr_edge_vm_yolo_local.command`) | ~18 en el Mac | El edge tiene CPU/GPU: más rápido, más preciso y no carga la VM |

- Con el detector del servidor activo, las detecciones que mande un edge se ignoran, para no mezclar dos modelos.
- Los modelos se exportan con `edge/exportar_onnx.py --clases mouse pencil --lado 416` a `datos/modelos/` (no van al repo) y `desplegar.sh` los sube si faltan en la VM. A 416 px el lápiz baja de 0,87 a ~0,67 de confianza frente a 640 px: un paso de cámara que no llega al 80 % se cierra declarando (capa 3).
- Con ~5 detecciones/s, la ventana de la capa 2 va en `VENTANA_DETECCION_S=1.5` para juntar las 5 que pide.

## El banco de pruebas

`/casos` corre cada criterio de aceptación contra un servidor de verdad. Un criterio nuevo entra primero al PRD y a `tests/`, después al código y después a su tarjeta en `casos.html`; `tests/test_casos.py` falla si falta la tarjeta. Tres cosas que conviene saber antes de apuntarlo a la VM:

- Cada corrida deja su OT (`casos-…`) en el servidor, porque la bitácora solo agrega. Su sesión se termina y los sensores vuelven a como estaban.
- Los sensores son una tabla global: si el servidor tiene una OT en sesión que no es del banco, la página lo avisa y pide confirmación, y `scripts/correr_casos.py` exige `--con-sesiones-ajenas`.
- El caso de cámara usa un JPEG generado en el navegador, o la cámara real abriendo `/camara?edge=<el edge de la corrida>`.

Debajo de los CA está la matriz de **escenarios por industria** ([PRD](../knowledge/projects/escenarios-por-industria/PRD.md)): 24 patrones de ejecución en minería, eléctrica y construcción, contra la barrera que los decide. Sus casos de uso, con las palabras de cada oficio, están en `tests/test_mineria.py`, `tests/test_electrica.py` y `tests/test_construccion.py`. Al final de `/casos` hay una sección por industria: su trasfondo, su pauta y la arquitectura por la que pasa cada uno de esos tests (`/casos?correr=mineria&test=B2` abre uno directo). Corren en una caja aislada del servidor, así que se pueden correr en la VM sin tocar nada. Un escenario nuevo entra en `escenarios.py`; si lo que espera el producto todavía no pasa, lleva `brecha` con la razón, y `tests/test_escenarios.py` avisa cuando alguien la cierra.

## La clave del equipo

La API es pública. Con `CLAVE_EQUIPO` en el entorno del servidor, quitarle un edge a la OT que ejecuta (`POST /ot/{id}/sesion`) o soltarlo (`DELETE /edge/{id}/sesion`) pide la cabecera `X-Clave-Equipo`, y sin ella el home queda de solo lectura. Se entra una vez con `/?clave=...` y queda en el navegador; el banco la toma de `?clave=` y `scripts/correr_casos.py`, de `--clave`. Sin la variable todo queda abierto, como en local. `GET /clave` dice si el servidor la pide: conviene mirarlo después de cada despliegue.

**No se tocan sin avisar:** `contratos.py` y `reglas.py` — son el contrato entre
los cuatro, y `tests/test_reglas.py` los vigila.
