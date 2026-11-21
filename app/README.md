# El esqueleto

Implementa [LOGICA.md](../knowledge/architecture/LOGICA.md). Correr:

```bash
uv run uvicorn app.api:app --reload   # la UI de ensayo queda en http://localhost:8000
python3 -m unittest discover tests    # reglas, calificación y servicios, sin dependencias
uv run --with httpx python -m unittest discover tests   # además el WebSocket de punta a punta
python3 scripts/recorrido_demo.py     # los cinco momentos del demo, de punta a punta
uv run python scripts/correr_casos.py http://localhost:8000   # el banco /casos en Chrome sin ventana: cuántos casos pasan
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
| `guia.py` | Servicios | La guía para agentes en `/agente`, con el catálogo de endpoints armado desde las rutas |
| `estatico/camara.html` · `estatico/monitor.html` | Servicios | El celular como cámara del edge, y la OT en vivo con video, avisos y bitácora |
| `estatico/casos.html` | Servicios | El banco de pruebas en `/casos`: una tarjeta por criterio del [PRD](../knowledge/projects/servicios-en-vivo/PRD.md), que corre su secuencia real contra el servidor elegido (local o la VM) con una OT y un edge propios, y muestra cada llamada y el stream en vivo |
| `../deploy/vm/` | Servicios | El servidor del demo: `deploy/vm/desplegar.sh` sube la rama actual a la VM sin borrar la bitácora |
| `verificacion.py` | Frente 3 | `juez_camara` por el VLM real; el ESP32 escribe en `POST /sensores` |
| `cerebro.py` | Frente 4 | `redactar_resumen` y `responder` por el modelo, con el registro completo |

## El banco de pruebas

`/casos` corre cada criterio de aceptación contra un servidor de verdad. Un criterio nuevo entra primero al PRD y a `tests/`, después al código y después a su tarjeta en `casos.html`; `tests/test_casos.py` falla si falta la tarjeta. Tres cosas que conviene saber antes de apuntarlo a la VM:

- Cada corrida deja su OT (`casos-…`) en el servidor, porque la bitácora solo agrega. Su sesión se termina y los sensores vuelven a como estaban.
- Los sensores son una tabla global: si el servidor tiene una OT en sesión que no es del banco, la página lo avisa y pide confirmación, y `scripts/correr_casos.py` exige `--con-sesiones-ajenas`.
- El caso de cámara usa un JPEG generado en el navegador, o la cámara real abriendo `/camara?edge=<el edge de la corrida>`.

**No se tocan sin avisar:** `contratos.py` y `reglas.py` — son el contrato entre
los cuatro, y `tests/test_reglas.py` los vigila.
