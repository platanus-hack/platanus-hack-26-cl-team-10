# El esqueleto

Implementa [LOGICA.md](../knowledge/architecture/LOGICA.md). Correr:

```bash
uv run uvicorn app.api:app --reload   # la UI de ensayo queda en http://localhost:8000
python3 -m unittest discover tests    # reglas, calificación y servicios, sin dependencias
uv run --with httpx python -m unittest discover tests   # además el WebSocket de punta a punta
python3 scripts/recorrido_demo.py     # los cinco momentos del demo, de punta a punta
uv run python scripts/correr_casos.py http://localhost:8000   # el banco /casos en Chrome sin ventana: cuántos casos pasan
python3 scripts/simular_capa2.py      # capa 2: qué detector aguanta qué falla, por industria (señales sintéticas)
python3 scripts/evaluar_capa3.py      # capa 3: falsa aceptación y falso rechazo del juez de cámara
```

## Quién toca qué

| Archivo | Dueño | Qué reemplaza |
|---|---|---|
| `protocolos.py` | Frente 1 | `extraer_pasos`: PDF → pasos. Hoy devuelve `datos/pauta-correa.json` |
| `api.py` + `estatico/` | Frente 2 | La UI de ensayo por la app del operario con voz |
| `servicios.py` + `bus.py` | Servicios | Atribuye lo del edge a la OT de la sesión y lo reparte por `/ot/{id}/stream` ([ADR-0007](../knowledge/decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md)) |
| `scoring.py` | Servicios | La calificación ok · warning · error con certeza y motivos, por capa |
| `catalogo.py` | Servicios | El CRUD de pautas, aprobaciones, OT y eventos, con las reglas de negocio como 409 |
| `video.py` | Servicios | El video del edge: entra por `WS /edge/{id}/video`, sale como MJPEG y le da al juez de cámara el último cuadro |
| `escenarios.py` | Servicios | La matriz de industria × patrón de ejecución contra cada barrera, en una caja aislada ([ADR-0008](../knowledge/decisions/0008-escenarios-por-industria-en-una-caja-aislada.md)). Las pautas de eléctrica y construcción están en `datos/` |
| `guia.py` | Servicios | La guía para agentes en `/agente`, con el catálogo de endpoints armado desde las rutas |
| `estatico/camara.html` · `estatico/monitor.html` | Servicios | El celular como cámara del edge, y la OT en vivo con video, avisos y bitácora |
| `estatico/casos.html` | Servicios | El banco de pruebas en `/casos`: una tarjeta por criterio del [PRD](../knowledge/projects/servicios-en-vivo/PRD.md), que corre su secuencia real contra el servidor elegido (local o la VM) con una OT y un edge propios, y muestra cada llamada y el stream en vivo |
| `../deploy/vm/` | Servicios | El servidor del demo: `deploy/vm/desplegar.sh` sube la rama actual a la VM sin borrar la bitácora |
| `verificacion.py` | Frente 3 | Capa 3 de cámara con Claude Haiku 5.5 (`ANTHROPIC_API_KEY`; en la VM va en `/srv/factum/entorno`; modelo en `VLM_MODELO`; sin key queda el stub). La capa 2 de cámara (YOLO del edge) está en `reglas.por_deteccion` |
| `cerebro.py` | Frente 4 | `redactar_resumen` y `responder` por el modelo, con el registro completo |

## El banco de pruebas

`/casos` corre cada criterio de aceptación contra un servidor de verdad. Un criterio nuevo entra primero al PRD y a `tests/`, después al código y después a su tarjeta en `casos.html`; `tests/test_casos.py` falla si falta la tarjeta. Tres cosas que conviene saber antes de apuntarlo a la VM:

- Cada corrida deja su OT (`casos-…`) en el servidor, porque la bitácora solo agrega. Su sesión se termina y los sensores vuelven a como estaban.
- Los sensores son una tabla global: si el servidor tiene una OT en sesión que no es del banco, la página lo avisa y pide confirmación, y `scripts/correr_casos.py` exige `--con-sesiones-ajenas`.
- El caso de cámara usa un JPEG generado en el navegador, o la cámara real abriendo `/camara?edge=<el edge de la corrida>`.

Debajo de los CA está la matriz de **escenarios por industria** ([PRD](../knowledge/projects/escenarios-por-industria/PRD.md)): 24 patrones de ejecución en minería, eléctrica y construcción, contra la barrera que los decide. Sus casos de uso, con las palabras de cada oficio, están en `tests/test_mineria.py`, `tests/test_electrica.py` y `tests/test_construccion.py`. Al final de `/casos` hay una sección por industria: su trasfondo, su pauta y la arquitectura por la que pasa cada uno de esos tests (`/casos?correr=mineria&test=B2` abre uno directo). Corren en una caja aislada del servidor, así que se pueden correr en la VM sin tocar nada. Un escenario nuevo entra en `escenarios.py`; si lo que espera el producto todavía no pasa, lleva `brecha` con la razón, y `tests/test_escenarios.py` avisa cuando alguien la cierra.

**No se tocan sin avisar:** `contratos.py` y `reglas.py` — son el contrato entre
los cuatro, y `tests/test_reglas.py` los vigila.
