# Research

> Qué encontramos, dónde está la originalidad y qué leer primero. Los números entre paréntesis remiten a [REFERENCIAS](./REFERENCIAS.md).

## Cómo se buscó

La primera pasada fue una revisión en IEEE Xplore de 117 papers, hecha por Francisco el 2026-11-21. Todas las búsquedas fueron sobre el abstract (Command Search):

- OT, bitácoras o registros de mantenimiento AND (NLP, text mining o LLM).
- OT o bitácoras AND (sensores, SCADA o telemetría) AND (predicción o pronóstico).
- Términos mineros (haul truck, SAG mill, open-pit, mining equipment) AND (PdM, RUL, condition monitoring o fault diagnosis).
- (Mantenimiento o montaje) AND (action/step recognition o egocentric) AND (verificación, errores o AR).

La hoja «Papers» de esa revisión, con 42 papers de NLP sobre OT, está en [fuentes/](./fuentes/revision-ieee-42-papers.csv). Los enlaces de la planilla original se perdieron al exportar a CSV.

La segunda pasada buscó fuera de IEEE la intersección con la visión del operario (ejecución verificada, seguridad y bitácora), y verificó que cada referencia existe. De ahí salen las 37 de [REFERENCIAS](./REFERENCIAS.md).

## El área y sus referentes

El área se llama *Technical Language Processing* (1). Los referentes son NIST (Brundage, Sexton) y el grupo de Hodkiewicz en la University of Western Australia, que trabaja con OT mineras (3), (4), (5), (6). Lo más parecido al ciclo completo es el trabajo de IBM en ACL 2026, que cruza OT, sensores y FMEA con un verificador (25).

## Vacíos

Ningún paper cubre la intersección completa, y ahí está la originalidad. `Confirmada` hasta donde llegó la búsqueda.

| Paper | Verifica con visión | Bitácora | Sensores | Seguridad | Terreno real |
|---|---|---|---|---|---|
| Carga de combustibles (20) | ✓ | — | — | ✓ | ✓ |
| O'Donncha et al. (25) | Verificador de texto | ✓ | ✓ | — | ✓ |
| Aqueveque et al. (24) | — | — | ✓ | — | ✓ Minería |
| Sabetta et al. (9) | ✓ | — | — | — | Montaje en mesa |
| EgoOops (10) | ✓ Contra el texto de la pauta | — | — | — | — |
| ENIGMA-51 (17) | ✓ | — | — | — | Reparación de tarjetas eléctricas |
| Seminara et al. (15) | ✓ Y aprende el proceso | — | — | — | — |
| Plant Memory (7) | — | ✓ | — | — | ✓ Una planta |
| Peres et al. (33) | — | — | — | ✓ | ✓ Petroquímica |
| Tesis de Cal Poly (23) | Candados inteligentes, sin cámara | ✓ | — | ✓ | Piloto industrial |

1. **Nadie convierte la ejecución verificada en la bitácora.** Solo hay proveedores que adjuntan un clip a la OT.
2. **No hay verificación de bloqueo y etiquetado con cámara revisada por pares.** Solo proveedores (Roboflow, iFactory) y una tesis con candados inteligentes (23).
3. **Nada de esto se ha probado en equipo pesado ni en minería.** Los datasets de errores de procedimiento son de cocina, juguetes, muebles o tarjetas eléctricas. El único caso en terreno real es la carga de combustibles (20).
4. **Nadie cruza el texto de las OT con telemetría usando datos mineros reales.**
5. **No hay un ciclo cerrado que actualice las pautas.** Lo que existe se apoya en FMEA o en cálculos de confiabilidad.

Y lo que todavía no funciona: un VLM general detecta 3 de 12 cambios de orden y rechaza 5 de 12 ejecuciones correctas (9). Eso condiciona el diseño: ver [ADR-0002](../../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md).

## Evidencia frente al planteamiento del equipo

El [planteamiento del 2026-11-21](../../domain/fuentes/2026-11-21-planteamiento-del-equipo.md) agregó ideas que la primera búsqueda no cubría. Esto dice lo que ya tenemos sobre cada una:

| Lo que plantea el equipo | Lo que dice la evidencia | Estado |
|---|---|---|
| Avisar en el momento que se saltó un paso | Es lo que un VLM general detecta mejor: 12 de 12, pero sobre el video completo y no en vivo (9). PREGO detecta el error mientras ocurre (11), (12); solo se leyó el resumen | `Candidata a validar` |
| Avisar un error de orden | Un VLM general lo detecta en 3 de 12 (9). Con sensores con marca de tiempo el orden no depende del modelo: [ADR-0004](../../decisions/0004-verificacion-por-capas.md) | `Candidata a validar` |
| No depender solo de un LLM | O'Donncha et al. ponen un verificador determinista entre el modelo y la respuesta (25) | `Confirmada` |
| Entregar un protocolo tras una ejecución observada | Sin pauta, el VLM describió el 54,6% de las fases (9). Es un borrador que el experto corrige | `Confirmada` |
| Un paso que muchos se saltan apunta a la pauta | Coincide con Peres et al.: muchas desviaciones nacen de pautas mal hechas y de la presión de la jefatura (33). En un paso de seguridad, que se salte seguido no lo vuelve prescindible | `Candidata a validar` |
| El supervisor va donde más se saltan pasos | Si la presión de la jefatura causa parte de las desviaciones (33), usar el dato para vigilar personas puede empeorarlas | `Candidata a validar` |
| USD 300.000 por hora de correa detenida | Es el tope del rango que da un proveedor, USD 100.000 a 300.000 (38). El sector habla de USD 40.000 a más de 200.000 (39) | `Candidata a validar` |
| Relevo de turno con resumen | No se buscó literatura | `Brecha` |
| Aviso por audio en el oído | No se buscó literatura sobre el canal ni sobre fatiga de alarmas | `Brecha` |

## Fatalidades y controles críticos

Buscado el 2026-11-21 para sostener el criterio de impacto con algo mejor que una estimación de proveedor. Las cuatro referencias nuevas, (40) a (43), son de ICMM y de prensa.

El dato que más sirve es de la fuente primaria y es casi literal a la tesis del producto: la **«ejecución inefectiva del control» fue la falla más común en los incidentes fatales de 2025, en 19 de 26** (40). `Confirmada`. No es que falte el control: el control existía y se ejecutó mal. Eso es exactamente lo que el flujo verifica paso a paso.

El mismo reporte pide foco en la identificación, implementación y **verificación** de los controles críticos, y entre los peligros de alta consecuencia nombra el **aislamiento de energía** (40). `Confirmada`. El aislamiento de energía es el bloqueo y etiquetado, que es el paso que el demo pone al centro: la línea va de la fuente primaria de la industria al momento que el jurado va a ver.

Escala, para dimensionar: 39 fallecidos en 2025 entre los 26 miembros de ICMM, 43 en 2024 y 35 en 2023, con tendencia al alza desde 2021 (41), (42). Sudamérica y África, once cada una; Chile, seis, y uno de los dos incidentes catastróficos del año fue en Chile (42). `Confirmada`.

### Lo que esto corrige del encuadre

El [CONTEXTO](../../domain/CONTEXTO.md) declaraba `Brecha` cuántas de las muertes mineras ocurren en tareas de mantenimiento. La respuesta honesta es que **no son la mayoría**: caída de roca, equipo móvil, trabajo en altura e irrupción explican 34 de los 39 (42). `Confirmada`.

Por eso el argumento de impacto no es «los malos protocolos matan mineros», que las cifras no sostienen. El argumento es el de ICMM, y pesa más porque viene de la propia industria: los riesgos y sus controles ya se conocen, y lo que falla es **ejecutar y verificar** el control. Ese reencuadre también sirve al [ADR-0005](../../decisions/0005-producto-general-mineria-como-caso-del-demo.md): la ejecución inefectiva de un control no es un problema minero, es un problema de cualquier operación con procedimientos críticos.

### Lo que no se usa

«Los miembros de ICMM cubren cerca de un tercio de la industria» se afirmó al preparar el pitch y ninguna de las fuentes abiertas lo dice. Fuera del pitch hasta encontrar el origen. Lo mismo con las 592 muertes de minería artesanal: el enlace no se abrió. Ver REFERENCIAS, «Mencionadas, sin verificar».

## Correcciones a la revisión original

Al verificar las referencias, dos no dicen lo que anotó la planilla. `Confirmada`.

- **Bikaun y Hodkiewicz 2021 (4)** no trata el sesgo de los técnicos. Muestra que el MTBF de un mismo equipo va de 97 a 226 días según cómo el analista agrupe las OT. Para los errores al registrar, la referencia es (3).
- **Peres et al. 2020 (33)** es de petroquímica, no de mantenimiento. Muestra que muchas desviaciones de la pauta vienen de la presión de la jefatura.

Seis referencias de la planilla no aparecieron en la web abierta: ver el final de [REFERENCIAS](./REFERENCIAS.md#no-encontradas).

## Qué leer primero

Si alcanzan a leer cinco: la carga de combustibles (20), porque es el caso en terreno real; EgoOops (10), porque verifica contra el texto de la pauta; Seminara et al. (15), porque identifica el proceso y verifica con un mismo modelo; O'Donncha et al. (25), para diferenciarse del lado de OT y sensores; y Aqueveque et al. (24), para la entrada sin integración en minería. Sabetta et al. (9) ya está leído completo.

## Datos y código para partir

- **MaintIE** (6): 1.076 OT anotadas en detalle y 7.000 más en grueso. Sirve como corpus de OT reales si no hay datos de faena.
- **MSHA** (37): accidentes mineros de EE.UU. desde 1983, con tipo, causa y ocupación.
- **IndustReal** (13): 84 videos con errores de ejecución, con código y pesos.
- **ENIGMA-51** (17): 22 horas de reparación de tarjetas eléctricas en primera persona.
- **AssetOpsBench** (25): sensores, OT, alertas y FMEA para agentes.

## Advertencias de la planilla original

- Los «¿?» de la planilla significan que el resumen de IEEE no lo decía; hay que confirmarlo al leer el paper.
- Varios papers de la hoja «Fuera de IEEE» son solo preprints de arXiv, a dos revisiones de realidad aumentada les falta el DOI y uno es una tesis. Está marcado en su columna «Nota».
- La columna «Industria» de Hodkiewicz y Ho 2016 dice «probablemente minería», sin confirmar.
- El siguiente paso que proponía la planilla: filtrar «Prioridad = Alta» (unos 60 papers), marcar «Estado» como Leído, Citar o Descartado y armar el estado del arte con los marcados «Citar».

## Realidad aumentada

Como interfaz, la descartamos: se acerca a la simulación y no es lo que buscamos. De Manuri et al. (18) y ENIGMA-51 (17) se toma otra cosa: el algoritmo que valida cada paso por su estado final y la grabación de reparaciones reales.

## Términos para seguir buscando

La literatura no usa nuestras palabras. Estos son los términos académicos de cada idea:

| Idea del equipo | Término académico |
|---|---|
| Entrar sin integración | *Plug-and-produce*, *retrofitting* de máquinas antiguas, *IIoT retrofitting legacy machines* |
| Identificar procesos | *Procedure learning* en video, *process mining* en registros |
| Estandarizar | *Standard work* (Lean y TPM), *task graphs* |
| Verificar la ejecución | *Procedural mistake detection*, *procedure step recognition*, *egocentric* |
| Predecir sin historia | Detección de anomalías *zero-shot* o *cold-start*, modelos fundacionales de series de tiempo |
| Interoperar con lo que existe | ISO 13374, MIMOSA OSA-CBM |

## Normas para el marco

ISO 14224, ISO 13374, ISO 17359, ISO 13381-1, EN 13306, IEC 60300-3-11, SAE JA1011, ISO 55000 e IEEE 1856. Sin enlace verificado.
