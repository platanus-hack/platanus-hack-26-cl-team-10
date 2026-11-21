# ADR-0002 — La aplicación impone el orden de la pauta

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

El paso 4 del [FLUJO](../architecture/FLUJO.md#4-ejecutar-y-verificar) verifica con cámara que el operario ejecutó la pauta. La primera idea fue darle al VLM el video y la pauta, y que juzgara si coinciden.

Sabetta et al. (IEEE Access, 2026) midieron justo eso con Gemini Robotics-ER 1.5 sobre 12 videos de montaje manual:

| Caso | Resultado |
|---|---|
| Paso de la pauta que no aparece en el video (paso saltado) | Detectado en 12 de 12 |
| Pasos en otro orden | Detectado en 3 de 12 |
| Acción hecha fuera de la pauta | Detectada en 0 de 12 |
| Ejecución correcta | Rechazada en 5 de 12 |

Los autores concluyen que el modelo sirve para redactar y revisar pautas, pero no para verificar cumplimiento de forma autónoma.

## Decisión

**La aplicación impone el orden.** Presenta un paso a la vez y no avanza hasta cerrarlo. El VLM solo responde si el estado final visible de ese paso se cumple, por ejemplo si el candado está puesto. El operario confirma cada paso. Mientras no midamos nuestra propia tasa de falsas alarmas, el sistema avisa y no bloquea.

## Alternativas consideradas

- **A — El VLM juzga el video completo contra la pauta:** es lo más simple de construir, pero falla justo en el orden, que es lo que importa en el bloqueo.
- **B — Entrenar un detector de pasos propio:** más preciso por clase, pero necesita datos etiquetados que no tenemos. Si se usa YOLO de Ultralytics, la licencia AGPL-3.0 obliga a abrir el producto o a pagar la licencia Enterprise.

## Consecuencias

- El caso que mejor funciona, el paso saltado, queda al centro del demo.
- Cada pregunta al modelo es chica y verificable, y su respuesta queda como evidencia en la bitácora.
- Lo que la cámara no ve bien hoy (piezas chicas, herramientas parecidas, acciones que se leen solo en el tiempo) se cubre con la confirmación del operario.

## Pendientes y no verificado

- El estudio es de un solo modelo, cuatro montajes en mesa y cámaras fijas. No sabemos cómo rinde con una cámara en el pecho, en terreno. `Brecha`.
- Cómo comprobar el orden del bloqueo si dos pasos dejan el mismo estado visible. `Brecha`.

## Referencias

- REFERENCIAS 9 y su [nota de lectura](../projects/research/notas/2026-sabetta-gemini-robotics-er.md).
- REFERENCIAS 10, 11 y 15: verificación paso a paso y grafo de tarea.
