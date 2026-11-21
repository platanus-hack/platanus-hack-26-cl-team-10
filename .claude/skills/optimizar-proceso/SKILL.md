---
name: optimizar-proceso
description: Analiza cómo se ejecutó una pauta en sus órdenes de trabajo (conflictos, cierres por persona, alertas y tiempos por paso, y las fotos o el video de los pasos que lo ameriten) y propone la versión siguiente de la pauta. Úsala cuando pidan mejora continua, optimizar un proceso, ver dónde se saltan pasos, por qué una pauta se demora, o revisar la historia de una pauta.
---

# Optimizar un proceso

Sale una **propuesta**: un borrador con la versión siguiente de la pauta y la razón de cada cambio. La aprueba o la rechaza el supervisor ([LOGICA](../../../knowledge/architecture/LOGICA.md#cuándo-el-sistema-propone-cambiar-la-pauta)).

## 1. Mirar los números

```bash
uv run python scripts/analizar.py ejecuciones [--pauta <id>] [--db <bitácora.sqlite3>]
```

Una tabla por versión de cada pauta, y debajo lo que el criterio pide mirar.

Contra un servidor, y no contra una base local, lo mismo sale de la API con la clave del equipo (`X-Clave-Equipo`): `GET /interno/mejoras` da las propuestas que los supervisores aceptaron, con las OT, las señales y las observaciones de cada paso ([ADR-0014](../../../knowledge/decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)). Las aceptadas son las primeras que se llevan a una versión nueva. Para un paso marcado, `GET /cliente/metricas/pautas/{pauta_id}/pasos` (con el login de un supervisor de esa empresa) da en qué capa cerró, con qué confianza, en cuántos intentos y cuánto tardó. **Si dice que hay menos OT que el mínimo, o que no hay nada que analizar, se termina acá**: díselo a la persona con la tabla. Una desviación suelta no es una propuesta, y buscarle una explicación es inventarla.

## 2. Leer las OT de cada paso marcado

Los números dicen dónde; el porqué está en la bitácora. Por cada paso que el criterio marcó, lee los eventos de las OT donde pasó (`GET /ot/{id}/eventos`, o la tabla `eventos`): qué declaró el operario, qué marcaba el sensor, cuánto tardó.

## 3. Mirar, solo en esos pasos

La bitácora ve cuándo se cerró un paso, no lo que pasó adentro: qué buscó el operario, dónde esperó, qué hizo distinto. Eso solo se ve. Mira imágenes únicamente de los pasos marcados; mirar todo es caro y no cambia nada.

- **Las fotos de evidencia.** Cada veredicto de cámara guarda el cuadro que juzgó: su ruta está en `evidencia.cuadro` del evento y el archivo en `datos/evidencias/`. Compara las de las OT donde el paso salió bien con las de donde no.
- **Una grabación de la ejecución, si alguien la hizo.** El sistema no graba: guarda los últimos 10 segundos y la foto de cada veredicto. Si hay un video de la OT, saca cuadros y mira el tramo entre el cierre del paso anterior y el de este (las horas están en la bitácora):

```bash
uv run python scripts/analizar.py cuadros <video> --cada 2
```

Si un paso está marcado por lento o por cierres por persona y no hay fotos ni video, dilo y pide que se grabe una ejecución: es mejor que adivinar. Las imágenes muestran personas: no salen de `datos/`, que no se versiona, y no se describen por nombre.

## 4. Decidir de qué es síntoma

| Lo que se repite | Suele ser | Qué se propone |
|---|---|---|
| Conflicto en el mismo paso | La instrucción no dice cuándo el paso está hecho, o el operario declara antes de terminar | Reescribir `titulo` e `instruccion` |
| Cierre por persona contra el sensor | El sensor falla o está mal montado | No se cambia la pauta: se avisa que hay que revisar el sensor |
| Cierre por persona en un paso de cámara | La cámara no ve el resultado, o la pregunta es ambigua | Skill `solucion-vision` |
| Alerta de orden invertido | El orden de la pauta no calza con cómo se hace el trabajo | Revisar el orden **con quien hace la tarea**, nunca solo |
| Un paso se lleva gran parte del tiempo | Espera (coordinación, enfriamiento) o un paso que son varios | Separarlo, o mover la espera para que no bloquee |

## 5. Lo que no se propone nunca

- **Quitar o relajar un control crítico porque se salta seguido.** Que se repita dice que la pauta está mal escrita o es impracticable, no que el paso sobre.
- **Nombrar personas.** El análisis cuenta OT y agrupa por pauta. Si alguien pide el detalle por operario, recuérdale que usar el dato para vigilar aumenta la presión que causa las desviaciones (REFERENCIAS 33).
- **Cambiar el orden de aislar, bloquear y probar.**

## 6. Escribir la propuesta

Un borrador en `datos/borradores/<pauta-id>-v<n+1>.json`, con la forma de la skill `reconocer-proceso`: la pauta completa con `version` siguiente, y en `analisis.cambios` una entrada por cambio: `{"paso", "antes", "despues", "porque", "ots"}`, donde `ots` son las órdenes que lo respaldan. Compruébalo:

```bash
uv run python scripts/analizar.py pauta datos/borradores/<pauta-id>-v<n+1>.json --estacion datos/estaciones/<estación>.json
```

Contra un servidor, `POST /interno/pautas/validar` corre las mismas comprobaciones sobre la pauta nueva sin guardarla.

Entrega la tabla, los cambios con sus OT y lo que **no** propusiste y por qué. No cargues ni apruebes la versión nueva: eso lo pide el supervisor.
