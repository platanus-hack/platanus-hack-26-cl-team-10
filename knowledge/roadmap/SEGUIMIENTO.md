# Seguimiento

> **El estado vivo del proyecto.** Único documento donde se escribe avance. Cada quien agrega y actualiza sus filas en el mismo commit que sube el trabajo. Estados: `pendiente` · `en curso` · `hecho` · `bloqueado`. Responsable `—` significa que nadie la tomó.

## Research

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Revisión bibliográfica en IEEE (117 papers) | Francisco | hecho | 2026-11-21. Hoja de NLP sobre OT en [fuentes/](../projects/research/fuentes/revision-ieee-42-papers.csv); la planilla completa la tiene Francisco |
| Intersección con la visión del operario y verificación de enlaces | Francisco | hecho | 2026-11-21. 37 referencias en [REFERENCIAS](../projects/research/REFERENCIAS.md) |
| Leer completo Sabetta et al. 2026 | Francisco | hecho | [Nota](../projects/research/notas/2026-sabetta-gemini-robotics-er.md). Originó el [ADR-0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md) |
| Pasar el planteamiento del equipo al knowledge | Francisco | hecho | 2026-11-21. [Transcripción íntegra](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md); entró a CONTEXTO, FLUJO, GLOSARIO y originó el [ADR-0004](../decisions/0004-verificacion-por-capas.md) |
| Alinear el knowledge con el planteamiento: producto general, OT desde el protocolo y predicción como visión | Francisco | hecho | 2026-11-21. [ADR-0005](../decisions/0005-producto-general-mineria-como-caso-del-demo.md), [ADR-0006](../decisions/0006-la-ot-nace-del-protocolo.md); cambiaron CONTEXTO, FLUJO y GLOSARIO |
| Costo por hora de detención de un equipo minero crítico | Francisco | en curso | Hay dos fuentes de prensa, (38) y (39): USD 100.000 a 300.000 por hora según un proveedor. Falta una fuente de operador, de Cochilco o de un estudio identificable antes de llevar la cifra al pitch |
| Subir las hojas «IEEE ampliado» (25) y «Fuera de IEEE» (50) de la planilla | Francisco | pendiente | Solo está la hoja «Papers» (42). Exportarlas a CSV en [fuentes/](../projects/research/fuentes/), idealmente con la columna de enlaces |
| Verificar las referencias mencionadas sin fuente | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#mencionadas-sin-verificar). Al verificarla, cada una recibe el número siguiente de su grupo |
| Leer completos los cinco prioritarios | — | pendiente | (20), (10), (15), (25) y (24); ver [research](../projects/research/research.md#qué-leer-primero) |
| Leer PREGO y TI-PREGO | — | pendiente | (11) y (12). Son la evidencia del aviso en el momento, y solo se leyó el resumen |
| Buscar literatura de relevo de turno en mantenimiento | — | pendiente | Sin búsqueda todavía. Punto de partida sin verificar: Piper Alpha |
| Buscar literatura del aviso por audio y de fatiga de alarmas | — | pendiente | Sin búsqueda todavía. Incluye si un auricular convive con la protección auditiva de una planta |
| Encontrar las seis referencias faltantes | — | pendiente | [Lista](../projects/research/REFERENCIAS.md#no-encontradas). La de Bate, Orchard y Tagle es la más valiosa |
| Fatalidades y controles críticos: fuentes primarias de ICMM | Daniel | hecho | 2026-11-21. Referencias (40) a (43) y [research](../projects/research/research.md#fatalidades-y-controles-críticos). La ejecución inefectiva del control, 19 de 26 incidentes fatales, sostiene el criterio de impacto |
| Aislar los accidentes en tareas de mantenimiento | — | pendiente | Fuente primaria de Sernageomin, no prensa. Para el pitch ya no bloquea: el argumento pasa por la ejecución del control (40), no por la proporción de muertes en mantenimiento |
| Abrir el PDF del benchmarking de ICMM 2025 | — | pendiente | Enlazado desde (40) y no abierto. Es la fuente más completa si se necesita el detalle por peligro |
| Encontrar el origen de «ICMM cubre un tercio de la industria» | — | pendiente | Se afirmó al preparar el pitch y ninguna fuente abierta lo dice. Hasta entonces, fuera del pitch |
| Transcribir y analizar las presentaciones del último año | Francisco | hecho | 2026-11-21. Cinco videos y 332 preguntas del jurado en [tour-platanus](../projects/research/tour-platanus.md) |
| Cerrar las brechas del banco de preguntas del jurado | — | pendiente | Modelo de visión, dónde corre, latencia, privacidad del operario, costo del kit y condiciones de faena. Ver [preguntas](../projects/research/tour-platanus.md#las-preguntas-que-nos-van-a-hacer) |
| Medir falsos positivos, falsos negativos y latencia del aviso | — | pendiente | Con el número de corridas. Es la pregunta que más le pesó a Veridian en Caracas |
| Ensayar pitch de 3 min y preguntas de 2 min | Equipo | pendiente | Con alguien que haga de jurado y las preguntas de [tour-platanus](../projects/research/tour-platanus.md#las-preguntas-que-nos-van-a-hacer) |
| Preguntar qué espera el jurado del track Physical World | — | pendiente | Ninguna edición anterior tuvo ese track |

## Construcción

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Acordar el formato de paso y de evento | Equipo | en curso | Propuesta en [LOGICA](../architecture/LOGICA.md) e implementada en `app/contratos.py`. Falta que el equipo la ratifique |
| Esqueleto del flujo: contratos, reglas, bitácora, API y recorrido del demo | Daniel | hecho | 2026-11-21. `app/` con un stub por frente, 12 pruebas de las tres reglas y `scripts/recorrido_demo.py` con los cinco momentos corriendo. Quién toca qué: `app/README.md` |
| Frente 1 · Protocolo a pasos con tipo de evidencia y pregunta visual | — | pendiente | [ADR-0006](../decisions/0006-la-ot-nace-del-protocolo.md). Sigue el stub en `app/protocolos.py`: las pautas del demo se escriben a mano en `datos/` |
| Frente 2 · App del operario: voz de ida y vuelta, un paso a la vez | Daniel y Diego | en curso | El orden lo impone la app ([ADR-0002](../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md)). App React en `web/` con voz por ElevenLabs (`app/voz.py`) y pantallas de supervisor, en la rama `feat/front-y-servicios`, sin integrar a `main`. Llama a `POST /ot/{id}/asignar`, que la API todavía no tiene |
| Frente 3 · Verificación: capa 1 con sensores, capa 3 con cámara | Jonathan | hecho | 2026-11-21. Solo la capa 1 interrumpe ([ADR-0004](../decisions/0004-verificacion-por-capas.md)). Capa 2 de cámara con YOLO del edge (`reglas.por_deteccion`) y capa 3 con Claude Haiku 5.5 (`app/verificacion.py`), #14. Falta una llamada real al juez medida con imágenes: ver el eval de capa 3 |
| Frente 4 · Registro de eventos, relevo de turno y vista del supervisor | — | pendiente | El relevo es una lectura de los eventos, no un documento aparte. La bitácora y `estado_de_ot` están; `cerebro.responder` sigue siendo un stub sin modelo |
| Edge: ESP32, cámara USB y YOLO-World en el Mac hacia el servidor | Jonathan | hecho | 2026-11-21. Video a 20 fps, detecciones en vivo y capa 2 de sensores calibrada con lecturas reales (#12). El hilo de sensores reintenta y reabre el puerto tras 10 s sin datos (#15, #16). Se lanza con `edge/correr_edge.command` o `edge/correr_edge_vm.command` |
| Demo LOTO en el home: pauta, sensores en vivo y declarar paso | Jonathan | hecho | 2026-11-21. `datos/pauta-loto.json` (#14); `/` es el monitor de la demo y abre la OT que el edge ejecuta (#17, #18); los pasos de cámara cierran en la VM (#20) |
| YOLO en el servidor (ONNX) en vez del edge | Jonathan | en curso | Experimento en la rama `exp/yolo-servidor` |
| Servicios en vivo: sesión por edge, stream por OT, calificación por capa y CRUD con reglas de negocio | Francisco | en curso | [PRD](../projects/servicios-en-vivo/PRD.md) y [ADR-0007](../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md). Recorrido animado en [servicios.html](../architecture/servicios.html). Desplegado en `https://34-176-44-192.sslip.io`, guía para agentes en `/agente` |
| Banco de pruebas `/casos`: cada criterio del PRD corrido contra un servidor vivo | Francisco | hecho | 2026-11-21. CA1 a CA17 pasan contra local con el código integrado con `main` (16 de 16 tarjetas; CA15 es el banco mismo). Falta correrlo contra la VM: ver [Servicios: estado y resultados](#servicios-estado-y-resultados) |
| Escenarios por industria: 24 patrones × minería, eléctrica y construcción contra cada barrera | Francisco | hecho | 2026-11-21. [PRD](../projects/escenarios-por-industria/PRD.md) y [ADR-0008](../decisions/0008-escenarios-por-industria-en-una-caja-aislada.md). Los 72 escenarios pasan, con un archivo de tests por industria y una sección por industria en `/casos`. Reglas por industria, orden invertido, control perdido y confirmación por persona en `reglas.py`, `servicios.py` y [LOGICA](../architecture/LOGICA.md). Abierto: [§9 del PRD](../projects/escenarios-por-industria/PRD.md#9-riesgos-y-decisiones-abiertas) |
| Regla de seguridad del demo: guarda abierta con energía viva | — | hecho | Capa 1, independiente del paso en curso, en `app/reglas.py` ([LOGICA](../architecture/LOGICA.md#qué-puede-interrumpir-al-operario)). La pauta LOTO del demo no monta sensor de guarda, así que hoy no aparece en vivo |

## Servicios: estado y resultados

Al 2026-11-21, con `dreamxist/services` integrada con `main` (YOLO en capa 2 de cámara, Claude Haiku 5.5 como juez de capa 3, pauta LOTO, SQLite serializada y edge). Dueño: Francisco. Para retomar, se parte de acá.

**Qué hay.** Toda la API de servicios vive en `app/`, y [app/README.md](../../app/README.md) dice qué archivo hace qué:

- sesión por edge, stream por OT, calificación por capa y CRUD con reglas ([PRD](../projects/servicios-en-vivo/PRD.md), CA1 a CA17);
- reglas de capa 1 por industria, más orden invertido y control perdido ([LOGICA](../architecture/LOGICA.md#qué-puede-interrumpir-al-operario));
- la confirmación por persona contra el sensor, `POST /ot/{id}/pasos/{paso}/confirmar` ([LOGICA](../architecture/LOGICA.md#cuando-la-persona-y-el-sensor-no-coinciden));
- la matriz de escenarios por industria en una caja aislada ([PRD](../projects/escenarios-por-industria/PRD.md));
- el banco `/casos`, con una sección por industria que anima el recorrido de cada test;
- la [simulación de capa 2](../projects/escenarios-por-industria/capa2-simulacion.md) y el eval de capa 3, `scripts/evaluar_capa3.py`.

El recorrido animado de una lectura está en [servicios.html](../architecture/servicios.html).

**Resultados.**

| Verificación | Comando | Resultado |
|---|---|---|
| Tests unitarios y de casos de uso | `uv run --with httpx python -m unittest discover tests` | 240 pasan, 0 fallan. También corre con `pytest` |
| De esos, por industria | `python3 -m unittest tests.test_mineria tests.test_electrica tests.test_construccion` | 27, 26 y 26 pasan |
| Recorrido del demo | `python3 scripts/recorrido_demo.py` | Pauta completa, 11 eventos, ninguno editado |
| Banco contra local | `uv run python scripts/correr_casos.py http://localhost:8000` | 16 de 16 tarjetas pasan (CA1 a CA17), con y sin `CLAVE_EQUIPO` en el servidor |
| Matriz de escenarios | `POST /escenarios/correr` | 72 de 72 pasan, 0 brechas abiertas |
| Simulación de capa 2 | `python3 scripts/simular_capa2.py` | Sin ciclo de carga (minería), el detector de hoy sostiene un escalón 100 % con 0,9 falsas alarmas cada 1.000. Con ciclo (eléctrica, construcción), lo sostiene 6 % y 30 %; el CUSUM contra el ciclo, 100 % |
| Eval de capa 3 | `python3 scripts/evaluar_capa3.py` | 24 escenas sin imagen. El juez sin cuadro responde el stub: acepta 15 de 15 pasos mal hechos. Mide al VLM real cuando haya imágenes y `ANTHROPIC_API_KEY` |
| Contra la VM, desplegada el 2026-11-21 a las 12:25 UTC con `CUENTA=francisco@imclabs.com deploy/vm/desplegar.sh` | `/casos` en `https://34-176-44-192.sslip.io` | Las páginas responden 200 y los 72 escenarios pasan. De las tarjetas pasan CA8, CA9, CA10 y CA14, las que no tocan sensores. El resto no se corrió porque había una sesión LOTO activa de otra persona (`edge-mac`) y el banco pisaría sus sensores globales |

**Lo que depende de otros frentes.**

- El edge reenvía cada sensor al menos cada 5 s; si no, la OT baja a warning por frescura.
- La app manda `paso_id` al declarar.
- La cámara transmite en los pasos de cámara; un cuadro de más de 10 s no cuenta.

**Decisiones abiertas.** Las cuatro primeras se discuten en el [§9 del PRD de escenarios](../projects/escenarios-por-industria/PRD.md#9-riesgos-y-decisiones-abiertas).

- Quién puede confirmar un control crítico contra el sensor: cualquier persona, como hoy, o solo un supervisor.
- Si hay una señal de carga para la capa 2 en eléctrica y construcción.
- Quién fotografía las escenas del eval de capa 3.
- La ventana de gracia de A3.
- El costo de la VM: la estimación da 18 a 24 USD al mes, y el tope fijado es unos 20.
- La API es pública. Con `CLAVE_EQUIPO` en el servidor, quitarle un edge a la OT que ejecuta, o soltarlo, pide la cabecera `X-Clave-Equipo` (CA17), y sin la clave el home queda de solo lectura: no muestra «Nueva demo LOTO» ni «Declarar paso». Se entra una vez con `?clave=` y queda en el navegador. Falta ponerla en `/srv/factum/entorno` de la VM y desplegar; hasta entonces el servidor sigue abierto. Queda abierto a propósito: las lecturas del edge, `/declarar` y `/confirmar` no piden clave, así que esto frena el clic de un visitante, no a quien llame a la API a mano. El gasto está acotado: video de hasta 8 edges y 3.000 llamadas al juez de cámara por proceso (`VLM_MAX_LLAMADAS`).

## Decisiones abiertas

| Tarea | Responsable | Estado | Notas |
|---|---|---|---|
| Aceptar o rechazar los ADR 0002 a 0006 y la decisión de dejar la predicción como visión | Equipo | pendiente | Ver el [registro](../decisions/decisions.md). El 0001 quedó reemplazado por el 0005 |
| ¿Hay hardware a mano para el demo? | Equipo | hecho | Sí: Arduino, Raspberry Pi, ESP, sensores, receptores y motores ([planteamiento](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md)) |
| ¿El demo es la correa a escala con el bloqueo saltado? | Equipo | pendiente | Ver [Demo propuesto](../architecture/FLUJO.md#demo-propuesto). Lo construido es la pauta LOTO con ESP32 y cámara (#14, #17), no la correa. Falta decidir si `web/` o el home de `app/estatico/` es la pantalla del demo |
| ¿La predicción de fallas y la OT automática siguen en el alcance del demo? | Francisco | hecho | 2026-11-21. No: quedan como visión ([registro](../decisions/decisions.md)). Falta que el equipo la acepte |
| Formato del relevo de turno | Equipo | pendiente | Resumen, consultas o *briefing*. Propuesta en [LOGICA](../architecture/LOGICA.md#relevo-de-turno): lectura de los eventos, registro completo al modelo y sin base vectorial |
| Canal del aviso al operario | Equipo | pendiente | El equipo propone un auricular. Confirmar qué dispositivo es «la muela» de la transcripción |
| Algoritmo de la capa de aprendizaje automático | Equipo | pendiente | Para el demo basta un umbral ([ADR-0004](../decisions/0004-verificacion-por-capas.md)) |
| ¿Hay OT reales de alguna faena? | — | pendiente | Sin ellas, el corpus sale de MaintIE (6) |
