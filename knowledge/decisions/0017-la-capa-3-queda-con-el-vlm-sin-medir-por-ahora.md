# ADR-0017 — La capa 3 queda con el VLM y sin medir por ahora; sabemos cómo bajarle el peso

> Estado: `accepted` · Fecha: 2026-11-21

## Contexto

En las corridas de la maqueta en la VM, el 20 y 21 de noviembre, la cámara juzgó 43 pasos y guardó la foto de cada juicio en `datos/evidencias/` de la VM: 36 los cerró el detector de capa 2 (YOLO) y 7 los juzgó el VLM de capa 3 (Claude Haiku 5.5). Los 7 del VLM respondieron «no» en el paso `e4` de `pauta-polin-estacion`, con 95 % a 97 % de confianza. En la OT `ot-1019` el operario declaró el paso cinco veces en siete minutos y nunca se cerró.

No sabemos si esos «no» fueron correctos, porque nadie miró las fotos. Tampoco sabemos cuántas veces el detector dijo «sí» sin que el objeto estuviera. Los 24 casos del eval de capa 3 (`datos/evals/capa3/casos.jsonl`) no tienen imagen. Es la pregunta de falsos positivos que el jurado hace siempre ([tour-platanus](../projects/research/tour-platanus.md), el caso Veridian).

## Decisión

Por ahora no etiquetamos las fotos ni cargamos otros modelos. La capa 3 sigue con el VLM tal como está, por comodidad y por tiempo. Queda escrito que lo sabemos y que no está medido.

Las salidas que existen para depender menos del VLM, en el orden en que conviene probarlas (es el de la skill [`solucion-vision`](../../.claude/skills/solucion-vision/SKILL.md)):

1. **Medir antes de cambiar.** Etiquetar a mano las 43 fotos ya guardadas: qué se ve de verdad en cada una. Cruzarlo con lo que respondió el sistema da la matriz de confusión de capa 2 y capa 3 con datos reales, y el número de falsos positivos. Es media hora de una persona.
2. **Reescribir la pregunta** al VLM y volver a medir con los mismos casos. La skill lo pide antes de pensar en otro modelo.
3. **Cargar las clases que pide la pauta en el detector de vocabulario abierto.** Ya está construido: el edge pregunta `GET /edge/{id}/clases` y busca lo que pide la OT en sesión. Un paso de «el objeto está» o «ya no está» que hoy cierra el VLM puede pasar a capa 2 con `deteccion` en la pauta.
4. **Probar otro detector de vocabulario abierto** cuando YOLO-World no llega a los umbrales de `reglas.por_deteccion` (0,8 para «está», 0,25 para «ya no está»).
5. **Un detector entrenado** con las fotos de `datos/evidencias/`, solo si la historia lo pide y los pasos anteriores se midieron y no alcanzan. No hay script de entrenamiento en el repo.

## Alternativas consideradas

- **A — Etiquetar ahora y medir:** es lo que responde al jurado con un número propio. No se hace por tiempo; es la primera opción cuando haya media hora.
- **B — Cambiar el VLM por un detector en todos los pasos de cámara:** sin medir no sabemos si el detector acierta más. Cambiar sin número es justo lo que esta decisión evita.

## Consecuencias

- En el demo, `e4` y `e5` los cierra el detector cuando ve la lata roja. Si el VLM tiene que decidir, puede negarse como en `ot-1019`.
- Al jurado se le dice que la capa 3 no está medida, qué fotos hay para medirla y cuál es el orden para bajarle el peso. No se inventa una tasa.

## Pendientes y no verificado

- Si los 7 «no» del VLM fueron aciertos o errores. `Brecha`.
- La tasa de falsos positivos del detector con objetos reales. `Brecha`.

## Referencias

- [ADR-0004](./0004-verificacion-por-capas.md): las tres capas. [ADR-0015](./0015-reconocer-procesos-con-skills-de-agente-y-un-criterio.md): el detector sigue las clases de la pauta.
- `scripts/evaluar_capa3.py`, `datos/evals/capa3/casos.jsonl`, `app/verificacion.py`, `app/reglas.py` (`por_deteccion`).
