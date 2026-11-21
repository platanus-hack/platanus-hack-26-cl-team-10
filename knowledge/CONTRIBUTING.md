# Cómo se contribuye

Estándar · knowledge · versión 2026-09-25.

## El estándar

1. **Enlazar, no duplicar.** El knowledge es el vestíbulo; el detalle técnico vive junto al código y se enlaza.
2. **Qué va dónde.** Si cambia cuando cambia el código, va junto al código y en el mismo commit. Si es dominio, arquitectura o una decisión estructural, va al knowledge. En la duda, gana el código.
3. **Nada se afirma sin origen.** Toda cifra o regla lleva su fuente y su estado (`Confirmada`, `Candidata a validar` o `Brecha`).
4. **El diseño va antes que el código y queda escrito.** Si al implementar aparece una decisión que el diseño no cubría, se escribe un ADR corto y se sigue.
5. **Un ADR `proposed` no se asume.** Lo que depende de él no se construye hasta que el equipo lo acepte.
6. **Cero secretos y cero datos personales versionados.** El repo es público.

Formato: Markdown GFM, enlaces relativos, fechas ISO 8601, documentos en español y commits en inglés. Los nombres van en `UPPER_SNAKE_CASE.md` para referencia y en `kebab-case.md` para narrativos.

## Adaptaciones de este equipo

- **Sin Linear.** El estado vivo vive **solo** en [SEGUIMIENTO](./roadmap/SEGUIMIENTO.md). Ningún otro documento repite avance.
- **Cada uno sube su research sin pisar al otro.** Un paper leído completo es una nota nueva en `projects/research/notas/`, con la [plantilla](./_TEMPLATE/nota-paper.md). Una referencia nueva se agrega al final de su grupo en [REFERENCIAS](./projects/research/REFERENCIAS.md) con el número siguiente; los números existentes no se reordenan, porque el flujo y el board los citan.
- **Un dueño por archivo a la vez.** Para editar el documento que otro tiene en curso, primero se le avisa.
- **Leer antes de citar.** Si solo leíste el resumen, dilo en la referencia. Lo que vaya a una lámina del pitch se abre desde su enlace antes.
