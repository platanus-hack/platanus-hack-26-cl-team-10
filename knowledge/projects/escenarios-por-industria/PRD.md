# PRD — Escenarios por industria

> **Dueño de la decisión:** Francisco · **Se consulta a:** frente 3 (sensores y juez de cámara), equipo (las reglas nuevas de capa 1 tocan el contrato) · **Alcance:** cada forma de ejecutar un paso, en minería, eléctrica y construcción, contra la barrera que la decide, con lo esperado atado a una norma o a una regla de LOGICA.
>
> **Estado →** [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md). Este documento no lleva avance. La decisión estructural está en [ADR-0008](../../decisions/0008-escenarios-por-industria-en-una-caja-aislada.md). Las normas, en [REFERENCIAS](../research/REFERENCIAS.md#reglas-de-seguridad-por-industria) 44 a 55.

## 1. Resumen

**Hoy:** los criterios del [PRD de servicios en vivo](../servicios-en-vivo/PRD.md) prueban que el servicio atribuye, califica y reparte. No prueban cómo responde cada barrera a las formas reales de equivocarse (saltarse un paso, decirlo antes de hacerlo, deshacer un control ya verificado), ni en otra industria que la correa del demo. Y las reglas de capa 1 están escritas para esa correa.

**Después:** una matriz de industria por patrón de ejecución, con la barrera que decide cada caso y lo esperado atado a su fuente. Corre en segundos, en una caja aislada, y muestra qué cumple, qué no y qué decisión lo cierra. Cada barrera se mejora con su propia herramienta: la capa 1 con reglas por industria, la capa 2 con una simulación que compara detectores y la capa 3 con un eval del juez de cámara.

## 2. Historia

**Antes.** Francisco quiere saber si el sistema detecta que un operario se saltó el bloqueo y lo hizo después. Tiene que armar a mano una OT, mandar lecturas y leer la bitácora, y la respuesta vale solo para la correa.

**Después.** Abre `/casos`, corre los escenarios y ve ese patrón (B2) en las tres industrias: la bitácora registra el orden invertido y la alerta se resuelve cuando se hace el paso saltado. Al lado lee de dónde sale lo esperado (DS 132 art. 52, RD 614 anexo II, 29 CFR 1926.600). El test de cada industria lo dice con las palabras del oficio: `test_b2_abrir_la_guarda_y_bloquear_despues_queda_en_la_bitacora`.

## 3. Objetivos y no-objetivos

- **O1 —** Cada industria tiene los mismos 24 patrones, cada uno con su test de caso de uso en el archivo de su industria, y la matriz completa corre sin tocar la bitácora ni los sensores del servidor.
- **O2 —** Cada escenario dice de dónde sale lo que espera: una regla de LOGICA, un ADR o una norma con número en REFERENCIAS.
- **O3 —** Cada brecha dice qué hace hoy el sistema, por qué y qué la cierra; y si alguien la cierra, el test lo avisa.
- **O4 —** Para la capa 2, una simulación compara detectores contra fallas típicas de cada industria y dice cuál aguanta cuál.
- **O5 —** Para la capa 3, un eval mide la falsa aceptación, el falso rechazo y la calibración del juez sobre escenas de cada industria.
- **NO1 —** No calibra umbrales: las señales de la capa 2 son sintéticas y la capa 3 todavía no tiene imágenes.
- **NO2 —** No cambia `contratos.py`: las reglas nuevas usan los tipos de evento que ya existen (`alerta` y `alerta_resuelta`, con `evidencia.tipo`).
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

Los mismos en las tres industrias. La barrera es la capa del [ADR-0004](../../decisions/0004-verificacion-por-capas.md) que decide el caso. Los 72 escenarios pasan; la última columna dice qué lo hace pasar.

| Grupo | Patrón | Barrera | Lo que pregunta | Qué lo decide |
| --- | --- | --- | --- | --- |
| A · Cuándo llega la evidencia | A0 La pauta completa, bien hecha | 1 | ¿Las reglas dan alguna falsa alarma? | El control de todas las demás: cero alertas, cero conflictos |
| | A1 Lo hace y el sensor lo ve, sin hablar | 1 | ¿Se cierra solo con la lectura? | El paso por sensor |
| | A2 El sensor lo ve y después lo dice | 1 | ¿La palabra tardía se confunde con el paso siguiente? | La declaración nombra su paso; si ya estaba cerrado, solo se registra |
| | A3 Lo dice y después el sensor lo ve | 1 | ¿Interrumpe por segundos de diferencia? | Sí: conflicto y después verificado. Ver §9 |
| | A4 Lo dice y el sensor nunca lo confirma | 1 | ¿Queda en conflicto y a la vista? | El paso por sensor |
| | A5 Dice que hizo el siguiente sin hacer este | 1 | ¿Se detecta el salto? | La app evalúa el paso actual |
| | A6 Lo confirma una persona contra el sensor | 1 | ¿Se le cree sin perder el rastro? | `POST /ot/{id}/pasos/{paso}/confirmar`: verificado por persona, OT en warning, la seguridad sigue mandando |
| B · El orden | B1 Se salta el paso y hace el siguiente | 1 | ¿La pauta avanza igual? | No avanza, y entra el orden invertido |
| | B2 Se lo salta, hace el siguiente y vuelve | 1 | ¿Queda registro del orden invertido? | Orden invertido, resuelto al hacer el paso saltado |
| | B3 Se lo salta y crea la condición de peligro | 1 | ¿Suena la alerta? | La regla de peligro de su industria |
| C · Un control se deshace | C1 Deshace un control crítico verificado | 1 | ¿Se avisa que el control se perdió? | Control crítico deshecho, resuelto al reponerlo |
| | C2 Lo deshace y se crea el peligro | 1 | ¿Suena la alerta? | Control deshecho más la regla de peligro |
| D · La lectura | D1 El sensor repite la lectura | 1 | ¿Se cuenta una vez? | El veredicto entra una vez |
| | D3 El sensor deja de mandar | 1 | ¿Baja la certeza? | Frescura: el sensor del paso en curso sin lecturas por más de 5 s baja la OT a warning |
| F · La cámara | F1 Confirma con confianza alta | 3 | ¿Se cierra sin aviso? | La calificación de capa 3 |
| | F2 Confirma con confianza baja | 3 | ¿Pide que alguien mire? | Bajo 75 % queda en warning |
| | F3 Contradice al operario | 3 | ¿Conflicto sin interrumpir? | La cámara se muestra y no suena |
| | F4 Sin video, el juez dice que sí | 3 | ¿Se acepta un sí sin cuadro? | Sin cuadro de los últimos 10 s no se le pregunta al juez |
| | F5 Dice que sí y un sensor marca peligro | 3 | ¿Un modelo contradice a un sensor? | La regla de peligro deja la OT en error |
| G · La señal | G1 Un pico aislado | 2 | ¿Avisa una vez y se resuelve? | El desvío robusto |
| | G2 Un escalón que se sostiene | 2 | ¿El aviso dura lo que dura la falla? | La historia solo aprende de lecturas normales |
| | G3 Una deriva lenta | 2 | ¿Se detecta antes del daño? | El desvío robusto |
| | G4 Ruido normal | 2 | ¿Da falsas alarmas? | El desvío robusto |
| | G5 Un sensor pegado que se mueve apenas | 2 | ¿Confunde quieto con falla? | El piso de ruido de scoring.py (2 % de la mediana, calibrado con sensores reales) y aviso aparte de sensor pegado tras 10 lecturas idénticas |

Los escenarios de la capa 2 no tienen ciclo de trabajo. Con un ciclo de carga, el detector de hoy no sostiene un escalón: lo muestra la [simulación](./capa2-simulacion.md) y es la primera decisión de §9.

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

### 5.3 Reglas de capa 1 por industria

Escritas en `reglas.py` y en [LOGICA](../../architecture/LOGICA.md#qué-puede-interrumpir-al-operario) en el mismo cambio. Todas `Candidata a validar`, como LOGICA.

| Regla | Industria | Condición sobre sensores | Fuente | Escenarios |
| --- | --- | --- | --- | --- |
| Orden invertido | Las tres | Llega la lectura que cierra un paso posterior mientras el paso en curso, control crítico, sigue abierto | LOGICA; 44 art. 52; 47; 48 A.1; 52 | B1, B2 |
| Control crítico deshecho | Las tres | El sensor de un control crítico verificado deja de marcar su valor antes del paso que lo deshace; se apaga en los pasos de confirmación finales | 44 art. 52; 48 A.2; 50 (m)(3)(xiii); 52 | C1, C2 |
| Guarda abierta con energía viva | Minería | `guarda = abierta` con `energia = viva` | 44, 45 | B3, C2, F5 |
| Tierra con tensión | Eléctrica | `tierra = puesta` con `tension = presente` | 50 (n)(5); 48 A.1; 49 9.1.5 | B3, C2, F5 |
| Cierre con tierras puestas | Eléctrica | `seccionador = cerrado` con `tierra = puesta` | 50 (m)(3)(xiii); 48 A.2; 49 9.1.7 | C2 y `test_reponer_el_servicio_con_las_tierras_puestas_interrumpe` |
| Persona bajo implemento levantado | Construcción | `zona = ocupada` con `implementos = levantados` | 52; 53 si la máquina opera en una mina | B3, C2, F5 |

Quedan fuera porque el demo no tiene el sensor: correa en movimiento con la guarda abierta (44 art. 116; 45 56.14112(b)), que pide velocidad, y «el candado lo saca quien lo puso» (45 56.12016), que pide identificar el candado o a la persona.

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

**Entra:** las tres pautas, los 24 patrones por industria, las reglas de §5.3 en `reglas.py`, la frescura, la declaración con su paso y el paso de cámara sin cuadro en `servicios.py`, el detector de capa 2 que no aprende de la falla, la caja aislada, `GET /escenarios` y `POST /escenarios[/{id}]/correr`, la matriz, el detalle y una sección por industria con su recorrido animado en `/casos` (`GET /industrias`), `tests/test_escenarios.py`, la simulación de capa 2 y el eval de capa 3 con su set de escenas.

**No entra:** el detector de capa 2 para equipos con ciclo de carga (§9), conectar un VLM (frente 3), juntar las imágenes del eval y patrones de relevo de turno.

## 8. Criterios de aceptación

- **CA1 —** **Dado** el catálogo, **cuando** se corre, **entonces** cada industria tiene los 24 patrones, cada patrón tiene su test en el archivo de su industria, y cada escenario sin brecha cumple lo esperado.
- **CA2 —** **Dado** un escenario con brecha, **cuando** alguien cambia el código y el escenario empieza a cumplir, **entonces** el test falla y pide quitar la marca.
- **CA3 —** **Dado** un servidor con su bitácora, **cuando** se corre la matriz, **entonces** su base no cambia.
- **CA4 —** **Dado** cualquier escenario, **cuando** se lee, **entonces** dice de dónde sale lo que espera.
- **CA5 —** **Dado** `/casos`, **cuando** se corren los escenarios, **entonces** se ve la matriz con su sello por celda, y al elegir una celda, lo esperado contra lo obtenido, la bitácora y lo que habría llegado por el stream.
- **CA6 —** **Dado** la simulación de capa 2, **cuando** se corre, **entonces** informa, por industria y detector, las falsas alarmas y si detecta y sostiene el pico, el escalón, la deriva y el sensor pegado.
- **CA8 —** **Dado** `/casos`, **cuando** se abre la sección de una industria, **entonces** se ven su trasfondo (la norma, lo que pasa cuando falla, sus reglas y sensores), su pauta y su arquitectura (tests, controladores, servicios y tablas). Al elegir un test, el recorrido de su escenario se anima tramo por tramo: qué controlador recibe, qué servicios corren y cuáles deciden, qué tablas se escriben y cómo queda cada paso de la pauta.
- **CA7 —** **Dado** un juez de cámara, **cuando** se corre el eval de capa 3, **entonces** informa la falsa aceptación, el falso rechazo y la confianza en aciertos y errores, y cuenta aparte los casos sin imagen.

Los tests: los casos de uso de cada industria en `tests/test_mineria.py`, `tests/test_electrica.py` y `tests/test_construccion.py`, 26 a 28 por industria; la matriz como un todo en `tests/test_escenarios.py` (CA1 a CA4); `tests/test_casos.py` (CA5 y CA8) y `tests/test_barreras.py` (CA6 y CA7).

## 9. Riesgos y decisiones abiertas

| Tema | Impacto | Qué falta decidir | Se consulta a | Decide |
| --- | --- | --- | --- | --- |
| Señal de carga para la capa 2 | alto fuera del demo | Con un ciclo de carga el detector de hoy sostiene un escalón 6 % del tiempo en eléctrica y 30 % en construcción. El CUSUM contra el ciclo lo sostiene entero, con 8 a 11 falsas alarmas cada 1.000 lecturas, pero necesita saber en qué parte del ciclo va el equipo. ¿Hay una señal de carga (corriente del motor o del transformador) en esas estaciones? En la correa del demo no hace falta: sin ciclo, el detector de hoy sostiene el escalón entero con 1,1 falsas alarmas cada 1.000 | Frente 3 | Francisco |
| Imágenes del eval de capa 3 | alto para el frente 3 | El set tiene 24 escenas y ninguna imagen; hoy el eval solo dice que el stub acepta los 15 pasos mal hechos. ¿Quién las fotografía en la maqueta con `/camara`? IndustReal (13) trae cuadros con errores de ejecución para una primera pasada | Frente 3 | Frente 3 |
| Lo que el edge y la app tienen que mandar | medio | Tres cambios ya hechos en la API que dependen de otros frentes. Primero, el edge reenvía cada sensor al menos cada 5 s, cambie o no; si no, la OT baja a warning por frescura. Segundo, la app manda `paso_id` al declarar; sin eso vuelve la falsa alarma de A2. Tercero, la cámara transmite durante los pasos de cámara; un cuadro de más de 10 s no cuenta | Frentes 2 y 3 | Francisco |
| Ventana de gracia (A3) | bajo | Decirlo un segundo antes de que el sensor lo vea abre un conflicto que interrumpe, como dice LOGICA. ¿Se espera unos segundos antes de declararlo? `Candidata a validar` en el ensayo | Frente 2 | Equipo |

## Fuentes

- [LOGICA](../../architecture/LOGICA.md), [ADR-0002](../../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md), [ADR-0004](../../decisions/0004-verificacion-por-capas.md), [ADR-0005](../../decisions/0005-producto-general-mineria-como-caso-del-demo.md), [ADR-0007](../../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md) y [ADR-0008](../../decisions/0008-escenarios-por-industria-en-una-caja-aislada.md).
- [CONTEXTO → Industrias](../../domain/CONTEXTO.md#industrias).
- REFERENCIAS 9, 13, 40 y 44 a 55.
