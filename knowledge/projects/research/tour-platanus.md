# Lo que enseñan las presentaciones del último año

> Research del 2026-11-21 sobre las presentaciones finales de las cinco ediciones de Platanus Hack de los últimos doce meses: Santiago 2025 y las cuatro paradas del Latam Tour 26. Responde tres preguntas: qué tracks hubo, qué pregunta el jurado y qué ganó. Termina con las preguntas que nos van a hacer y con lo que tenemos que traer resuelto.

## De dónde sale

Hay cinco videos del canal de Platanus en YouTube. De cada uno se bajó la transcripción automática en español y se partió por los capítulos de la descripción, que son un proyecto por capítulo. Un agente por video extrajo el formato, los tracks, las preguntas del jurado y los ganadores, y escribió una nota por edición. Los criterios, los ganadores generales y el viaje a Chile se verificaron contra la transcripción.

La transcripción es automática y no se corrigió, así que los nombres propios pueden venir mal escritos. Las citas son paráfrasis cercanas, salvo las que van entre comillas.

| Edición | Fecha | Tracks | Proyectos | Ganador general | Nota | Transcripción |
|---|---|---|---|---|---|---|
| Hack 25 · Santiago ft. Buk | 2025-11-23 | Legacy, Consumer AI, Human Enhancement, Fintech + Digital Security | 45 | `Brecha`: el video no trae la premiación | [nota](./tour/2025-11-23-hack-25-santiago.md) | [texto](./fuentes/videos-platanus/2025-11-23-hack-25-santiago.md) · [video](https://www.youtube.com/watch?v=1BkgjK1RQm0) |
| Hack 26 · Buenos Aires | 2026-05-10 | Vertical AI, AI Security, Future, Agentic Money | 25 | Tranquera (AI Security) | [nota](./tour/2026-05-10-hack-26-buenos-aires.md) | [texto](./fuentes/videos-platanus/2026-05-10-hack-26-buenos-aires.md) · [video](https://www.youtube.com/watch?v=JP7laiGtB8o) |
| Hack 26 · CDMX | 2026-06-21 | Legacy, AI Security, New Interfaces, New Media | 21 | Dominikito (?), New Media. El audio de la premiación casi no se entiende | [nota](./tour/2026-06-21-hack-26-cdmx.md) | [texto](./fuentes/videos-platanus/2026-06-21-hack-26-cdmx.md) · [video](https://www.youtube.com/watch?v=LUvJUPFiDVY) |
| Hack 26 · Bogotá | 2026-08-23 | Emergencies, Simulations, Access, AI Security | 24 | WOKI (Emergencies), por 0,25 puntos sobre Peaje | [nota](./tour/2026-08-23-hack-26-bogota.md) | [texto](./fuentes/videos-platanus/2026-08-23-hack-26-bogota.md) · [video](https://www.youtube.com/watch?v=5Yn687MW-_A) |
| Hack 26 · Caracas | 2026-10-26 | Trust, Three-Dimensional, AI Security, Emergencies | 22 | mus3o (Three-Dimensional), con 80,7 de 100 | [nota](./tour/2026-10-26-hack-26-caracas.md) | [texto](./fuentes/videos-platanus/2026-10-26-hack-26-caracas.md) · [video](https://www.youtube.com/watch?v=6mIvorbU_T0) |

El canal tiene además la *Build Night* de Bogotá y el debate de superinteligencia con Kairos y Buk. No se transcribieron porque no son presentaciones con jurado.

## Lo que cambia decisiones

1. **Los ganadores de cada parada compiten contra nosotros.** En Buenos Aires, Bogotá y Caracas el premio incluye un pasaje para competir en la final de Santiago en noviembre, y al ganador de Chile Platanus le paga el viaje a San Francisco. Así que en la sala van a estar Tranquera, WOKI, mus3o y probablemente el ganador de CDMX, todos con un proyecto que ya ganó una vez. `Confirmada` en las transcripciones de Buenos Aires [4:44:42] y Bogotá [5:01:45–5:03:06], y en la nota de Caracas.
2. **El hardware real que funciona en vivo gana.** WOKI, ganador general de Bogotá, fue el único proyecto con hardware propio: nodos LoRa y ESP32, todo sin conexión, mostrado en vivo con compañeros colgados de un poste. Su frase de cierre fue «todo funciona, lo pueden descargar y verificar». SmartTraffic ganó Trust en Caracas con una cámara real y YOLO, montada en un ascensor que hacía de semáforo. `Confirmada`.
3. **Nadie ha presentado algo como lo nuestro.** En 137 proyectos no hubo ninguno de minería, mantenimiento industrial, seguridad laboral ni visión por computador sobre operarios. Tampoco hubo un track Physical AI en ninguna de las cinco ediciones, así que no sabemos qué pide ese jurado en particular. Lo más cercano fue Tridi, en Caracas, que genera datos de movimiento para entrenar robots y se presentó como *physical AI* en el track Three-Dimensional. No quedó en el podio, y le preguntaron si reinventaba lo que ya hacen Tesla o Figure y con cuántos videos entrenó. El hueco ayuda a la originalidad, pero no deja precedente. `Confirmada` hasta donde llegan las transcripciones.
4. **El jurado lee el código.** En CDMX y Bogotá el host explicó que los jueces abren el repositorio con agentes para ver si hay «ingeniería detrás», y en dos casos citaron el código en las preguntas. A Huella SOS le encontraron en el repo pesos sin calibrar. Lo que digamos en el pitch tiene que estar en el código. `Confirmada`.
5. **Un demo simulado se castiga en público.** A Hop lo expusieron por simular la integración, a facturin por usar fotos ideales y a Consentinel se le coló un *happy path* por un umbral mal puesto. A Veridian le pesó decir que su 3% de falsos positivos lo midieron ellos mismos. `Confirmada`.

## Formato y criterios

El formato se repitió en las cuatro paradas del tour. `Confirmada`:

- 3 minutos de demo con corte estricto, 2 minutos de preguntas solo de los jueces y alrededor de 1:30 para que evalúen.
- El proyecto tiene que estar desplegado y ser open source.
- Los criterios son los mismos de [CONTEXTO](../../domain/CONTEXTO.md#cómo-nos-evalúan): aspecto técnico 25%, ambición 20%, ejecución 20%, impacto 20% y originalidad 15%. Los pesos se dijeron en CDMX y Caracas. Cada juez pone de 0 a 5 por criterio y su nota se normaliza contra todas las que puso.
- El modelo de negocio queda fuera de la evaluación. Igual lo preguntan: en Caracas salió seis veces y en Buenos Aires once.

En Santiago 2025 el pitch duraba unos 3 minutos y las preguntas de 1 a 3 minutos. El programa de Santiago 2026 tiene dos rondas, «Presentaciones Generales» y «Presentaciones Finales», y una charla el sábado sobre «Cómo hacer un buen demo» ([sitio](https://hack.platan.us/26-cl)). `Confirmada`.

## Qué pregunta el jurado

Se contaron 332 preguntas en las cinco ediciones. La técnica es la primera o la segunda categoría en todas.

| Categoría | Santiago 25 | Buenos Aires | CDMX | Bogotá | Caracas | Ejemplo |
|---|---|---|---|---|---|---|
| Técnica y arquitectura: qué modelo, dónde corre, qué fue lo más difícil | 41 | 19 | 14 | 22 | 12 | «¿Pesos de YOLO ya entrenados o *fine tuning*? ¿Con qué datos lo probaron?» (SmartTraffic) |
| Usuario, cliente, quién paga y adopción | 25 | 21 | 5 | 13 | 6 | «¿Qué incentivo tiene el que tiene que usarlo?» (MCD, brunito) |
| Diferenciación y por qué no algo más simple | 4 | 4 | 5 | 7 | 13 | «¿Qué ventaja tiene frente a un simple botón SOS?» (Aló Mamá) |
| Qué es real y qué es mock | 16 | 6 | 2 | 3 | 3 | «¿Hasta dónde llegaron?» (Hop) |
| Precisión, falsos positivos y qué pasa si se equivoca | 7 | 1 | 8 | 4 | 6 | «Si se equivoca es grave, ¿no?» (MyEyesTalk) |
| Datos, privacidad y seguridad | 6 | 3 | 4 | 3 | 2 | «¿Cómo prevengo que mi jefe pueda preguntar si fui al baño?» (Omni) |
| Total contado, con el resto de categorías | 113 | 62 | 38 | 64 | 55 | |

Cada agente armó sus propias categorías, y acá se juntaron las equivalentes, así que los conteos sirven para ordenar, no para sumar al detalle. En Bogotá hubo además 10 preguntas sobre de dónde salen los datos y cómo se mantienen al día, y en Caracas 6 sobre decisiones de diseño del tipo «¿por qué X y no Y?».

## Las preguntas que nos van a hacer

Estas son las que salieron a proyectos parecidos al nuestro, traducidas a nuestro caso. La respuesta es un borrador del equipo, `Candidata a validar`, y la última columna dice qué tiene que existir para poder darla.

| Pregunta probable | De dónde sale | Borrador de respuesta | Qué tenemos que traer |
|---|---|---|---|
| ¿Qué es real y qué es mock en el demo? | Hop, Orbit, Replica, SkillLab | Cámara, sensores y aviso corren en vivo sobre la correa a escala. La OT de entrada es una pauta real o de MaintIE. | Una lista honesta de qué es real, dicha antes de que la pidan |
| ¿Qué pasa si das un paso por cumplido sin que lo esté, o si alertas de más? | MyEyesTalk, Veridian, Huella SOS | La capa determinista (sensor y orden de la pauta) manda sobre la del modelo, y un paso dudoso queda pendiente, no aprobado ([ADR-0004](../../decisions/0004-verificacion-por-capas.md)). | Un número de falsos positivos y negativos medido en nuestras pruebas, y cuántas pruebas fueron |
| ¿Qué modelo de visión usan, preentrenado o ajustado, y con qué datos? | SmartTraffic, faro, Tridi | `Brecha`: el modelo no está decidido. | El modelo elegido, por qué ese y con qué se probó |
| ¿Dónde corre y con qué latencia? ¿Qué pasa si el aviso llega tarde? | faro, SafeLine, SENDA, Beto | `Brecha`: hay que decidir entre el equipo (Raspberry o ESP) y la nube. | La latencia medida del paso saltado al aviso en el auricular |
| ¿Por qué cámara y sensores y no un checklist digital? ¿Por qué un LLM y no un clasificador? | Aló Mamá, HAWK, Provenance Firewall | El checklist muestra el paso siguiente, pero no comprueba que el anterior se hizo (REFERENCIAS 18). El LLM no decide solo: hay reglas y sensores debajo. | Que el demo muestre el salto que un checklist no ve |
| ¿Quién paga y qué incentivo tiene el operario para no apagarlo? | MCD, brunito, Omni | Paga la minera o la contratista por la detención que se evita. Al operario le sirve como respaldo de que hizo bien el trabajo, y en el relevo de turno. | Una cifra de costo por hora con fuente de operador, que hoy está `en curso` en [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md) |
| ¿Cómo evitas que el jefe use la cámara para vigilarme? | Omni | `Brecha`: no hay postura escrita sobre privacidad del operario. | Una respuesta de una frase: qué se graba, quién lo ve y cuánto dura |
| ¿Qué pasa en faena real, con polvo, poca luz, ruido o sin señal? | Tiqn, WOKI, Roxy, Meshy | `Brecha`. | Saber qué falla primero y decirlo antes de que lo pregunten |
| ¿Cómo se instala en una faena y cuánto cuesta el hardware? | WOKI | `Brecha`. | El costo del kit del demo y qué cambia a escala real |
| ¿De dónde salen las pautas y cómo se mantienen al día? | PULSO, complAI, Vity | De los procedimientos que la minera ya tiene. Con N ejecuciones, el sistema propone mejoras. | Una pauta de ejemplo cargada en el demo |
| ¿Qué te defiende de que un proveedor grande lo saque como *feature*? | yieldOS, Tridi | Nadie convierte hoy la ejecución verificada en bitácora (ver [Vacíos](./research.md#vacíos)). | Que la bitácora generada se vea en el demo |

## Plan

Los pasos 1 a 3 se hicieron en esta pasada. Los siguientes son para el equipo y quedan en [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md).

1. Ubicar los videos del último año y bajar sus transcripciones (hecho).
2. Extraer por edición el formato, los tracks, las preguntas y los ganadores (hecho, en [tour/](./tour/)).
3. Cruzar las preguntas con nuestro proyecto (hecho, la tabla de arriba).
4. Cerrar las `Brecha` de la tabla de preguntas: modelo de visión, dónde corre, latencia, privacidad, costo del kit y condiciones de faena. Varias dependen de decisiones abiertas en [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md).
5. Medir en nuestras pruebas falsos positivos, falsos negativos y latencia, y anotar cuántas corridas son. Es lo que le faltó a Veridian.
6. Ensayar el pitch en 3 minutos con corte, y las preguntas de la tabla en 2 minutos, con alguien que haga de jurado.
7. Antes de la entrega, revisar el repo como lo haría un juez con un agente: que el README diga qué hace cada parte y que no queden umbrales sin explicar.
8. Preguntar a los organizadores en Santiago qué espera el jurado del track Physical AI, porque ninguna edición anterior lo tuvo.

## Lo que falta

- Ganadores de Santiago 2025: el video termina en el último pitch. `Brecha`.
- Ganador general de CDMX: el audio de la premiación casi no se entiende. `Brecha`.
- Qué juez hizo cada pregunta: las transcripciones no lo distinguen. `Brecha`.
- Por qué ganó cada proyecto: en la premiación solo se leen puntajes. `Brecha`.
