# El esqueleto

Implementa [LOGICA.md](../knowledge/architecture/LOGICA.md). Correr:

```bash
uv run uvicorn app.api:app --reload   # la UI de ensayo queda en http://localhost:8000
python3 -m unittest discover tests    # reglas, calificación y servicios, sin dependencias
uv run --with httpx python -m unittest discover tests   # además el WebSocket de punta a punta
python3 scripts/recorrido_demo.py     # los cinco momentos del demo, de punta a punta
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
| `../deploy/vm/` | Servicios | El servidor del demo: `deploy/vm/desplegar.sh` sube la rama actual a la VM sin borrar la bitácora |
| `verificacion.py` | Frente 3 | Capa 3 de cámara con Gemini (`GEMINI_API_KEY`, modelo en `GEMINI_MODELO`; sin key queda el stub). La capa 2 de cámara (YOLO del edge) está en `reglas.por_deteccion` |
| `cerebro.py` | Frente 4 | `redactar_resumen` y `responder` por el modelo, con el registro completo |

**No se tocan sin avisar:** `contratos.py` y `reglas.py` — son el contrato entre
los cuatro, y `tests/test_reglas.py` los vigila.
