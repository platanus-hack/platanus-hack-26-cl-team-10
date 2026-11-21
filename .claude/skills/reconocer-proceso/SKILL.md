---
name: reconocer-proceso
description: Convierte el protocolo de un cliente (texto, Markdown o PDF) o una ejecución grabada (video o fotos) en un borrador de pauta verificable, con sus pasos, puntos críticos, elementos y la evidencia que cierra cada paso, comprobado contra los sensores de la estación. Úsala cuando pidan cargar un protocolo, sacar la pauta de un procedimiento, desglosar un proceso paso a paso, o ver si una pauta se puede verificar con los sensores que hay.
---

# Reconocer un proceso

Sale un **borrador** en `datos/borradores/<id>.json`. Nunca una pauta aprobada: la aprueba una persona ([ADR-0003](../../../knowledge/decisions/0003-patrones-de-arquitectura-para-el-mvp.md)). No escribas en `datos/pauta-*.json`: la semilla aprueba sola todo lo que hay ahí.

Tu trabajo es leer y proponer. Lo que se puede comprobar no lo opinas: lo corre `scripts/analizar.py`.

## Qué necesitas

1. **La fuente.** El documento del cliente (si es PDF, léelo entero), o una grabación (ver [Desde una grabación](#desde-una-grabación)).
2. **La estación:** `datos/estaciones/<estación>.json`, con los sensores, sus valores, si hay cámara y qué clases ve el detector. Si no existe, pregunta qué hay instalado y escríbela. Si es un cliente nuevo y todavía no hay nada, usa `datos/estaciones/solo-camara.json`: lo que salga dice qué habría que instalar.

## Cómo leer el documento

En este orden, porque cada cosa decide la siguiente:

1. **Lo que no puede pasar.** Los eventos de alta consecuencia que el protocolo quiere evitar. Por cada uno, la combinación de lecturas de sensor que lo describe, si existe (`guarda = abierta` con `energia = viva`). De acá salen los controles críticos y las reglas de seguridad.
2. **Los elementos.** Equipos, herramientas, repuestos, protecciones, energías y personas que el proceso nombra. Usa las palabras del protocolo (su glosario, si tiene).
3. **Los pasos.**

## Los pasos

- Un paso es **una acción que deja un estado que se puede comprobar**. Si una frase deja dos estados que se comprueban por separado, son dos pasos: aislar la energía, bloquear y probar que no hay energía van separados y en ese orden ([ADR-0011](../../../knowledge/decisions/0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md)). Dos cosas que van juntas y que cierra la misma evidencia son un paso («Pon tu candado y tu tarjeta»).
- **Solo lo que el documento dice.** Cada paso lleva una `cita`: un fragmento literal y continuo del documento, copiado, no parafraseado (el comprobador ignora las negritas y los saltos de línea). Dos pasos que salen de la misma frase pueden compartir cita. Si crees que al protocolo le falta un paso, no lo agregues: va a `dudas`.
- Son pasos los que el protocolo enumera como la tarea, en el orden en que se ejecutan (si no es el del documento, anótalo en `dudas`). El alcance, las obligaciones de gestión (capacitar, planificar turnos, cumplir la norma), lo que pide tener listo antes de empezar y los registros no lo son: si alguno te parece que sostiene un control (probar el instrumento antes de medir), va a `dudas`.
- Si el protocolo exige dentro de un paso un orden o una condición («con todos fuera de la correa») que la evidencia no distingue, va a `dudas`: es justo lo que la pauta no va a comprobar.
- Una pauta es una lista en orden, y cada paso se cierra con un estado. Lo que el protocolo pide y esa forma no expresa **no se fuerza ni se calla**: va a `no_cabe`, con su tipo y su cita (ver [Lo que no cabe](#lo-que-no-cabe)).
- La pauta va en el idioma del operario; las citas, en el del documento. Las unidades quedan como las trae el documento, sin convertir.
- `titulo`: en infinitivo y con las palabras que oye el operario («Poner tu candado»). `instruccion`: el detalle como lo dice el protocolo, hablándole al operario.
- `id` de `p1` a `pn`, `orden` de 1 a n.

## Qué evidencia cierra cada paso

La primera que aplique. No es una preferencia: es la regla de [LOGICA](../../../knowledge/architecture/LOGICA.md#quién-decide-que-un-paso-está-hecho).

1. **`sensor`**, si el paso **cambia** la lectura de un sensor **de la estación**. Si el sensor ya marcaba ese valor antes del paso (probar que no arranca, con la correa ya detenida), el paso se cerraría solo: no es de sensor. Tampoco lo es si lo que pide es que el operario mire o pruebe algo y el sensor cambia de paso («probar sin carga»): eso es confirmación. Usa el `id` y el valor tal como están ahí; no inventes sensores ni valores. Si no es evidente qué significa un valor (¿`cerrado` es el candado puesto?), anótalo en `dudas`.
2. **`camara`**, si la estación tiene cámara y el resultado se ve en una sola foto. La `pregunta_visual` es de sí o no, sobre el **estado final** y no sobre la acción ni el orden, y «sí» significa hecho. Pregunta solo por lo que se ve: «pernos puestos» se ve, «pernos apretados» no, y lo que no se ve va a `dudas`. La lectura de un instrumento (un termómetro, un manómetro) no cuenta como algo que se ve, salvo que la estación diga que la cámara lo enmarca: es confirmación, y el instrumento va a `sensores_que_faltan`. `deteccion` solo si el objeto está en las `clases` de la estación.
3. **`confirmacion`**, para lo demás: una prueba que hace el operario, una coordinación, algo que la cámara no alcanza a ver.

Así el borrador siempre se puede ejecutar en la estación que hay. Si un control crítico termina cerrándolo la cámara o la palabra porque falta un sensor, no lo arregles: la comprobación lo marca como `instrumentar`, y ese es el resultado de factibilidad que la persona necesita ver.

Por cada paso que un sensor cerraría mejor y que hoy cierra la cámara o la palabra, propón ese sensor en `sensores_que_faltan`: qué mide y qué estados reporta. Un límite numérico o un tiempo **sí caben**: el edge los convierte en estado (`temperatura = bajo_5C`, `enfriamiento = cumplido`), así que «enfriar al menos cinco minutos» es un sensor que falta, no algo que no cabe. Proponer no es escribirlo en la pauta.

`capa_minima`: 1 para sensor y confirmación, 3 para cámara, 2 para cámara con `deteccion`.

## Qué es control crítico

`control_critico: true` solo si su falla deja ocurrir algo de «lo que no puede pasar», y `critico_porque` dice cuál. Los pasos que deshacen un control (sacar el candado, devolver la corriente) también lo son. Si dudas, no lo marques y anótalo en `dudas`: marcar de más hace que el sistema interrumpa por cosas que no lo valen.

## La forma del borrador

```json
{
  "documento": "datos/protocolos/prot-x.md",
  "protocolos": ["prot-x"],
  "pauta": {"id": "pauta-x-01", "nombre": "…", "version": 1, "equipo": "…", "pasos": [
    {"id": "p1", "orden": 1, "titulo": "…", "instruccion": "…", "tipo_evidencia": "sensor",
     "capa_minima": 1, "control_critico": true, "sensor": {"id": "energia", "espera": "cortada"}}
  ]},
  "analisis": {
    "fuente": "protocolo",
    "no_puede_pasar": [{"que": "…", "sensores": {"guarda": "abierta", "energia": "viva"}, "cita": "…"}],
    "elementos": [{"nombre": "candado personal", "tipo": "proteccion", "pasos": ["p3", "p8"]}],
    "pasos": {"p1": {"cita": "…", "evidencia_porque": "…", "critico_porque": "…"}},
    "sensores_que_faltan": [{"paso": "p4", "sensor": "botonera", "estados": ["partir_apretado", "suelta"], "mide": "…"}],
    "no_cabe": [{"tipo": "rama", "paso": "p6", "cita": "…"}],
    "dudas": ["…"]
  }
}
```

`pauta` es el contrato de `app/contratos.py`, sin campos de más. En `no_puede_pasar`, `sensores` usa solo sensores de la estación; un peligro que esos sensores no describen completo (falta medir a la persona, por ejemplo) lleva `"sensores": {}` y una línea en `dudas`. No aproximes: de esa combinación sale una regla que interrumpe al operario. `elementos[].tipo` es uno de `equipo`, `herramienta`, `repuesto`, `material` (lo que se procesa), `proteccion`, `energia`, `persona`. `pauta.equipo` es sobre qué se hace la tarea: la máquina, o la línea o el producto si no hay una. `critico_porque` va solo en los pasos críticos. Los ids de `protocolos` salen de `datos/protocolos.json`; si el documento dice que aplica junto con otro protocolo, van los dos.

## Lo que no cabe

| `tipo` | Lo que pide el protocolo | Ejemplo |
|---|---|---|
| `rama` | Un paso que solo se hace si se cumple una condición, caminos distintos, volver a un paso anterior o terminar antes | «Si no llegó a 70 °F, recalienta y empieza de nuevo» |
| `eleccion` | Uno o más entre varios modos de hacerlo | «Enfría con uno o más de estos métodos» |
| `repeticion` | Lo mismo por cada uno de varios | «Repite en cada uno de los seis pernos» |
| `periodico` | Algo que se repite cada cierto tiempo mientras un paso sigue abierto | «Mide la temperatura cada hora» |
| `plazo` | Un tiempo que corre entre pasos o desde un paso anterior | «Dentro de las 4 horas que quedan» |
| `sin_orden` | Pasos que se pueden hacer en cualquier orden, o a la vez | «Mientras se enfría, revisa las mangueras» |
| `registro` | Un valor que hay que anotar, no solo cumplir | «Anota la temperatura y la hora» |
| `rol` | Que lo haga una persona determinada, o dos | «Lo baja el eléctrico autorizado» |
| `otro` | Cualquier otra cosa | |

`paso` es el paso donde quedó lo más cercano, o nulo si es de toda la pauta. En la pauta, escribe el camino normal y en orden; el resto queda aquí a la vista, incluido lo que el documento pide en sus secciones de monitoreo, acciones correctivas y registros. Un plazo que vive dentro de un solo paso es un sensor que falta; uno que cruza pasos es `plazo`. Esta lista es la que le dice al equipo qué le falta al contrato para un proceso nuevo: sé literal y no la abultes.

## Comprobar

```bash
uv run python scripts/analizar.py pauta datos/borradores/<id>.json --estacion datos/estaciones/<estación>.json
```

Dice si cumple el contrato, si cada cita está literal en el documento, qué puede cerrar la estación y qué análisis vale la pena correr. Sale con 1 si falla el contrato, una cita, un `capa_minima` o si un paso pide algo que la estación no tiene: corrige y repite hasta que salga con 0. Lo que aparece en «Qué vale la pena analizar» no es un error y no cambia el código de salida: no se arregla editando el borrador, se entrega.

Si ya existe una pauta escrita por una persona para el mismo proceso, mide cuánto te acercaste:

```bash
uv run python scripts/analizar.py comparar datos/borradores/<id>.json datos/pauta-<x>.json
```

## Entregar

A la persona que aprueba, en este orden: los pasos con su evidencia, las `dudas`, lo que la estación no puede cerrar, y lo que pide «Qué vale la pena analizar». Cada pedido tiene su skill (`regla-programatica`, `solucion-vision`); `instrumentar` es una decisión de hardware y es de la persona. No corras esas skills por tu cuenta: propón.

Solo cuando te lo pidan, carga el borrador, que nace sin aprobar: `POST /interno/protocolos/{protocolo_id}/pautas` con `{"pauta": <pauta>, "actor": "equipo:<quien>", "protocolos": []}`. Nunca apruebes.

## Desde una grabación

```bash
uv run python scripts/analizar.py cuadros <video> --cada 2
```

Mira los cuadros en orden. Un paso termina donde la escena cambia de estado. La `cita` de cada paso es el nombre del cuadro donde se ve el estado final, `fuente` es `"observacion"` y el borrador no lleva `documento`.

Lo que sale de una grabación vale menos que lo que sale de un documento, y hay que decirlo al entregar: un VLM sin la pauta describió el 54,6 % de las fases de un montaje ([REFERENCIAS 9](../../../knowledge/projects/research/REFERENCIAS.md)). Es un borrador para que el experto que hizo la tarea lo corrija. Desde un video no marques ningún control crítico: el peligro no se ve en la imagen. Van a `dudas`.
