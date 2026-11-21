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
| `verificacion.py` | Frente 3 | `juez_camara` por el VLM real; el ESP32 escribe en `POST /sensores` |
| `cerebro.py` | Frente 4 | `redactar_resumen` y `responder` por el modelo, con el registro completo |

**No se tocan sin avisar:** `contratos.py` y `reglas.py` — son el contrato entre
los cuatro, y `tests/test_reglas.py` los vigila.
