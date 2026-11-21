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

## Normas para el marco

ISO 14224, ISO 13374, ISO 17359, ISO 13381-1, EN 13306, IEC 60300-3-11, SAE JA1011, ISO 55000 e IEEE 1856. Sin enlace verificado.
