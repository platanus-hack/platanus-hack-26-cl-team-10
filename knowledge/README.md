# Qué es este knowledge

Estándar · knowledge · versión 2026-09-25, adaptado al equipo 10 de Platanus Hack 26 el 2026-11-21.

Este directorio es la cadena de conocimiento del proyecto. Guarda lo que no cambia cuando cambia el código: el problema, la evidencia que lo respalda, las decisiones y de dónde salen, y en qué va cada frente. Lo lee cualquier integrante, o un agente, antes de tomar una tarea.

En qué va cada frente está en [SEGUIMIENTO](./roadmap/SEGUIMIENTO.md), y solo ahí. El research de cada integrante va a `projects/research/`.

## Cómo leerlo

1. [INDEX](./INDEX.md) es la entrada.
2. [CONTEXTO](./domain/CONTEXTO.md) dice qué problema resolvemos y cómo nos evalúan.
3. [FLUJO](./architecture/FLUJO.md) dice cómo funciona la solución, paso a paso.
4. [LOGICA](./architecture/LOGICA.md) dice las reglas de negocio que el código implementa.
5. [research](./projects/research/research.md) dice qué encontramos y qué falta.
6. Si algo de acá contradice al código, manda el código, y el documento se corrige en el mismo commit.

## Dos modos de documento

- **Vivos**, con nombre fijo, se editan a medida que crecen: `CONTEXTO`, `GLOSARIO`, `FLUJO`, `LOGICA`, `REFERENCIAS` y `SEGUIMIENTO`.
- **Inmutables**: los ADR numerados y las notas de lectura de cada paper. Si algo cambia, se escribe otro que los reemplaza.

## Estado de validación

Cada afirmación, cifra o regla lleva su fuente y uno de tres estados:

- `Confirmada`: la sostiene una fuente verificada o la acordó el equipo.
- `Candidata a validar`: la propuso alguien y todavía no se acuerda o no se verifica.
- `Brecha`: falta el dato o la decisión, y se dice.
