# Seguimiento

> **El estado vivo del proyecto.** Único documento donde se escribe avance. Cada quien agrega y actualiza sus filas en el mismo commit que sube el trabajo. Estados: `pendiente` · `en curso` · `hecho` · `bloqueado`. Responsable `—` significa que nadie la tomó.

## Research

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Revisión bibliográfica en IEEE (117 papers) | Francisco | hecho | 2026-11-21. Hoja de NLP sobre OT en [fuentes/](../projects/research/fuentes/revision-ieee-42-papers.csv); la planilla completa la tiene Francisco |
| Intersección con la visión del operario y verificación de enlaces | Francisco | hecho | 2026-11-21. 37 referencias en [REFERENCIAS](../projects/research/REFERENCIAS.md) |
| Leer completo Sabetta et al. 2026 | Francisco | hecho | [Nota](../projects/research/notas/2026-sabetta-gemini-robotics-er.md). Originó el [ADR-0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md) |
| Pasar el planteamiento del equipo al knowledge | Francisco | hecho | 2026-11-21. [Transcripción íntegra](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md); entró a CONTEXTO, FLUJO, GLOSARIO y originó el [ADR-0004](../decisions/0004-verificacion-por-capas.md) |
| Costo por hora de detención de un equipo minero crítico | Francisco | en curso | Hay dos fuentes de prensa, (38) y (39): USD 100.000 a 300.000 por hora según un proveedor. Falta una fuente de operador, de Cochilco o de un estudio identificable antes de llevar la cifra al pitch |
| Subir las hojas «IEEE ampliado» (25) y «Fuera de IEEE» (50) de la planilla | Francisco | pendiente | Solo está la hoja «Papers» (42). Exportarlas a CSV en [fuentes/](../projects/research/fuentes/), idealmente con la columna de enlaces |
| Verificar las referencias mencionadas sin fuente | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#mencionadas-sin-verificar). Al verificarla, cada una recibe el número siguiente de su grupo |
| Leer completos los cinco prioritarios | — | pendiente | (20), (10), (15), (25) y (24); ver [research](../projects/research/research.md#qué-leer-primero) |
| Leer PREGO y TI-PREGO | — | pendiente | (11) y (12). Son la evidencia del aviso en el momento, y solo se leyó el resumen |
| Buscar literatura de relevo de turno en mantenimiento | — | pendiente | Sin búsqueda todavía. Punto de partida sin verificar: Piper Alpha |
| Buscar literatura del aviso por audio y de fatiga de alarmas | — | pendiente | Sin búsqueda todavía. Incluye si un auricular convive con la protección auditiva de una planta |
| Encontrar las seis referencias faltantes | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#no-encontradas). La de Bate, Orchard y Tagle es la más valiosa |
| Aislar los accidentes en tareas de mantenimiento | — | pendiente | Fuente primaria de Sernageomin, no prensa |

## Decisiones abiertas

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Aceptar o rechazar los ADR 0001 a 0004 | Equipo | pendiente | Ver el [registro](../decisions/decisions.md) |
| ¿Hay hardware a mano para el demo? | Equipo | hecho | Sí: Arduino, Raspberry Pi, ESP, sensores, receptores y motores ([planteamiento](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md)) |
| ¿El demo es la correa a escala con el bloqueo saltado? | Equipo | pendiente | Ver [Demo propuesto](../architecture/FLUJO.md#demo-propuesto). Define qué sensores se montan |
| ¿La predicción de fallas y la OT automática siguen en el alcance del demo? | Equipo | pendiente | El handoff original las incluye; el planteamiento del 2026-11-21 no las menciona ([CONTEXTO](../domain/CONTEXTO.md#la-visión)) |
| Formato del relevo de turno | Equipo | pendiente | Resumen, consultas o *briefing* |
| Canal del aviso al operario | Equipo | pendiente | El equipo propone un auricular. Confirmar qué dispositivo es «la muela» de la transcripción |
| Algoritmo de la capa de aprendizaje automático | Equipo | pendiente | Para el demo basta un umbral ([ADR-0004](../decisions/0004-verificacion-por-capas.md)) |
| ¿Hay OT reales de alguna faena? | — | pendiente | Sin ellas, el corpus sale de MaintIE (6) |
