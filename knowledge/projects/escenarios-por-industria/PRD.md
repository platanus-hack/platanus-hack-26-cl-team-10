# PRD — Escenarios por industria

> **Dueño de la decisión:** Francisco · **Se consulta a:** frente 3 (sensores y juez de cámara), equipo (las reglas nuevas de capa 1 tocan el contrato) · **Alcance:** cada forma de ejecutar un paso, en minería, eléctrica y construcción, contra la barrera que la decide, con lo esperado atado a una norma o a una regla de LOGICA.
>
> **Estado →** [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md). Este documento no lleva avance. La decisión estructural está en [ADR-0008](../../decisions/0008-escenarios-por-industria-en-una-caja-aislada.md). Las normas, en [REFERENCIAS](../research/REFERENCIAS.md#reglas-de-seguridad-por-industria) 44 a 55.

## 1. Resumen

**Hoy:** los criterios del [PRD de servicios en vivo](../servicios-en-vivo/PRD.md) prueban que el servicio atribuye, califica y reparte. No prueban cómo responde cada barrera a las formas reales de equivocarse (saltarse un paso, decirlo antes de hacerlo, deshacer un control ya verificado), ni en otra industria que la correa del demo. Y las reglas de capa 1 están escritas para esa correa.

**Después:** una matriz de industria por patrón de ejecución, con la barrera que decide cada caso y lo esperado atado a su fuente. Corre en segundos, en una caja aislada, y muestra qué cumple, qué no y qué decisión lo cierra. Cada barrera se mejora con su propia herramienta: la capa 1 con reglas por industria, la capa 2 con una simulación que compara detectores y la capa 3 con un eval del juez de cámara.

## 2. Historia

**Antes.** Francisco quiere saber si el sistema detecta que un operario se saltó el bloqueo y lo hizo después. Tiene que armar a mano una OT, mandar lecturas y leer la bitácora, y la respuesta vale solo para la correa.

**Después.** Abre `/casos`, corre los escenarios y ve que en las tres industrias ese patrón (B2) deja la bitácora limpia. Lee de dónde sale lo esperado (DS 132 art. 52, RD 614 anexo II, 29 CFR 1926.600) y qué regla lo cerraría.

## 3. Objetivos y no-objetivos

- **O1 —** Cada industria tiene los mismos 22 patrones, y la matriz completa corre sin tocar la bitácora ni los sensores del servidor.
- **O2 —** Cada escenario dice de dónde sale lo que espera: una regla de LOGICA, un ADR o una norma con número en REFERENCIAS.
- **O3 —** Cada brecha dice qué hace hoy el sistema, por qué y qué la cierra; y si alguien la cierra, el test lo avisa.
- **O4 —** Para la capa 2, una simulación compara detectores contra fallas típicas de cada industria y dice cuál aguanta cuál.
- **O5 —** Para la capa 3, un eval mide la falsa aceptación, el falso rechazo y la calibración del juez sobre escenas de cada industria.
- **NO1 —** No calibra umbrales: las señales de la capa 2 son sintéticas y la capa 3 todavía no tiene imágenes.
- **NO2 —** No agrega reglas a `reglas.py` ni cambia `contratos.py`: las propone (§5.3) y las decide el equipo.
- **NO3 —** No reemplaza los CA del servicio, que siguen probando el camino HTTP real en `/casos`.

## 4. Flujo: hoy → después

```text
HOY
pregunta («¿qué pasa si se salta el bloqueo?») → OT a mano en el servidor → lecturas por curl → leer la bitácora → vale para la correa

DESPUÉS
/casos o tests → catálogo (industria × patrón) → caja aislada: base en memoria, juez y reloj inyectados
              → servicios.py real → bitácora, stream y calificación → esperado contra obtenido → pasa · brecha · falla
capa 2 → scripts/simular_capa2.py → detector × falla × industria → capa2-simulacion.md
capa 3 → scripts/evaluar_capa3.py → juez × escena → falsa aceptación, falso rechazo, calibración
```

## 5. Datos y reglas

### 5.1 Industrias

Una pauta por industria, del mismo flujo ([ADR-0005](../../decisions/0005-producto-general-mineria-como-caso-del-demo.md)). Los sensores devuelven estados discretos, como `reed_bloqueo`.

| Industria | Pauta | Sensores | Regla de peligro de capa 1 | Estado de la regla |
| --- | --- | --- | --- | --- |
| Minería | `datos/pauta-correa.json`, cambio de rodillo, 6 pasos | `reed_bloqueo`, `guarda`, `energia`, `vibracion` | Guarda abierta con energía viva (44, 45) | Vigente en LOGICA |
| Eléctrica | `datos/pauta-celda-mt.json`, interruptor de celda MT, 8 pasos | `seccionador`, `candado_mando`, `tension`, `tierra`, `temperatura_conexion` | Puesta a tierra con tensión presente (48, 49, 50) | Propuesta |
| Construcción | `datos/pauta-excavadora.json`, manguera hidráulica, 7 pasos | `implementos`, `motor`, `palanca_seguridad`, `presion_hidraulica`, `zona`, `temperatura_aceite` | Persona en la zona con los implementos levantados (52) | Propuesta |

En construcción, bloquear la palanca y aliviar la presión **no tienen norma**: 29 CFR 1910.147 lo exige, pero excluye la construcción (52). Esos pasos vienen del fabricante y no se presentan como obligación legal.

### 5.2 Patrones de ejecución

Los mismos en las tres industrias. La barrera es la capa del [ADR-0004](../../decisions/0004-verificacion-por-capas.md) que decide el caso.

| Grupo | Patrón | Barrera | Lo que pregunta | Hoy (las tres industrias) |
| --- | --- | --- | --- | --- |
| A · Cuándo llega la evidencia | A1 Lo hace y el sensor lo ve, sin hablar | 1 | ¿Se cierra solo con la lectura? | pasa |
| | A2 El sensor lo ve y después lo dice | 1 | ¿La palabra tardía se confunde con el paso siguiente? | **brecha** |
| | A3 Lo dice y después el sensor lo ve | 1 | ¿Interrumpe por segundos de diferencia? | pasa, con nota |
| | A4 Lo dice y el sensor nunca lo confirma | 1 | ¿Queda en conflicto y a la vista? | pasa |
| | A5 Dice que hizo el siguiente sin hacer este | 1 | ¿Se detecta el salto? | pasa |
| B · El orden | B1 Se salta el paso y hace el siguiente | 1 | ¿La pauta avanza igual? | pasa |
| | B2 Se lo salta, hace el siguiente y vuelve | 1 | ¿Queda registro del orden invertido? | **brecha** |
| | B3 Se lo salta y crea la condición de peligro | 1 | ¿Suena la alerta? | pasa en minería; **brecha** en las otras |
| C · Un control se deshace | C1 Deshace un control crítico verificado | 1 | ¿Se avisa que el control se perdió? | **brecha** |
| | C2 Lo deshace y se crea el peligro | 1 | ¿Suena la alerta? | pasa en minería; **brecha** en las otras |
| D · La lectura | D1 El sensor repite la lectura | 1 | ¿Se cuenta una vez? | pasa |
| | D3 El sensor deja de mandar | 1 | ¿Baja la certeza? | **brecha** |
| F · La cámara | F1 Confirma con confianza alta | 3 | ¿Se cierra sin aviso? | pasa |
| | F2 Confirma con confianza baja | 3 | ¿Pide que alguien mire? | pasa |
| | F3 Contradice al operario | 3 | ¿Conflicto sin interrumpir? | pasa |
| | F4 Sin video, el juez dice que sí | 3 | ¿Se acepta un sí sin cuadro? | **brecha** |
| | F5 Dice que sí y un sensor marca peligro | 3 | ¿Un modelo contradice a un sensor? | pasa en minería; **brecha** en las otras |
| G · La señal | G1 Un pico aislado | 2 | ¿Avisa una vez y se resuelve? | pasa |
| | G2 Un escalón que se sostiene | 2 | ¿El aviso dura lo que dura la falla? | **brecha** |
| | G3 Una deriva lenta | 2 | ¿Se detecta antes del daño? | pasa |
| | G4 Ruido normal | 2 | ¿Da falsas alarmas? | pasa |
| | G5 Un sensor pegado que se mueve apenas | 2 | ¿Confunde quieto con falla? | **brecha** |

En total, 66 escenarios: 39 pasan y 27 son brechas.

Los criterios del servicio, ordenados en la misma taxonomía. Son transversales: valen igual en las tres industrias.

| CA del servicio | Patrón o grupo | Barrera |
| --- | --- | --- |
| CA1, CA2 | Atribución: sin sesión y otra OT abierta. Condición previa de toda la matriz | 1 |
| CA3 | A1 | 1 |
| CA4 | B1 | 1 |
| CA5, CA11 | B3 y C2: la alerta entra una vez y se resuelve con el sensor | 1 |
| CA6, CA7 | Reparto: lo que la matriz ve por el stream | — |
| CA8, CA9, CA10 | Reglas del CRUD: pauta aprobada, versión, bitácora que solo agrega | — |
| CA12 | G1 | 2 |
| CA13 | F1, con el cuadro como evidencia | 3 |
| CA14 | Guía para agentes | — |

### 5.3 Reglas de capa 1 propuestas por industria

Cada una cierra brechas de la matriz y tiene su norma. Ninguna está en `reglas.py`: agregarlas toca el contrato y [LOGICA](../../architecture/LOGICA.md) en el mismo commit. Todas `Candidata a validar`.

| Regla | Industria | Condición sobre sensores | Fuente | Cierra |
| --- | --- | --- | --- | --- |
| Orden invertido | Las tres | Llega la lectura que cierra un paso posterior mientras el actual no está verificado → alerta de capa 1 con `evidencia.tipo = "orden"`, aunque después se haga | LOGICA; 44 art. 52; 48 A.1; 52 | B2 |
| Control crítico deshecho | Las tres | El sensor de un paso `control_critico` ya verificado vuelve a su valor anterior antes del paso que lo deshace en la pauta → alerta de capa 1 | 44 art. 52; 48 A.2; 50 (m)(3)(xiii); 52 | C1 |
| Tierra con tensión | Eléctrica | `tierra = puesta` con `tension = presente` | 50 (n)(5); 48 A.1; 49 9.1.5 | B3, C2, F5 |
| Reponer con tierras puestas | Eléctrica | `seccionador = cerrado` con `tierra = puesta` | 50 (m)(3)(xiii); 48 A.2; 49 9.1.7 | Patrón nuevo cuando entre la regla |
| Persona bajo implemento levantado | Construcción | `zona = ocupada` con `implementos = levantados` | 52; 53 en minería | B3, C2, F5 |
| Correa en movimiento con guarda abierta | Minería | Necesita un sensor de velocidad que el demo no tiene | 44 art. 116; 45 56.14112(b) | — |
| El candado lo saca quien lo puso | Minería | Necesita identificar el candado o a la persona (RFID) | 45 56.12016 | — |

El patrón que estas reglas atacan es el que la evidencia repite: el control existía y no se ejecutó. ICMM lo encontró en 19 de 26 fatales (40); MSHA, en una correa con procedimiento escrito de bloqueo que no se aplicó (47), y en ocho muertes en correas evitables con bloqueo (46); OSHA, en tierras retiradas en el orden equivocado (51).

### 5.4 Lo que no es regla de negocio

| Dato | Cambio | Fuente |
| --- | --- | --- |
| Escenario | Industria, patrón, pasos, lo esperado, fuente y, si la hay, la brecha. Vive en `app/escenarios.py` y se sirve en `GET /escenarios` | ADR-0008 |
| Casos del eval de capa 3 | `datos/evals/capa3/casos.jsonl`: 24 escenas, 8 por industria, con la respuesta esperada y el tipo de error. Las imágenes van en `datos/evals/capa3/imagenes/` y no se versionan | ADR-0008; CONTRIBUTING regla 6 |

## 6. Contrato de comportamiento

```text
CUANDO se corre un escenario
  ENTONCES se arma una caja nueva: base en memoria, la pauta de su industria, una OT y una sesión
           se aplican sus pasos (lecturas, declaraciones, cuadros, tiempo) por servicios.py
           se mide el estado final y el peor nivel que alcanzó, y se compara con lo esperado
  SI no tiene brecha y no cumple      → falla: algo que funcionaba se rompió
  SI tiene brecha y no cumple         → brecha: lo conocido
  SI tiene brecha y cumple            → brecha cerrada: hay que quitar la marca
  NO toca la base, los sensores ni el bus del servidor

Promesas: la misma matriz para las tres industrias; lo esperado siempre con fuente; una brecha nunca pasa en silencio.
```

## 7. Alcance

**Entra:** las tres pautas, los 22 patrones por industria, la caja aislada, `GET /escenarios` y `POST /escenarios[/{id}]/correr`, la matriz y el detalle en `/casos`, `tests/test_escenarios.py`, la simulación de capa 2 y el eval de capa 3 con su set de escenas.

**No entra:** escribir las reglas de §5.3 (decide el equipo), cambiar el detector de capa 2 (sale de la simulación y del ensayo), conectar un VLM (frente 3), juntar las imágenes del eval y patrones de relevo de turno.

## 8. Criterios de aceptación

- **CA1 —** **Dado** el catálogo, **cuando** se corre, **entonces** cada industria tiene los 22 patrones y cada escenario sin brecha cumple lo esperado.
- **CA2 —** **Dado** un escenario con brecha, **cuando** alguien cambia el código y el escenario empieza a cumplir, **entonces** el test falla y pide quitar la marca.
- **CA3 —** **Dado** un servidor con su bitácora, **cuando** se corre la matriz, **entonces** su base no cambia.
- **CA4 —** **Dado** cualquier escenario, **cuando** se lee, **entonces** dice de dónde sale lo que espera.
- **CA5 —** **Dado** `/casos`, **cuando** se corren los escenarios, **entonces** se ve la matriz con su sello por celda, y al elegir una celda, lo esperado contra lo obtenido, la bitácora y lo que habría llegado por el stream.
- **CA6 —** **Dado** la simulación de capa 2, **cuando** se corre, **entonces** informa, por industria y detector, las falsas alarmas y si detecta y sostiene el pico, el escalón, la deriva y el sensor pegado.
- **CA7 —** **Dado** un juez de cámara, **cuando** se corre el eval de capa 3, **entonces** informa la falsa aceptación, el falso rechazo y la confianza en aciertos y errores, y cuenta aparte los casos sin imagen.

Los tests: `tests/test_escenarios.py` (CA1 a CA4), `tests/test_casos.py` (CA5) y `tests/test_barreras.py` (CA6 y CA7).

## 9. Riesgos y decisiones abiertas

Ordenadas por lo que cambian. Las tres primeras son de capa 1 y cambian lo que se muestra en el demo.

| Tema | Impacto | Qué falta decidir | Se consulta a | Decide |
| --- | --- | --- | --- | --- |
| Orden invertido (B2) | alto | Saltarse el bloqueo y hacerlo después deja la bitácora limpia en las tres industrias. Es el momento del demo. ¿Entra la regla «orden invertido» de §5.3 en `reglas.py`? | Equipo | Equipo |
| Declaración tardía (A2) | alto | Si el sensor cerró el paso y el operario lo dice después, la palabra cae sobre el siguiente y abre un conflicto de capa 1 que **interrumpe**. Es una falsa alarma en el oído. ¿`POST /ot/{id}/declarar` acepta `paso_id`, y una declaración sobre un paso ya verificado solo se registra? | Frente 2 | Francisco |
| Control deshecho (C1) | alto | Sacar el candado con la guarda abierta no avisa nada si la energía no está viva. ¿Entra la regla «control crítico deshecho»? | Equipo | Equipo |
| Reglas de eléctrica y construcción | medio | Sin ellas, B3, C2 y F5 no alertan en esas industrias. ¿Las reglas de seguridad pasan a ser datos de la pauta, en vez de código en `reglas.py`? Es un cambio de contrato, pero evita tocar código por cada industria | Equipo | Equipo |
| Sin cuadro (F4) | medio | El stub dice que sí con 55 % aunque no haya video, y el paso se verifica. ¿`servicios.py` deja sin verificar un paso de cámara sin cuadro? No toca el contrato | Frente 3 | Francisco |
| Frescura (D3) | medio | `scoring.py` define 5 s de frescura y el servicio nunca le pasa la edad: un sensor caído sigue con certeza total. Se arregla en `servicios.py` | Frente 3 | Francisco |
| Detector de capa 2 (G2, G5) | medio | Con la historia móvil de hoy, un escalón sostenido apaga su alarma: cubre 47 % de la falla en minería, 13 % en construcción y 4 % en eléctrica, y en eléctrica detecta 32 % de las derivas. El CUSUM contra el ciclo de trabajo detecta y sostiene todo, con 7 a 11 falsas alarmas cada 1.000 lecturas; el umbral fijo tiene casi cero falsas alarmas y es más lento en la deriva. Ver la [simulación](./capa2-simulacion.md). ¿Umbral fijo más CUSUM contra el ciclo, con un detector aparte de sensor pegado? Pide conocer el ciclo, por ejemplo con la corriente | Frente 3 | Francisco |
| Ventana de gracia (A3) | bajo | Decirlo un segundo antes de que el sensor lo vea abre un conflicto que interrumpe. ¿Se espera unos segundos antes de declarar el conflicto? `Candidata a validar` | Frente 2 | Equipo |
| Imágenes del eval de capa 3 | alto para el frente 3 | El set tiene 24 escenas y ninguna imagen. Hoy el eval solo dice que el stub acepta todo (falsa aceptación 15 de 15). ¿Se fotografían en la maqueta del demo con `/camara`? IndustReal (13) trae cuadros con errores de ejecución para una primera pasada | Frente 3 | Frente 3 |

## Fuentes

- [LOGICA](../../architecture/LOGICA.md), [ADR-0002](../../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md), [ADR-0004](../../decisions/0004-verificacion-por-capas.md), [ADR-0005](../../decisions/0005-producto-general-mineria-como-caso-del-demo.md), [ADR-0007](../../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md) y [ADR-0008](../../decisions/0008-escenarios-por-industria-en-una-caja-aislada.md).
- [CONTEXTO → Industrias](../../domain/CONTEXTO.md#industrias).
- REFERENCIAS 9, 13, 40 y 44 a 55.
