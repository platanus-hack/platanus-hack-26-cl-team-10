# Seguimiento

> **El estado vivo del proyecto.** Único documento donde se escribe avance. Cada quien agrega y actualiza sus filas en el mismo commit que sube el trabajo. Estados: `pendiente` · `en curso` · `hecho` · `bloqueado`. Responsable `—` significa que nadie la tomó.

## Research

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Revisión bibliográfica en IEEE (117 papers) | Francisco | hecho | 2026-11-21. Hoja de NLP sobre OT en [fuentes/](../projects/research/fuentes/revision-ieee-42-papers.csv); la planilla completa la tiene Francisco |
| Intersección con la visión del operario y verificación de enlaces | Francisco | hecho | 2026-11-21. 37 referencias en [REFERENCIAS](../projects/research/REFERENCIAS.md) |
| Leer completo Sabetta et al. 2026 | Francisco | hecho | [Nota](../projects/research/notas/2026-sabetta-gemini-robotics-er.md). Originó el [ADR-0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md) |
| Pasar el planteamiento del equipo al knowledge | Francisco | hecho | 2026-11-21. [Transcripción íntegra](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md); entró a CONTEXTO, FLUJO, GLOSARIO y originó el [ADR-0004](../decisions/0004-verificacion-por-capas.md) |
| Alinear el knowledge con el planteamiento: producto general, OT desde el protocolo y predicción como visión | Francisco | hecho | 2026-11-21. [ADR-0005](../decisions/0005-producto-general-mineria-como-caso-del-demo.md), [ADR-0006](../decisions/0006-la-ot-nace-del-protocolo.md); cambiaron CONTEXTO, FLUJO y GLOSARIO |
| Costo por hora de detención de un equipo minero crítico | Francisco | en curso | Hay dos fuentes de prensa, (38) y (39): USD 100.000 a 300.000 por hora según un proveedor. Falta una fuente de operador, de Cochilco o de un estudio identificable antes de llevar la cifra al pitch |
| Subir las hojas «IEEE ampliado» (25) y «Fuera de IEEE» (50) de la planilla | Francisco | pendiente | Solo está la hoja «Papers» (42). Exportarlas a CSV en [fuentes/](../projects/research/fuentes/), idealmente con la columna de enlaces |
| Verificar las referencias mencionadas sin fuente | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#mencionadas-sin-verificar). Al verificarla, cada una recibe el número siguiente de su grupo |
| Leer completos los cinco prioritarios | — | pendiente | (20), (10), (15), (25) y (24); ver [research](../projects/research/research.md#qué-leer-primero) |
| Leer PREGO y TI-PREGO | — | pendiente | (11) y (12). Son la evidencia del aviso en el momento, y solo se leyó el resumen |
| Buscar literatura de relevo de turno en mantenimiento | — | pendiente | Sin búsqueda todavía. Punto de partida sin verificar: Piper Alpha |
| Buscar literatura del aviso por audio y de fatiga de alarmas | — | pendiente | Sin búsqueda todavía. Incluye si un auricular convive con la protección auditiva de una planta |
| Encontrar las seis referencias faltantes | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#no-encontradas). La de Bate, Orchard y Tagle es la más valiosa |
| Fatalidades y controles críticos: fuentes primarias de ICMM | Daniel | hecho | 2026-11-21. Referencias (40) a (43) y [research](../projects/research/research.md#fatalidades-y-controles-críticos). La ejecución inefectiva del control, 19 de 26 incidentes fatales, sostiene el criterio de impacto |
| Aislar los accidentes en tareas de mantenimiento | — | pendiente | Fuente primaria de Sernageomin, no prensa. Para el pitch ya no bloquea: el argumento pasa por la ejecución del control (40), no por la proporción de muertes en mantenimiento |
| Abrir el PDF del benchmarking de ICMM 2025 | — | pendiente | Enlazado desde (40) y no abierto. Es la fuente más completa si se necesita el detalle por peligro |
| Encontrar el origen de «ICMM cubre un tercio de la industria» | — | pendiente | Se afirmó al preparar el pitch y ninguna fuente abierta lo dice. Hasta entonces, fuera del pitch |
| Transcribir y analizar las presentaciones del último año | Francisco | hecho | 2026-11-21. Cinco videos y 332 preguntas del jurado en [tour-platanus](../projects/research/tour-platanus.md) |
| Cerrar las brechas del banco de preguntas del jurado | — | pendiente | Modelo de visión, dónde corre, latencia, privacidad del operario, costo del kit y condiciones de faena. Ver [preguntas](../projects/research/tour-platanus.md#las-preguntas-que-nos-van-a-hacer) |
| Medir falsos positivos, falsos negativos y latencia del aviso | — | pendiente | Con el número de corridas. Es la pregunta que más le pesó a Veridian en Caracas |
| Ensayar pitch de 3 min y preguntas de 2 min | Equipo | pendiente | Con alguien que haga de jurado y las preguntas de [tour-platanus](../projects/research/tour-platanus.md#las-preguntas-que-nos-van-a-hacer) |
| Preguntar qué espera el jurado del track Physical World | — | pendiente | Ninguna edición anterior tuvo ese track |

## Decisiones abiertas

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Aceptar o rechazar los ADR 0002 a 0006 y la decisión de dejar la predicción como visión | Equipo | pendiente | Ver el [registro](../decisions/decisions.md). El 0001 quedó reemplazado por el 0005 |
| ¿Hay hardware a mano para el demo? | Equipo | hecho | Sí: Arduino, Raspberry Pi, ESP, sensores, receptores y motores ([planteamiento](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md)) |
| ¿El demo es la correa a escala con el bloqueo saltado? | Equipo | pendiente | Ver [Demo propuesto](../architecture/FLUJO.md#demo-propuesto). Define qué sensores se montan |
| ¿La predicción de fallas y la OT automática siguen en el alcance del demo? | Francisco | hecho | 2026-11-21. No: quedan como visión ([registro](../decisions/decisions.md)). Falta que el equipo la acepte |
| Formato del relevo de turno | Equipo | pendiente | Resumen, consultas o *briefing* |
| Canal del aviso al operario | Equipo | pendiente | El equipo propone un auricular. Confirmar qué dispositivo es «la muela» de la transcripción |
| Algoritmo de la capa de aprendizaje automático | Equipo | pendiente | Para el demo basta un umbral ([ADR-0004](../decisions/0004-verificacion-por-capas.md)) |
| ¿Hay OT reales de alguna faena? | — | pendiente | Sin ellas, el corpus sale de MaintIE (6) |
