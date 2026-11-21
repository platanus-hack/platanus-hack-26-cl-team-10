---
name: regla-programatica
description: Convierte un peligro que un protocolo describe con lecturas de sensores («lo que no puede pasar») en una regla de seguridad de capa 1 en el código, con su test y su documentación. Úsala cuando el análisis de una pauta pida `regla-programatica`, o cuando pidan agregar una regla de seguridad, una alerta o una condición programática.
---

# Escribir una regla programática

## Primero: ¿hace falta código?

Casi nunca. Estas reglas ya son genéricas y valen para cualquier pauta sin tocar nada:

| Lo que se quiere | Cómo se consigue |
|---|---|
| Que un paso no se cierre sin su evidencia | `tipo_evidencia` y `sensor` del paso |
| Que avise si se salta un control | `control_critico: true` (alerta de orden invertido) |
| Que avise si se deshace un control antes de tiempo | `control_critico: true` (alerta de control perdido) |
| Que una señal numérica rara avise | Nada: `scoring.capa2` la compara contra su historia |

Solo se escribe código para un **peligro que no depende del paso en curso**: una combinación de lecturas que no puede darse nunca, vaya el operario donde vaya. Y solo si `scripts/analizar.py pauta` lo pidió: eso ya comprobó que ninguna regla existente dispara y que la estación tiene los sensores.

## Lo que una regla puede expresar

Igualdad entre estados discretos: `{"guarda": "abierta", "energia": "viva"}`. No hay rangos ni tiempos. Un umbral (temperatura sobre 60 °C) se vuelve estado en el edge, en `estados()` de `edge/edge.py`, y la regla compara el estado (`equipo = caliente`). Si el peligro necesita otra cosa (una duración, una secuencia), no entra acá: para y plantéalo, porque es un cambio de diseño.

## Qué se toca

1. `app/reglas.py`, tupla `_PELIGROS`: la condición, el aviso y la fuente. El aviso va en mayúsculas en su primera frase y dice qué hacer, como los que ya hay.
2. `tests/test_reglas.py`: que dispara con la condición, y que no dispara con cada sensor por separado.
3. [LOGICA.md](../../../knowledge/architecture/LOGICA.md), tabla de reglas que no dependen del paso: una fila, con la industria y el porqué.
4. Si es de una industria con escenarios, su escenario en `app/escenarios.py` ([PRD](../../../knowledge/projects/escenarios-por-industria/PRD.md)).

Después: `uv run python -m unittest discover tests`.

## Lo que no se salta

- **La fuente.** Nada se afirma sin origen: la norma, o la sección del protocolo del cliente que lo dice, literal. Sin fuente no hay regla.
- **Es una decisión de producto, y `reglas.py` es el contrato entre los frentes.** La regla va en su propio PR y se avisa al equipo. No la mezcles con otro cambio.
- **Una regla interrumpe al operario.** Si la condición puede darse en una ejecución correcta de alguna pauta (revisa las de `datos/`), la regla está mal: una alarma falsa repetida enseña a ignorar la alarma.
