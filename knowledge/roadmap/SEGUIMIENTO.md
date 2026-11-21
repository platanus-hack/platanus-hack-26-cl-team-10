# Seguimiento

> **El estado vivo del proyecto.** Único documento donde se escribe avance. Cada quien agrega y actualiza sus filas en el mismo commit que sube el trabajo. Estados: `pendiente` · `en curso` · `hecho` · `bloqueado`. Responsable `—` significa que nadie la tomó.

## Research

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Revisión bibliográfica en IEEE (117 papers) | Francisco | hecho | 2026-11-21. Hoja de NLP sobre OT en [fuentes/](../projects/research/fuentes/revision-ieee-42-papers.csv); la planilla completa la tiene Francisco |
| Intersección con la visión del operario y verificación de enlaces | Francisco | hecho | 2026-11-21. 37 referencias en [REFERENCIAS](../projects/research/REFERENCIAS.md) |
| Leer completo Sabetta et al. 2026 | Francisco | hecho | [Nota](../projects/research/notas/2026-sabetta-gemini-robotics-er.md). Originó el [ADR-0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md) |
| Subir las hojas «IEEE ampliado» (25) y «Fuera de IEEE» (50) de la planilla | Francisco | pendiente | Solo está la hoja «Papers» (42). Exportarlas a CSV en [fuentes/](../projects/research/fuentes/), idealmente con la columna de enlaces |
| Verificar las referencias mencionadas sin fuente | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#mencionadas-sin-verificar). Al verificarla, cada una recibe el número siguiente de su grupo |
| Leer completos los cinco prioritarios | — | pendiente | (20), (10), (15), (25) y (24); ver [research](../projects/research/research.md#qué-leer-primero) |
| Encontrar las seis referencias faltantes | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#no-encontradas). La de Bate, Orchard y Tagle es la más valiosa |
| Aislar los accidentes en tareas de mantenimiento | — | pendiente | Fuente primaria de Sernageomin, no prensa |
| Costo por hora de detención de un equipo minero crítico | — | pendiente | Con fuente, para el criterio de impacto |

## Decisiones abiertas

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Aceptar o rechazar los ADR 0001 a 0003 | Equipo | pendiente | Ver el [registro](../decisions/decisions.md) |
| ¿Hay hardware a mano para el demo? | — | pendiente | Define si el demo va sobre un equipo físico o telemetría simulada ([Demo propuesto](../architecture/FLUJO.md#demo-propuesto)) |
| ¿Hay OT reales de alguna faena? | — | pendiente | Sin ellas, el corpus sale de MaintIE (6) |
