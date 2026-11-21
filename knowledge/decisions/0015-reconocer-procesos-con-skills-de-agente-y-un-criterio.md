# ADR-0015 — Los procesos los reconoce un agente con skills; lo comprobable lo comprueba el código, y un criterio decide qué se analiza

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

El producto es general ([ADR-0005](./0005-producto-general-mineria-como-caso-del-demo.md), [ADR-0009](./0009-flujo-operacional-verificable-mantenimiento-como-caso-de-uso.md)): tiene que servir para cualquier proceso estandarizado que se pueda verificar. Hoy las pautas de `datos/` se escriben a mano y `app/protocolos.extraer_pasos` es un stub. Jonathan planteó el 2026-11-21 la meta: dada cualquier pauta o un proceso observado, reconocer sus pasos, sus puntos importantes y sus elementos, ver si es factible con los sensores que hay, proponer la pauta, buscar mejoras, y generar reglas programáticas y soluciones de visión cuando hagan falta. Con alta certeza, y sin hacer todos esos análisis para cada operación.

Dos restricciones ya decididas: una persona aprueba toda pauta antes de usarla ([ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md)), y un modelo nunca contradice a un sensor ([ADR-0004](./0004-verificacion-por-capas.md)).

## Decisión

**El reconocimiento lo hace un agente con skills, no un servicio nuevo.** Cuatro skills en `.claude/skills/`, una por capacidad:

| Skill | Entra | Sale |
|---|---|---|
| `reconocer-proceso` | El protocolo del cliente, o una ejecución grabada, y la estación | Un borrador de pauta con pasos, controles críticos, elementos y «lo que no puede pasar» |
| `optimizar-proceso` | La bitácora de las OT de una pauta | La versión siguiente de la pauta, con la razón y las OT de cada cambio |
| `regla-programatica` | Un peligro descrito con lecturas de sensores | Una regla de capa 1 en `app/reglas.py`, con test y su fila en LOGICA |
| `solucion-vision` | Un paso de cámara y sus imágenes | La pregunta al VLM o el detector, y los casos que lo miden |

**Lo que se puede comprobar no lo opina el agente.** `app/analisis.py`, con `scripts/analizar.py` como entrada, comprueba sin modelo: que la pauta cumple el contrato, que cada paso cita un fragmento literal del protocolo, que ningún paso de sensor se cierra solo porque un paso anterior ya dejó esa lectura, que ninguna regla de seguridad dispara cuando la pauta se ejecuta bien, qué capa puede cerrar cada paso en una estación dada (`datos/estaciones/`), y cuánto se parece un borrador a la pauta que escribió una persona. De ahí sale la certeza: de lo que se comprobó, no de la confianza que declare el modelo.

**Un criterio decide qué se analiza, y vive en el código** (`analisis.criterio` y `analisis.criterio_de_historia`). Un paso que su sensor cierra, que no es crítico y que nadie se salta no pide nada. Se pide:

| Análisis | Cuándo |
|---|---|
| `instrumentar` (decisión de una persona) | Un paso que la estación no puede cerrar; un control crítico que cierra la palabra o la cámara; un peligro cuyos sensores no existen |
| `regla-programatica` | Un peligro que los sensores de la estación describen y con el que ninguna regla de seguridad dispara |
| `solucion-vision` | Un paso que cierra el VLM y cuya pregunta no tiene casos en el eval de capa 3; o que la cámara no cerró en 2 o más OT |
| `optimizar-proceso` | Con 5 o más OT de la misma versión: un paso con conflicto, cierre por persona o alerta en 2 o más OT, o que se lleva el 40 % del tiempo |

Los umbrales son constantes con nombre en `app/analisis.py`. Cambiarlos es cambiar el criterio.

**Nada de esto se usa solo.** Las skills escriben borradores en `datos/borradores/`, no cargan ni aprueban, y una regla nueva va en su propio PR.

**Lo que un proceso pide y la pauta no expresa queda a la vista, no se fuerza.** Una pauta es una lista en orden donde cada paso se cierra con un estado. El borrador lleva `no_cabe` (ramas, elecciones, repeticiones, plazos entre pasos, pasos sin orden, valores que hay que anotar, quién debe hacerlo) y `sensores_que_faltan` (lo que un sensor cerraría mejor que la cámara o la palabra). La primera lista, sumada sobre protocolos reales, es la que dice qué le falta al contrato; la segunda, qué instalar. Un cliente nuevo parte con `datos/estaciones/solo-camara.json`.

## Hasta dónde llega hoy con un proceso desconocido

| Etapa | Sin tocar código | Qué hace falta |
|---|---|---|
| Leer el proceso y proponer la pauta | Sí | La skill y el documento |
| Saber si es factible y qué instalar | Sí | Describir la estación en un JSON |
| Ejecutarla con cámara y confirmación | Sí | Cargar el borrador y que una persona lo apruebe |
| Que el detector busque los objetos de la pauta | Sí, con el detector en el edge | El edge pregunta qué clases pide la OT en sesión y las suma a las que busca siempre (`--clases`, que incluye las que solo están para no confundir, como `soda can` junto a `red soda can`). Con el detector en el servidor hay que exportar el modelo de nuevo. Un detector que no busca una clase no puede decir que el objeto ya no está |
| Ejecutarla con un sensor nuevo | **No** | El paso de lectura cruda a estado está escrito a mano en `estados()` de `edge/edge.py`, y el firmware es del demo |
| Que avise un peligro propio del proceso | **No** | Las reglas son una tupla global en `app/reglas.py`. Comparan nombres de sensor, así que dos procesos que usen `energia` o `zona` con sentidos distintos se pisan; el servidor no sabe a qué estación pertenece una lectura |
| Procesos que no son una lista en orden | **No** | El contrato es lineal. No expresa ramas, elegir entre varios modos, algo que se repite cada cierto tiempo, ni un plazo que corre entre pasos |

Las tres filas en «No» son del producto, no de las skills. Las dos primeras se resolverían con el mismo movimiento: que el archivo de la estación sea la única descripción de una instalación, con sus umbrales y sus peligros, y que el edge y las reglas lo lean. No está decidido ni construido. `Brecha`.

## Relación con el PRD de skills y con el ADR-0014

Este trabajo se hizo en una rama que partió antes de que llegaran a `main` el [PRD de skills](../projects/skills/PRD.md) de Francisco y el [ADR-0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md). Se cruzan, y no está acordado cuál forma queda. `Brecha` de coordinación.

| En el PRD | Acá | Diferencia |
|---|---|---|
| `factum-extraer-protocolo` y `factum-generar-pauta` | `reconocer-proceso` | Una skill en vez de dos. No guarda el protocolo por la API: lee el documento y escribe un borrador en `datos/borradores/` |
| `factum-mejorar-pauta` | `optimizar-proceso` | Lee la bitácora directo. El PRD la quiere sobre `GET /interno/mejoras` y las métricas por paso del ADR-0014, cuyo código todavía no está en `main`. `analisis.historia` y `criterio_de_historia` duplican parte de eso y tendrían que ceder cuando llegue |
| El validador (`POST /interno/pautas/validar`, reglas V1 a V4) | `app/analisis.py` y `scripts/analizar.py` | Es un comando, no una ruta. Cubre V1 (control crítico sin sensor, como `instrumentar`) y V4 (`capa_minima`); de V2 cubre el paso que espera lo que un paso anterior ya dejó, no el valor de reposo al abrir la OT; V3 (reposición en orden inverso) no está |
| El inventario de cada estación | `datos/estaciones/*.json` | Archivos, no una ruta, y el servidor no los lee |
| `factum-pedir-ot`, `factum-ejecutar-ot`, `factum-reportar`, `factum-medir` | — | No están |
| — | `regla-programatica`, `solucion-vision` y el criterio | No están en el PRD |

Las skills viven en `.claude/skills/`, donde Claude Code las carga solas; el PRD las pone en `skills/` con el prefijo `factum-`. El paso que este ADR deja como siguiente (que el archivo de la estación traiga umbrales y peligros) es la misma pregunta que el PRD deja abierta como «Inventario por estación» y «Perfil por protocolo», y la decide Francisco.

## Alternativas consideradas

- **A — Un servicio en la API que llama al modelo (`POST /interno/protocolos/{id}/borrador`):** deja el reconocimiento dentro del producto, pero hay que escribir y mantener el prompt, el esquema, los reintentos y el presupuesto, y solo cubre «protocolo a pasos». Las otras tres capacidades tocan código, fotos y evals, que es trabajo de agente. Queda para cuando el cliente lo necesite sin el equipo en medio; las comprobaciones de `app/analisis.py` son las mismas.
- **B — Que el agente lo haga todo, sin comprobador:** más corto, pero la certeza queda en lo que el modelo dice de sí mismo. Un VLM general acertó 3 de 12 cambios de orden (REFERENCIAS 9).
- **C — Analizar todo, siempre:** cada paso de cámara con su eval y su detector, cada pauta con su análisis de historia. Con 41 de los 60 pasos de las pautas de `datos/` cerrados por sensor, la mayor parte del gasto no cambiaría nada.

## Consecuencias

- Cargar un protocolo nuevo deja de ser escribir un JSON a mano: es correr una skill y revisar un borrador con sus citas y sus dudas.
- «Ver factibilidad» tiene una respuesta concreta: qué pasos no puede cerrar esta estación y qué controles críticos quedan sin sensor. Exige describir cada estación en `datos/estaciones/`.
- El frente 1 queda cubierto por la skill, pero `extraer_pasos` sigue siendo un stub: la API no reconoce nada por sí sola.
- Las skills dependen de un agente que las cargue (Claude Code, o el Agent SDK sin interfaz). Es una dependencia de herramienta, no de producto.

## Pendientes y no verificado

- **Medido, y es poco.** `reconocer-proceso` se probó a ciegas con dos protocolos (`prot-correa-01` y `prot-celda-mt-01`): un agente sin acceso a la pauta escrita por una persona, y después `scripts/analizar.py comparar`. En la correa, 9 de 10 pasos salieron iguales en evidencia, sensor, valor y control crítico; el que difiere es «Probar sin carga», que el agente cerró con el sensor de la correa y la persona con confirmación. En la celda, los 8 pasos de la persona salieron con la misma evidencia y en el mismo orden, 7 con el mismo control crítico, más 3 pasos que la persona no escribió. Todas las citas fueron literales. `Candidata a validar`: son dos protocolos que redactó el mismo equipo que escribió las pautas, una corrida de cada uno, y las estaciones se armaron con los sensores que esas pautas usan. Falta un protocolo real de un cliente.
- **Con un proceso de otro dominio, reconoce pero no representa.** Se probó a ciegas con un procedimiento público de inocuidad alimentaria (enfriado en dos etapas, del Institute of Child Nutrition, en inglés), sin sensores: solo `solo-camara.json`. No inventó nada (3 de 3 citas literales), propuso los dos sensores que harían falta (sonda y reloj por etapa) y dejó fuera de la pauta, con su cita, 7 cosas: 4 ramas, el monitoreo cada hora, el registro y la verificación del encargado. Pero la pauta que queda tiene 3 pasos y los tres los cierra la palabra del operario. El proceso es una espera vigilada con plazos, no una secuencia de acciones, y ahí una pauta lineal sirve de registro y no de verificación. El comprobador lo dice cuando lo que queda fuera iguala o supera a los pasos. Es un solo documento. `Candidata a validar`.
- **De punta a punta, en memoria.** Dos pautas generadas por el agente (el enfriado, 3 pasos; la celda, 13) se cargaron desde un protocolo, se aprobaron y se ejecutaron hasta el final, con las lecturas puestas a mano y el VLM simulado. Prueba el recorrido, no que la cámara acierte.
- **El edge sigue las clases de la OT**, probado con YOLO-World real en el Mac contra una API de prueba y cuadros de ruido: sumó `bottle` a sus clases al tomar una OT que la pide y la soltó al cerrar la sesión. Cada cambio de lista carga el modelo de nuevo (unos segundos); una pauta que solo pide clases que el edge ya busca no lo recarga. No se probó con la cámara ni con objetos reales, ni que un objeto fuera de `mouse` y `pencil` llegue al 80 % de confianza. `Candidata a validar`.
- Quién decide que un objeto de la pauta se puede detectar sigue siendo una persona con la skill `solucion-vision`: el reconocedor solo escribe `deteccion` para clases que la estación ya declara.
- **El comprobador encontró algo en una pauta del demo.** `pauta-polin-estacion` (llegó de `main` al integrar) repone la corriente en `e6` sin un paso que aleje al operario, que `e2` dejó junto a la cinta. Seguida al pie de la letra dispara «persona junto a la máquina con el motor encendido». Puede ser lo que el demo quiere mostrar; si no, falta un paso «alejarse» antes de `e6`. No se tocó la pauta: es de quien arma el demo. `Candidata a validar`.
- La primera ronda de esa prueba dejó pasar dos errores que el comprobador ahora ataja o la skill ya no pide: un paso de sensor que se cerraba solo, y un sensor inventado para un control crítico. Es de esperar que haya más de esa clase.
- `comparar` alinea por la evidencia: dos pasos de cámara, o dos de confirmación, calzan aunque hablen de cosas distintas. Solo los de sensor prueban algo.
- Reconocer desde una grabación no se probó: no hay un video de una ejecución en el repo. La skill lo trata como un borrador de menor certeza, por el 54,6 % de fases que describe un VLM sin la pauta (REFERENCIAS 9). `Brecha`.
- `optimizar-proceso` se corrió solo sobre las 15 OT de la semilla, que no llegan a 5 por pauta: el criterio no pidió nada, que es lo esperado. No hay historia real. `Brecha`.
- `regla-programatica` y `solucion-vision` no se corrieron de punta a punta. El detector entrenado no tiene script de entrenamiento. `Brecha`.
- Los umbrales del criterio (5 OT, 2 repeticiones, 40 %) no salen de ninguna medición. `Candidata a validar`.
- El tiempo del primer paso se mide desde que se abrió la OT, que incluye la espera.

## Referencias

- [LOGICA](../architecture/LOGICA.md): quién decide que un paso está hecho, dónde aprueba una persona, y cuándo el sistema propone cambiar la pauta.
- [FLUJO](../architecture/FLUJO.md), pasos 2 y 6.
- REFERENCIAS 9 y 33.
- `app/analisis.py`, `scripts/analizar.py`, `tests/test_analisis.py` y `.claude/skills/`.
