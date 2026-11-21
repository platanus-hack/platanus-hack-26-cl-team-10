# Platanus Hack 26 · Caracas (oct-2026)

> Fuente: [transcripción](../fuentes/videos-platanus/2026-10-26-hack-26-caracas.md) · [video](https://www.youtube.com/watch?v=6mIvorbU_T0). Extraído por un agente de la transcripción automática; las citas son paráfrasis cercanas salvo que vayan entre comillas.

## Formato

- **Contexto del tour** [0:00:36]: es la cuarta hackathon del año fuera de Chile (Buenos Aires, Ciudad de México, Bogotá, Caracas); la última del año es en Chile.
- **Sede y anfitrión** [0:01:10]: oficina de Yomi/Yumi (?). Su CTO, Ignacio, da la bienvenida y pregunta cuántos van a su primera hackathon: "como la mitad".
- **Postulación** [0:04:30]: más de 400 postulaciones; en la sala hay 100 hackers.
- **Qué se evalúa** [0:06:45]: "de cero a producto en 36 horas", entendiendo producto como solución e implementación técnica, "dejando por esta competencia de lado la parte de modelo de negocios". Igual el jurado preguntó por negocio (ver más abajo).
- **Reglas** [0:07:19]: 36 horas, alojamiento en la sede, apps deployadas, todo open source, interacción con mentores. Cada equipo tuvo un mentor desde el brainstorming hasta la implementación [0:06:10].
- **Sponsors** [0:04:30, 0:07:19, 0:12:50]: Anthropic (créditos de Claude para cada hacker), Yomi/Yumi (?) (sede), Eleven Labs, Capso (?), Render, Cacheado/Cachea (?) y Supabase (camisetas del mercado).
- **Jurado** [0:09:30–0:10:03]:
  - Diego Ramos, CTO de Dugu (?), startup early stage de e-commerce para mascotas; estudió ingeniería y medicina en paralelo.
  - Ignacio, CTO de Yomi/Yumi (?), que se presenta como "la empresa de tecnología más icónica de Venezuela".
  - Juan Vargas (?), founder de Big Bob (?), software factory chilena que también ayudó a organizar.
  - Brecha: la transcripción no dice qué juez hizo cada pregunta.
- **Criterios y pesos** [0:10:03]: originalidad 15%, ambición 20%, ejecución 20%, aspecto técnico 25%, impacto 20%.
- **Puntaje** [0:10:36]:
  1. Cada juez pone de 0 a 5 en cada dimensión.
  2. Se normaliza a cada juez según todas las notas que puso.
  3. Se promedia entre jueces y se pondera por criterio.
  4. Se lleva a una escala lineal de 0 a 100.
  - Lo nuevo de esta edición [0:11:10] es que al final se liberan los puntajes de cada equipo en su dashboard.
- **Tiempos** [0:11:10]: 3 min de demo (cuentan desde que empiezas a hablar), 2 min de preguntas y 1 min 30 s para que los jueces evalúen y pase el siguiente equipo.
- **Premios** [0:07:19, 0:11:44, 3:53:45]: USD 3.000 en total. Cada ganador de track recibe USD 400. El ganador general recibe USD 1.200 en lugar de los 400 y viaja a la hackathon de Chile "en menos de un mes". El segundo lugar de track no tiene premio.
- **Premio del público** [0:11:44]: el video se publica durante la semana y el proyecto con más votos del público en un plazo dado gana USD 400. Se menciona "un proyecto que tuvo 613 puntos", sin aclarar de qué edición. Brecha: no se dice quién lo ganó en Caracas.
- **Mercado de predicción** [0:12:16]: estilo Polymarket. Cada hacker parte con 1.000 bananas para apostar quién gana. El mejor trader gana USD 100 y el top 30% una camiseta de Supabase. Los organizadores aclaran que no quieren "incentivar la ludopatía".
- **Deliberación** [3:33:59–3:52:35]: solo hay música. Brecha: no hay comentarios del jurado.

## Tracks

| Track | Descripción (según el host) | N° de proyectos |
|---|---|---|
| 🛡️ AI Security | Cómo avanzar en IA sin que se vuelva un peligro [0:07:52] | 6 |
| 🤝 Trust | Sistemas para interactuar con entidades sin confiar ciegamente [0:07:52] | 6 |
| 🚨 Emergencies | Prevenir o actuar rápido ante emergencias, por el contexto del último terremoto en Venezuela [0:07:52–0:08:25] | 4 |
| 🧊 Three-Dimensional | Explorar las nuevas capacidades de la IA para crear productos que exploten lo 3D [0:08:25] | 6 |

Total: 22 proyectos presentados.

## Proyectos

| Marca | Proyecto | Track | Qué hace | ¿Físico/hardware? | Preguntas del jurado |
|---|---|---|---|---|---|
| [0:17:34] | Constancia | Trust | Constancias de trabajo firmadas criptográficamente (estándar W3C, blockchain) que permiten probar la experiencia laboral sin exponer datos privados | no | ¿Por qué solo constancias de trabajo, si sirve para cualquier documento que emite un ente y debe verificarse? · ¿Por qué mañana LinkedIn no puede usar la misma tecnología y quitarles el moat? |
| [0:32:33] | Rastro | Trust | Plataforma de donaciones en USDT que custodia el dinero y lo libera por tramos a la ONG contra verificación de gastos | no | ¿Quién verifica que el gasto ocurrió, más allá de una factura que puede ser falsificada? · ¿Cómo funciona exactamente la donación (el "pote")? · ¿Por qué una fundación aceptaría recibir por partes y no de una vez? |
| [0:40:03] | SmartTraffic | Trust | Modelos de IA con cámaras inteligentes que detectan infracciones de tránsito por placa y emiten multas automáticas con evidencia; red de cámaras ante choques | sí (cámara real simulando un semáforo en el ascensor del edificio) | ¿Cómo detectan la matrícula: pesos de YOLO ya entrenados o fine tuning? · ¿Dónde lo entrenaron? · ¿Qué datos usaron para la prueba? |
| [0:53:44] | mus3o (Museo) | Three-Dimensional | Convierte apuntes/PDF o un prompt en un museo 3D navegable (salas por subtema, tótems, guía IA "Aris", modo examen, VR) | no | ¿Cómo generan las piezas 3D y su distribución en el espacio? · La célula que vimos, ¿la generó el prompt o la hicieron aparte? |
| [1:01:27] | Manito | Emergencies | Agente de voz que hace el censo de víctimas del sismo por llamada y arma perfiles para certificarlos y conectarlos con vacantes | no | ¿Cómo reconocen la voz, quién guía la conversación y cómo la alinean? · ¿Integraron algún proveedor de telefonía para el demo? · ¿Quién valida que de verdad tengo la profesión que digo? |
| [1:12:48] | Arkangel | AI Security | Agente local que vigila procesos, logs y cambios del computador, detecta agentes maliciosos y propone correcciones que el usuario aprueba; abrió mostrando un hackeo real de una base de datos en la wifi del evento | no | ¿Qué decisión concreta ayuda a tomar? · ¿Cómo lograron que Claude les sirviera para entrar a los computadores de otros? · ¿Qué tipos de ataque monitorean y detectan? |
| [1:19:08] | Mapz | Three-Dimensional | Navegación 3D "hasta la puerta" con alertas de reductores, huecos y semáforos; vista de conductor | parcial (prototipo de reflejo en el parabrisas; el video no corrió) | ¿Los datos los consiguieron ustedes grabando las calles? · ¿Qué problema resuelve y cuál es la ventaja sobre la navegación 2D de Google Maps o Waze? |
| [1:26:19] | Gotchu | AI Security | Seguridad para pymes: análisis externo (URL) e interno (repo de GitHub), vigilancia de amenazas y un agente en sandbox que repara y abre un PR con humano en el loop | no | ¿En qué se diferencia de la skill de review de Codex más un "please fix"? · ¿Cómo validan que la alerta es real: métricas, precisión, falsos positivos y negativos? · ¿Es data sintética con la que entrenaron? |
| [1:41:15] | VanGUARD | AI Security | Revisión de seguridad continua que conecta GitHub, Supabase y Cloudflare; asistente "Vigía", alertas y llamadas por WhatsApp, corta PRs riesgosos y expone un MCP | no | ¿Cuál es el diferenciador frente a la skill de review de Codex sobre un PR? · ¿Por qué una plataforma y no una GitHub Action que corra code review? |
| [1:49:23] | ZeroID | Trust | Identidad digital: registro con pasaporte (OCR), trust score de cada plataforma según estándares de datos y login por SDK con consentimiento dato por dato | no | ¿Cuál es la propuesta de valor para los negocios? ("a mi mamá eso no le importa") · ¿Qué safeguards tienen para que el usuario les confíe datos tan sensibles? |
| [1:57:37] | Céflow | Three-Dimensional | Planificación de implantes dentales con IA a partir de tomografía y escaneo intraoral, con modelo 3D y mapa de contacto | no | ¿Qué seguridad le da a un odontólogo que el modelo se basa en datos validados con millones de pacientes reales y no en "la nube intangible" de Claude? · ¿Qué tiene de distinto frente a los programas que ya existen? |
| [2:04:54] | Tridi | Three-Dimensional | Convierte videos comunes en datos de movimiento simulados con física real para entrenar robots (physical AI); vende los datasets y exporta ONNX | no (robot en simulación; el output va al hardware) | ¿Investigaron lo que ya existe para detectar movimiento? · ¿Figure AI o Tesla entrenan así, o están reinventando la rueda? · ¿Con cuántos videos entrenaron la red? |
| [2:15:30] | HAWK | AI Security | Raspberry Pi 4B en paralelo a la red, como "silicio separado", con un LLM local fine-tuneado que filtra los requests de agentes (Claude, Codex, OpenCode); app móvil para aprobar | sí (Raspberry Pi) | ¿Qué modelo corre en la Raspberry y cómo categoriza los requests? · ¿Es un LLM? · ¿Por qué un LLM y no un clasificador? · Claude ya evalúa permisos con un servicio aparte, ¿qué aporta esto? |
| [2:25:06] | Arvi | Three-Dimensional | Guía turístico en realidad aumentada con personajes históricos que conversan (Simón Bolívar) y detección de objetos | no (app móvil AR) | ¿Quién es el usuario? En turismo uno quiere vivirlo, no mirarlo por una pantalla · El contenido está algo mock, ¿puedo pedirle cualquier dato histórico? · ¿Respondería algo abierto, como la historia del metro de Caracas? |
| [2:31:52] | Quórum | Trust | Votación verificable: credencial de hacker, verificación facial en el dispositivo (solo hash), votos encadenados y JSON descargable para auditar; demo en vivo con el público | no | ¿Qué impide enviar caras fabricadas, incluso con IA? · ¿Qué diferencia tiene frente a otros sistemas de voto online o descentralizados? |
| [2:39:03] | Presente | Emergencies | Convierte un Android viejo en un reloj de mesa para adultos mayores solos: escucha palabras clave, escala llamadas (hijo, vecino, emergencias), saca foto con contexto IA si la persona cae ante la cámara, avisa por Telegram y lee récipes por OCR | sí (teléfono como dispositivo fijo con cámara y micrófono) | Si la persona está lejos del celular y no responde, ¿se transmite algo automáticamente a quien atiende? · Si no lo hubiesen hecho en un teléfono, ¿en qué y por qué? |
| [2:46:46] | Veridian | AI Security | Autenticación continua por comportamiento: un clasificador levanta alertas y un agente decide si bloquea la sesión; se integra al backend "con tres líneas de código" | no | ¿Midieron la tasa de falsos positivos? · ¿Cómo funciona el clasificador? · ¿Es un chequeo determinista de reglas o un modelo de aprendizaje? |
| [2:53:34] | sIsA | Trust | Credencial única que comparte solo el dato necesario (p. ej. mayoría de edad) vía hash y bot de WhatsApp; el primer cliente es el Estado ("cédula 7.0") | sí (dispositivo físico, inferido de la pregunta del jurado) | ¿Qué valor le da al bar, para que pague, si hoy valida la edad gratis con la cédula? · ¿Por qué un dispositivo físico y no el NFC del celular? · Quién define qué datos se comparten y quién es el cliente |
| [3:01:26] | Qubbot (Kubot) | Three-Dimensional | Agente para crear software por voz, con mapa isométrico 3D del proyecto que colorea los archivos con vulnerabilidades | no | ¿Qué moat tienen para que mañana Claude o ChatGPT no saquen esta visualización 3D? (Brecha: parte de la pregunta y la respuesta queda cortada entre [3:05:27] y [3:06:40]) |
| [3:11:55] | Aló Mamá | Emergencies | Alerta encubierta: con unos botones se dispara la llamada de un agente de voz que finge ser tu mamá, detecta la frase clave de peligro y avisa por WhatsApp con ubicación en vivo, transcripción y reporte; dicen que funciona sin señal | no | ¿Qué ventaja tiene la llamada frente a solo apretar un botón SOS? · ¿Qué diferencia hay entre que me llame y yo diga "Andrés" y apretar un botón de pánico? · ¿Se pueden configurar varias frases de peligro según el escenario? |
| [3:20:01] | AGENT ZERO | AI Security | Guardia entre los agentes de chat y los datos: "model armor" detecta mensajes sospechosos, abre una sesión de engaño para aprender del atacante y genera políticas nuevas (whitelist de funciones); demo abierta al público por QR | no | ¿En qué se diferencia de una skill de review? · ¿Qué está haciendo realmente el módulo del medio? |
| [3:27:54] | Meshy | Emergencies | SOS sin internet que salta por Bluetooth mesh de teléfono en teléfono hasta uno con conexión; avisa a los contactos vía Capso (?) y conecta un LLM de primeros auxilios (fork de Bitchat) | sí (demo con tres teléfonos reales por Bluetooth) | ¿Por qué forkear Bitchat y modificarlo en vez de conectar su servicio al Bitchat normal? · Si el teléfono cierra la app antes de enviar el SOS, ¿qué pasa con la alerta? |

## Ganadores

| Track | 1° lugar (USD 400) | 2° lugar (sin premio) | Marca |
|---|---|---|---|
| AI Security | Arkangel | Gotchu (score 35, mostrado por error) | [3:54:53]–[3:55:28] |
| Emergencies | Aló Mamá (transcrito "Aloha") | Presente (equipo 25) | [3:57:43]–[3:58:19] |
| Trust | SmartTraffic | Quórum | [3:59:30]–[4:00:04] |
| Three-Dimensional | mus3o / Museo (equipo 5) | Qubbot / Kubot | [4:01:37]–[4:02:44] |

- **Ganador general** [4:04:57]: **mus3o (Museo)**, score 80,7. Gana USD 1.200 y viaja a la hackathon de Chile.
- **Mercado de predicción** [3:53:12]: daba 34,5% a Museo, y acertó.
- **Ganador del mercado** [4:07:55]: un trader llamado "Gede Castellano" (?). Hubo bromas sobre "insider trading", porque apostó por sí mismo.
- Brecha: no se dan los puntajes de los demás proyectos ni el ganador del voto del público.

## Preguntas del jurado por tipo

Total clasificado: 55 preguntas. Cada pregunta se cuenta en una sola categoría.

### 1. Competencia y diferenciación ("¿qué tiene esto que no tenga X?"): 13

- [1:29:06] Gotchu: "cómo se diferencia esto versus, por ejemplo, la skill de review de Codex más un please fix". La misma pregunta se repitió con VanGUARD [1:43:30] y AGENT ZERO [3:23:26].
- [2:08:15] Tridi: ¿Figure AI o Tesla entrenan sus robots de forma parecida, "o están reinventando la rueda"?
- [3:04:54] Qubbot: "qué moat tienen ustedes para que el día de mañana Claude no haga esta herramienta".
- [3:15:48] Aló Mamá: ¿qué diferencia hay entre que me llame y diga "Andrés" y apretar un botón de pánico? Respuesta inicial: "No, ninguna, en verdad".

### 2. Técnica y arquitectura (cómo está hecho, qué modelo): 12

- [0:43:34] SmartTraffic: ¿la detección de matrícula usa pesos de YOLO ya entrenados, o le hicieron fine tuning?
- [2:18:54] HAWK: ¿qué modelo corre en la Raspberry Pi y cómo categoriza los requests? ¿Es un LLM?
- [2:51:18] Veridian: "¿es un chequeo determinista de regla o es un modelo de aprendizaje?"
- [0:57:46] mus3o: ¿cómo generan las imágenes 3D y quién decide dónde va cada figura en el espacio?

### 3. Validación, precisión y verdad del resultado: 6

- [1:29:40] Gotchu: ¿cómo validan que la alerta es real? Las métricas, la precisión, los falsos negativos y los falsos positivos, "toda esa parte que es importante".
- [2:49:41] Veridian: "si midieron tasa de falsos positivos, creo que esto se presta mucho a que hayan alertas cuando realmente no lo hay". Respuesta: cerca de 3%, medido por ellos mismos.
- [2:00:21] Céflow: en IA y medicina la validación se hace con millones de pacientes reales, nunca sintéticos. ¿Qué seguridad le da eso a un odontólogo?
- [0:35:31] Rastro: ¿quién verifica que el gasto ocurrió, más allá de una factura que puede ser falsificada? En la misma línea, Manito [1:05:26]: ¿quién valida que de verdad tengo esa profesión?

### 4. Decisiones de diseño ("¿por qué X y no Y?"): 6

- [2:19:27] HAWK: ¿por qué un LLM y no un clasificador?
- [1:45:43] VanGUARD: ¿por qué una plataforma y no una GitHub Action que corra code review?
- [2:43:04] Presente: "si no lo hubiesen hecho en un teléfono, ¿en qué lo hubiesen hecho y por qué?"
- [2:57:33] sIsA: ¿por qué un dispositivo físico y no el NFC del celular?

### 5. Negocio, cliente y quién paga o adopta: 6

Esto pasó aunque el host dijo que el modelo de negocio quedaba fuera de la evaluación [0:06:45].

- [1:52:50] ZeroID: ¿cuál es la propuesta de valor para los negocios? Somos ingenieros, "pero a mi mamá eso no le importa".
- [2:56:24] sIsA: ¿qué valor agregado le da al local para que quiera pagar?
- [0:37:14] Rastro: ¿por qué una fundación aceptaría recibir la donación por partes?
- [2:28:39] Arvi: ¿quién es el usuario de este producto?

### 6. Origen de los datos y entrenamiento: 4

- [0:44:09] SmartTraffic: ¿dónde lo entrenaron y qué datos usaron para la prueba?
- [1:21:55] Mapz: los datos, ¿los consiguieron ustedes grabando esas calles?
- [2:09:24] Tridi: ¿con cuántos videos entrenaron la red?

### 7. Qué es real y qué es mock en el demo: 3

- [1:05:26] Manito: para el demo, ¿no integraron ningún proveedor de telefonía? Respuesta: solo web.
- [2:29:10] Arvi: "el contenido que tiene está un poco mock… no es que puedo pedirle cualquier cantidad de información de historia".
- [2:30:15] Arvi: si le hago una pregunta abierta, como la historia del metro de Caracas, ¿la responde?

### 8. Casos borde y robustez: 3

- [2:42:32] Presente: si la persona está lejos del celular y no responde, ¿se transmite algo automáticamente? Respuesta: "Por ahora no".
- [3:32:22] Meshy: si el teléfono cierra la app antes de enviar el SOS, ¿qué pasa con esa alerta "en el limbo"?
- [3:16:56] Aló Mamá: ¿se pueden configurar varias frases de peligro según el escenario?

### 9. Seguridad y privacidad de los datos: 2

- [1:54:01] ZeroID: ¿qué safeguards tienen para el tratamiento de datos tan sensibles?
- [2:34:37] Quórum: ¿qué impide enviar caras fabricadas, incluso con IA?

### Categorías sin preguntas

Brecha: no hubo preguntas de regulación, de escalabilidad, de validación con usuarios reales (entrevistas o pilotos) ni sobre el equipo.

## Lo que el jurado elogió o criticó

**Elogios**
- [0:02:16] Ignacio, en la bienvenida: lo que él presentó en su hackathon hace 12 años "no le llega ni a los pies" a lo que pueden hacer hoy con estas herramientas.
- [0:01:10] Ignacio: que la mitad venga a su primera hackathon es "bastante impresionante".
- [0:35:31] Rastro: "Me parece super interesante esto, pero…"
- [2:28:39] Arvi: "superchévere la presentación".
- [2:43:04] Presente: le gustó la presentación.
- [3:04:54] Qubbot: "superchida su idea, sobre todo para… vibe coders" (?). Para el juez, el mayor valor agregado es ver en 3D cómo está organizado el proyecto.

**Críticas**
- [1:14:58] Arkangel: no entendió qué decisión concreta ayuda a tomar el producto, ni cómo lograron el bypass.
- [1:22:27] Mapz: "no me quedó tan claro qué problema resuelve".
- [1:29:40] Gotchu: hoy muchas herramientas de IA "simplemente se conectan a Skills de Claude" sin un modelo propio detrás, y Claude no explica cómo lo hace.
- [2:00:54] Céflow: duda sobre la validación médica ("la nube tan intangible de Claude").
- [2:02:03] Céflow: "si eres odontólogo debes saber que programas como estos ya existen, porque yo también los he visto".
- [2:20:35] HAWK: Claude ya evalúa permisos con un servicio aparte. Ellos respondieron con el argumento de zero trust y separar al que ejecuta del que audita.
- [2:28:39] Arvi: en turismo "uno quiere estar presente y vivirlo", no verlo por una pantalla.
- [2:29:10] Arvi: el contenido está "un poco mock".
- [3:23:26] AGENT ZERO: "no alcanzamos a ver la demo específicamente".
- [2:30:49] El host corta a Arvi para "ser justa con todos los grupos": el tiempo se aplica estricto.

**En la premiación**
- [4:03:19] Solo frases sueltas: "Cansancio lo valió. El kinder (?) fue la clave. Fue la calidad".
- Brecha: el jurado no explicó por qué ganó cada proyecto.

## Relevante para nuestro proyecto

- **SmartTraffic** (ganó Trust) usó cámara real e IA de visión (YOLO + OCR de placas) en un demo físico en vivo. Le preguntaron si los pesos eran preentrenados o con fine tuning, dónde entrenaron y con qué datos probaron.
- **HAWK** (Raspberry Pi como hardware separado con LLM local) no quedó en el podio. Le preguntaron qué modelo exacto corre, por qué un LLM y no un clasificador, y qué aporta si Claude ya evalúa permisos.
- **Presente** (2° en Emergencies) usa un Android fijo con cámara y micrófono: escucha palabras clave y saca foto con contexto IA ante una caída. Le preguntaron qué pasa si la persona está lejos o no responde, y en qué hardware lo harían si no fuera un teléfono (respondieron Raspberry o ESP32).
- **Meshy** (Bluetooth mesh entre teléfonos) recibió la pregunta del caso borde: la app se cierra antes de enviar la alerta.
- **Aló Mamá** (ganó Emergencies) es un agente de voz que alerta a contactos. Le preguntaron qué ventaja tiene frente a un simple botón SOS.
- **Tridi** (physical AI y robots) tuvo que contestar si reinventaba lo que ya hacen Tesla o Figure y con cuántos videos entrenó.
- **Céflow** se validó contra un caso real ya operado (error de 0,02 mm, o 0,2 mm según el tramo). Igual le cuestionaron la validación con pacientes reales y la diferencia con el software existente.
- **Veridian** recibió la pregunta que más nos toca: la tasa de falsos positivos de las alertas. Respondieron 3%, medido por ellos mismos, y lo reconocieron como una debilidad.
