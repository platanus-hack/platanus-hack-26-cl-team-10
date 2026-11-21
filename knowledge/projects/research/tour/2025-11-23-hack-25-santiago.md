# Platanus Hack 25 · Santiago (nov-2025)

> Fuente: [transcripción](../fuentes/videos-platanus/2025-11-23-hack-25-santiago.md) · [video](https://www.youtube.com/watch?v=1BkgjK1RQm0). Extraído por un agente de la transcripción automática; las citas son paráfrasis cercanas salvo que vayan entre comillas.

## Formato

- **Evento**: según la descripción del video, 200 hackers, «de cero a producto en 36 horas», del viernes 21 al domingo 23 de noviembre de 2025, en las oficinas de Buk. El video reúne «más de 40 presentaciones»; los capítulos suman 45. Un presentador habla de «150 hackers, mentores y jurados» en la sala [0:37:38].
- **Dinámica**: cada equipo hace un pitch con demo en vivo y después responde preguntas. El host corta con «Tiempo» o «Estamos en el tiempo» (p. ej. [0:07:27], [0:29:34], [0:34:10], [0:55:30], [1:19:12]), abre con «Vamos con las preguntas» ([0:30:08], [0:43:55], [0:50:13]) o «Ahora pasamos a las preguntas de los jueces» [3:10:03] y cierra con «un fuerte aplauso al equipo número N» (equipos 16 [3:14:29], 17 [3:26:45], 19 [3:33:33], 29 [3:38:32], 30 [3:45:47], 36 [3:52:50], 4 [3:58:59] y 42 [4:03:16]; también se mencionan el Team 40 [2:19:54], el grupo 37 [2:35:45] y el equipo 41 [2:41:14]).
- **Minutos de pitch y de preguntas**: Brecha, porque nadie los dice. Por las marcas de tiempo, el pitch dura unos 3 minutos y las preguntas entre 1 y 3. Entran de 1 a 5 preguntas por equipo y cada bloque ocupa entre 4 y 7 minutos.
- **Equipos de una persona**: el host aplaude «el solo número 10» (Chekia) [3:20:31]. PaanEat [1:57:34], Eska [2:46:12] y vitrina [2:11:23] también hablan en primera persona singular («desarrollé», «implementé»).
- **Trabajo previo**: Adsombroso reconoce que «la otra parte ya la teníamos hecha» (el módulo de ventas de sus startups) y que en la hackatón hicieron solo la generación de contenido [1:31:17]. Nadie del jurado lo objeta.
- **Jurado**: no se presenta. Lo único que da la transcripción es un jurado que se identifica como «Pedro» (?) [1:59:50] y otro que dice «yo también soy ingeniero, pero no tan especialista como ellos en IA» [1:29:05]. Nombres, cargos y procedencia: Brecha.
- **Criterios de evaluación**: Brecha.
- **Premios**: Brecha. El único indicio es la apertura del pitch de GoBoard: «Imagina que ganaste la jaón, te ganaste $,000 en Bitcoin y queréis ir a canjearlo… vay a registrarte a Buda» [3:59:23]. Es un supuesto del presentador, no un anuncio oficial.
- **Sponsors**: Buk es el anfitrión («ft. Buk»; un presentador habla de «Platonus Book» [0:52:47]). Circles menciona startups «del portafolio» que reclutan desarrolladores [3:56:10]. No hay más sponsors explícitos (Brecha). Los equipos nombran como herramientas Anthropic/Claude, Twilio, Convex, Vercel, Fintoc, Stripe, Azure y Gemini, pero eso no los hace sponsors.
- **Reglas**: más allá de las 36 horas y «de cero a producto», Brecha.

## Tracks

| Track | Descripción si se dice | N° de proyectos |
|---|---|---|
| ☎️ Legacy | La define un presentador, no la organización: «procesos o sistemas antiguos que al día de hoy se siguen ocupando y que a veces no siempre son los mejores» (Memo [0:16:58]) | 16 |
| ✨ Consumer AI | No se define | 12 |
| 🦾 Human Enhancement | No se define formalmente. Imagination Lab dice que eligió el track y por eso metió computer vision: «cómo podemos entrar a Real World» [0:51:21] | 10 |
| 🛡️ Fintech + Digital Security | No se define | 7 |

Ese año no hubo track Physical AI.

## Proyectos

Criterio de «¿físico/hardware?»: sí cuando el producto capta el mundo físico con cámara o sensor en vivo o actúa sobre él. Telefonía y bots de chat cuentan como no.

| Marca | Proyecto | Track | Qué hace | ¿Físico/hardware? | Preguntas del jurado |
|---|---|---|---|---|---|
| [0:00:00] | MedSim | Legacy | Simula pacientes con IA para que estudiantes de medicina practiquen anamnesis y diagnóstico, y les pone nota. | no | De dónde sacan la información (RAG, normas del Minsal) · ¿Las radiografías se generan o salen de bancos de imágenes? |
| [0:04:39] | Cognitive Context | Human Enhancement | Memoria personal multimodal (texto y audio) en un grafo con RAG, pensada como «MCP de cerebros». | no | ¿Qué es cada punto del grafo? · ¿Las memorias antiguas pesan menos que las nuevas? |
| [0:11:02] | MIDIA | Human Enhancement | Copiloto para músicos: tokeniza MIDI, un LLM sugiere notas y acordes y lo devuelve como MIDI. | no | ¿Cómo evitan que un LLM, que «promedia», dé música plana? · ¿Qué ve primero el LLM y qué tokenización usan? |
| [0:16:58] | Memo | Legacy | Gestiona la medicación de adultos mayores con recordatorios por WhatsApp y llamadas de voz (Twilio), con panel para la familia. | no | ¿Cuánto del daño por medicación se debe a olvidar la pastilla? · ¿Para quién es la plataforma, hijos o abuelo? · ¿Avisa a la familia si el abuelo no contesta? |
| [0:23:07] | despens.ai | Consumer AI | Bot de Telegram que lleva el stock de la despensa leyendo boletas y arma la lista o el carrito del súper. | no | ¿Cómo saben lo que queda en la despensa? |
| [0:26:44] | 0ratorIA | Human Enhancement | Corrige audios y entrena la expresión oral con métricas de fluidez, claridad y vocabulario. | no | ¿Consideran que la velocidad y el vocabulario cambian por país (Chile, Argentina, Colombia)? |
| [0:30:51] | BodyCart | Consumer AI | Extensión de Chrome con agentes que puntúan de 0 a 100 si una tienda o vendedor es estafa. | no | ¿Por qué todos los chequeos son con IA si existen bases de datos y sistemas para eso? |
| [0:35:57] | Record.AI | Human Enhancement | Reconocimiento facial con la cámara del teléfono o lentes (Meta glasses) que muestra datos de la persona por voz; versión para Alzheimer. | sí (cámara, lentes) | ¿De dónde saco las bases de datos para usarlo en mi vida diaria? |
| [0:40:35] | Themis | Legacy | Detecta licitaciones públicas irregulares con embeddings, filtros y agentes que revisan la Ley de Compras. | no | ¿Cómo definieron los criterios de irregularidad sin generar muchos falsos positivos? · ¿Por qué no detectar outliers automáticamente? · ¿Cuál fue la motivación? Es políticamente «picante» |
| [0:46:17] | Imagination Lab | Human Enhancement | Niños de 6 a 12 años crean mundos con voz y gestos usando computer vision. | sí (cámara, gestos) | ¿Qué guardrails tienen para contenido infantil? · ¿Qué lo distingue de Minecraft, Lego Mindstorms o Roblox? |
| [0:52:14] | Legal Ward | Legacy | Cruza los documentos de una empresa con proyectos de ley y estima el impacto y su avance. | no | ¿Cómo manejan documentos legales muy largos con un RAG que responda a tiempo? · ¿Cómo distingo los proyectos que de verdad avanzan de los que quedan botados? |
| [0:59:26] | SafeLine | Consumer AI | Se mete en la llamada telefónica con un troncal y conferencia, detecta la estafa en vivo y la corta. | no (telefonía) | ¿Funciona con WhatsApp o con teléfono, y cómo interviene? · ¿Funciona en iPhone? · ¿Al atacante le suena un pitido? · ¿Podría contestar primero un asistente? · ¿Cómo resuelven la clonación de voz? · Con la latencia de detección, ¿qué pasa si ya entregué mis datos? |
| [1:05:23] | Tiqn | Legacy | Un agente escucha la llamada de emergencia, llena el formulario y actualiza en vivo la app del rescatista. | no (telefonía) | ¿Cómo intervienen la llamada? · ¿Qué modelo de transcripción usan? · ¿Funciona con español chileno? · ¿Por qué transcriben solo al que llama? |
| [1:10:39] | SuperTracker | Consumer AI | Compra agéntica: arma y compara carritos en varios supermercados para un objetivo y un presupuesto. | no | ¿Los carritos son comparables en calidad entre supermercados? · Señalan precios mal calculados, presupuesto excedido y carne de carbonada en un asado |
| [1:15:51] | scrapi.fast | Consumer AI | Un agente convierte cualquier sitio web en una API determinista que se repara sola. | no | A los dueños de sitios no les gustan los scrapers, ¿cómo lo abordan? · ¿Y cuando te bloquean? |
| [1:21:00] | Hedgie | Fintech + Digital Security | Replica sin comisión los portafolios de hedge funds y políticos (13F, STOCK Act). | no | ¿Solo portafolios de EE.UU.? · ¿Qué lo diferencia de Autopilot? · Con el retraso de la información, ¿cuánto rinde la estrategia? · ¿Con qué plataforma ejecutan las operaciones? |
| [1:26:16] | Adsombroso | Legacy | Investiga la empresa, genera guion, imágenes y video, y publica campañas en Meta. | no | ¿Qué usan para imágenes y video y qué guardrails tienen contra alucinaciones? · ¿Dónde entran las reglas de Meta? · ¿Retroalimentan con el desempeño de los posts? · ¿Qué hacen con la fatiga ante contenido hecho con IA? |
| [1:32:40] | faro | Human Enhancement | Asistente para personas ciegas: la cámara del teléfono detecta obstáculos y semáforos (YOLOv8) y guía con audio y vibraciones. | sí (cámara, vibración) | ¿Funciona ahora en el teléfono? · ¿Dónde corre y con qué infraestructura? · ¿Qué modelos de reconocimiento de imagen usan y cómo funcionan? |
| [1:36:51] | Shadow | Fintech + Digital Security | Tarjetas virtuales por comercio, creadas desde el checkout y respaldadas por la tarjeta personal. | no | ¿Por qué esto tiene sentido «en casi diciembre del 2025»? · ¿Está en producción? ¿Las tarjetas son reales? (Respuesta: Stripe sandbox) |
| [1:42:11] | bananandamos | Legacy | Crea y juega aventuras de texto o imagen tipo «elige tu propia aventura» generadas con Gemini. | no | ¿La historia se genera mientras juego o está pregenerada? · ¿Tu hija lo probó? · ¿Su feedback cambió algo? · ¿Qué falta para lanzarlo? |
| [1:46:59] | MiCandidatop | Legacy | Match estilo Tinder con candidatos presidenciales a partir de opiniones anónimas (embeddings). | no | Detalles del ETL: fuentes, procesamiento y si corre seguido o fue una sola vez · ¿Cómo funciona el algoritmo de match? |
| [1:52:06] | BrainFlow | Human Enhancement | «Segundo cerebro» con un agente que genera notas, rutas de aprendizaje y planes en el calendario. | no | No queda claro cómo resuelve la sobresaturación: «yo veo eso y como que me siento saturado» |
| [1:57:34] | PaanEat | Consumer AI | Agente de WhatsApp que planifica el menú semanal y hace el pedido real en un e-commerce (Fresh (?)). | no | ¿Cómo mantienen el contexto en conversaciones largas? · ¿Dónde se hace el pedido? · ¿Cómo hacen match entre ingredientes y productos? · ¿Considera lo que ya tengo en casa? |
| [2:01:51] | Recuerdo | Human Enhancement | Notas de voz sobre personas y eventos, agrupadas por temas para recordar a los amigos. | no | ¿Está desplegado en producción? · ¿Sobre qué infraestructura (AWS, base de datos)? |
| [2:05:35] | CUENTI | Legacy | Convierte un PDF de cuento infantil en un videojuego 2D jugable (Phaser (?)). | no | ¿Cómo se genera el juego, cómo se crean las imágenes y dónde se guardan? |
| [2:10:18] | vitrina | Consumer AI | Arma una tienda con pago (Mercado Pago) a partir del Instagram de vendedores de ropa de segunda mano. | no | ¿Cómo se actualizan fotos y precios cuando cambian? (audio confuso) · ¿Qué hay del lado del vendedor? |
| [2:14:35] | Felipe | Human Enhancement | Copiloto de decisiones que combina un LLM con mercados de Polymarket para «ver futuros». | no | ¿En qué se basan las nuevas predicciones? · ¿Ese porcentaje sale de Polymarket? (Respuesta: no, es «alucinación de Felipe») · ¿Qué busca si pregunto por casarme? · ¿Se le puede dar contexto personal? |
| [2:19:53] | Oregon Health | Legacy | Centraliza documentos médicos, los explica en lenguaje simple y sugiere chequeos según la historia familiar. | no | Privacidad: ¿qué información de mis familiares puedo usar? · ¿Cómo se generan las recomendaciones y dónde corren los modelos? |
| [2:25:13] | ThinkTwice with Pausito | Fintech + Digital Security | Extensión de Chrome que detecta un checkout y frena la compra impulsiva con un comentario persuasivo. | no | ¿Cómo se integra con AliExpress y Mercado Libre y con qué umbral aparece? · ¿Guarda datos, en local o en la nube? |
| [2:30:47] | PostulaMe | Legacy | Arma el perfil, busca vacantes (scraping) y adapta el CV a cada postulación. | no | ¿Cómo se envía la postulación y a quién le llega? |
| [2:35:45] | wakai | Legacy | Agentes de chat y voz que confirman la asistencia a mediaciones familiares y priorizan casos con un score. | no (telefonía) | ¿Cuál es exactamente el problema que atacan? · ¿Dónde está el «factor humano» que mencionan? |
| [2:41:13] | BusCachorros | Legacy | Encuentra mascotas perdidas con match por foto, mapa de avistamientos y bot de Telegram. | no | ¿Por qué Telegram? · ¿Cómo me entero de que el bot existe? |
| [2:45:38] | Eska | Fintech + Digital Security | Microcréditos P2P con subasta y bolsas de préstamos para gente con scoring medio. | no | ¿Quién presta y quién pide? · ¿Cómo manejan el riesgo y la honestidad de las partes? · ¿Cómo sabes si soy buen pagador y con qué base de datos? · ¿Validan los documentos? |
| [2:49:22] | Vocanize | Consumer AI | Onboarding con IA y modelos psicológicos que propone caminos de carrera y universidad a escolares. | no | ¿Cómo se adapta a cada persona y con qué datos, aparte del formulario? · Si un camino no me gusta, ¿cómo doy feedback? |
| [2:56:12] | SkillLab | Consumer AI | Coach deportivo: Gemini analiza segundo a segundo un video de entrenamiento y agentes por disciplina dan feedback. | no (video subido) | ¿El análisis se hizo en vivo o ya estaba listo? · En una pelea, ¿a cuál de los dos peleadores analiza? |
| [3:01:07] | Hop | Fintech + Digital Security | Blindaje de llamadas: detecta riesgo con NLP, alerta a contactos y filtra datos sensibles en vivo. | no (llamada simulada en web) | ¿El monitoreo es a nivel de aplicación? ¿Hasta dónde llegaron? (Respuesta: simularon la llamada en una web) · ¿Implementaron las alertas y a quién le llegan? |
| [3:06:05] | django-security-suite | Fintech + Digital Security | Librería open source para Django con bloqueo de amenazas, campos cifrados buscables y logs de cumplimiento. | no | ¿Con qué reglas identifican una amenaza? · ¿Cómo se busca sobre datos cifrados? · ¿Qué ventaja tiene sobre Cloudflare? · ¿Filtra en el servidor web o antes? · ¿Qué les faltó hacer? |
| [3:14:42] | Chekia | Consumer AI | Pega el link de un video de redes y varios agentes verifican si es verdadero. | no | ¿Solo TikTok? ¿Y los videos privados? · ¿Y si meto un prompt en la descripción para que diga que es cierto? · ¿Sirve para videos legales? · ¿Cómo sería la experiencia para una abuela de 76 años? |
| [3:21:06] | CoBrot | Fintech + Digital Security | Bot de WhatsApp que lee boletas (OCR), reparte ítems entre amigos y registra los pagos. | no | ¿Cómo identifica la sesión del grupo? · ¿Cómo controlan que no alucine precios al leer la boleta? · ¿Cómo monetizarían? · ¿Qué pasa si pago una deuda en varias cuotas? |
| [3:27:18] | GreenLight | Legacy | Agentes que ayudan a un product manager a definir y validar el problema real (consultas por Slack, deep research). | no | ¿Dónde vive el contexto de la empresa? · ¿La app espera a que la persona responda en Slack? |
| [3:33:55] | Lucas | Consumer AI | Asistente de finanzas personales conectado a los bancos (Fintoc) con herramientas de análisis. | no | ¿Cómo hicieron la parte de IA, con agentes y qué herramientas? · ¿Solo muestra datos o también sugiere cambios? · ¿Cómo llega la información de Fintoc y qué le agregaron? |
| [3:39:00] | DeepBonds | Human Enhancement | Analiza tus chats de WhatsApp y simula a un ser querido para ensayar mensajes difíciles. | no | ¿Cómo definieron qué es un buen vínculo? ¿Hay base académica? · ¿La respuesta usa el contexto de conversaciones anteriores? · ¿Cuál fue el desafío técnico más difícil? |
| [3:46:17] | Pasa el dato | Legacy | Mapa de datos y recomendaciones locales entre vecinos y comunidades. | no | ¿Cuál fue el desafío técnico? · ¿Cómo atraerían a mucha gente? · ¿Cómo sé si un dato es reciente y confiable? |
| [3:53:19] | Circles | Consumer AI | Red social donde los asistentes personales negocian entre sí para hacer match y juntar a la gente en persona. | no | ¿Cómo escala el match sin volverse exponencial? · ¿Qué quedó en el backlog, como fotos y contenido humano? |
| [3:59:22] | GoBoard | Legacy | Onboarding reutilizable (OpenID Connect y passkey) que rellena los datos del usuario en las apps integradas. | no | ¿Por qué la app debe integrarse con ustedes y no rellenar todo en local? |

## Ganadores

Brecha. La transcripción termina con el pitch de GoBoard [4:03:16] («Un gran aplauso para el equipo número 42… Señor») y no incluye premiación ni anuncio de ganadores, ni por track ni general. Tampoco se ven finalistas.

## Preguntas del jurado por tipo

Total contado: 113 preguntas en 45 proyectos. Cada pregunta va en una sola categoría.

1. **Técnica, arquitectura, stack y modelos: 41.** Es por lejos la más común. Casi todos los equipos reciben al menos una pregunta de «cómo funciona por dentro».
   - faro [1:35:32]: «¿me puedes dar un poco más de detalle sobre los modelos que usaron para reconocimiento de imágenes y cómo más o menos cómo funciona eso?»
   - Recuerdo [2:04:50]: «¿Sobre qué infraestructura está funcionando en producción? … ¿Están usando AWS? ¿Qué servicios?»
   - MIDIA [0:15:36]: «Quiero entender qué es lo que ve primero el el Ll[M]».
   - SafeLine [1:04:19]: con la latencia de detección, ¿qué pasa si ya le di mis datos a la persona?
2. **Producto, usuario objetivo y alcance: 18.**
   - Memo [0:22:00]: «la plataforma que vimos, ¿esa para quién está pensada?»
   - Chekia [3:19:56]: «¿Cómo adaptaríais el user experience para alguien como mi abuela que tiene 76 años?»
   - Lucas [3:37:25]: ¿solo muestra cosas o también sugiere cambios de rutina?
3. **Qué es real y qué es mock (producción, demo en vivo, integraciones): 16.**
   - Shadow [1:40:43]: «¿esto está en producción? ¿Esas tarjetas son reales?»
   - SkillLab [2:59:30]: «no entendí si en verdad se hizo el análisis ahí o lo está mostrando».
   - Hop [3:04:31]: «este monitoreo no me quedó claro si era a nivel de aplicación, o sea, como cómo lograron tener este acceso o hasta dónde llegaron».
   - Felipe [2:18:36]: ¿ese porcentaje lo dijo Polymarket? Respuesta: «Este es alucinación de Felipe».
4. **Fiabilidad del resultado (falsos positivos, alucinación, sesgo, validez del criterio): 7.**
   - Themis [0:43:55]: lo difícil es tener una muestra de casos fraudulentos; «es difícil no … dar simplemente muchos falsos positivos».
   - CoBrot [3:25:02]: «¿Cómo controlan que no alucine en base a la imágenes o cosas que lee?»
   - Tiqn [1:09:22]: «mi duda principal es español chileno».
   - DeepBonds [3:43:33]: «¿Cómo saben que un vínculo es bueno?»
5. **Negocio, quién paga, riesgo y adopción: 7.**
   - CoBrot [3:26:11]: «La segunda, que es la que siempre hago, ¿cómo monetizarían esto?» Es la única pregunta explícita de monetización, pero el jurado dice que la hace siempre.
   - Pasa el dato [3:51:13]: «¿Cómo harían para que entren muchas personas a pasar el dato?»
   - Eska [2:48:01]: «¿Cómo tú te das cuenta de que yo soy un buen o mal pagador? ¿Qué base de datos ocupas?»
6. **Datos, privacidad y seguridad: 6.**
   - Oregon Health [2:22:37]: «Tengo una pregunta sobre privacidad que es super importante en temas de salud».
   - ThinkTwice [2:29:46]: ¿guarda la data en algún lado? ¿vive en local o en la nube?
   - Chekia [3:18:13]: ¿qué pasa si en la descripción del video pongo un prompt para que los agentes digan que es cierto?
   - SafeLine [1:03:46]: «¿Cómo resuelven el problema de clonación de voz?»
7. **Competencia, diferenciación y timing: 4.**
   - Imagination Lab [0:50:45]: «qué tiene de distinto esto que haría que los niños pasen de ser un 2% a un, no sé, un 10».
   - Hedgie [1:23:45]: ¿qué diferencia tiene con Autopilot?
   - django-security-suite [3:11:12]: «qué ventaja tendría hacerlo con esa librería versus usar Cloudfare o algo así».
   - Shadow [1:39:38]: «¿por qué crear esto hizo sentido en casi diciembre del 2025?»
8. **Problema real y su tamaño: 3.**
   - wakai [2:39:01]: «no me quedó muy claro … cuál era el problema que buscaban atacar».
   - Memo [0:20:19]: ¿cuál es el impacto de esos daños y cuántos son realmente por olvidar la pastilla?
   - BrainFlow [1:55:29]: cómo resuelve estar sobresaturado si al verlo uno se siente saturado.
9. **Uso de IA o por qué un LLM: 3.**
   - BodyCart [0:34:45]: «¿Por qué todos tus chequeos son con I[A]?» si existen sistemas y bases de datos.
   - MIDIA [0:14:30]: los LLM promedian y dan contenido plano; ¿cómo lo contrarrestan si buscan creatividad?
   - Adsombroso [1:31:17]: ya hay fatiga ante el contenido visual generado.
10. **Equipo, motivación y roadmap: 3.**
    - Themis [0:45:33]: «¿Y cuál fue su motivación?»
    - django-security-suite [3:12:51]: «¿Qué les faltó hacer…?»
    - Circles [3:57:53]: «¿Qué les quedó en el backlock?»
11. **Legal y ética: 2.**
    - scrapi.fast [1:19:50]: «la mayoría de los dueños de sitio web no les gustan los scrapers».
    - scrapi.fast [1:20:22]: el sitio probablemente no quiere que lo usen de API y tiende a bloquearte. Respuesta: rotan IPs, «es poco ético, pero bueno, es una demo».
12. **Validación con usuarios: 2.**
    - bananandamos [1:45:40]: «¿y tu hija ya probó el juego?» y [1:46:13]: «¿Su feedback te sirvió en generar algún cambio?»
13. **Escalabilidad: 1.**
    - Circles [3:57:19]: «¿cómo hacen para que eso escale y no sea como exponencial?»

No hubo preguntas explícitas de regulación. Lo más cercano: con qué plataforma ejecuta Hedgie las operaciones [1:24:51] y Shadow explicando que no puede salir a producción por temas legales [1:41:17].

## Lo que el jurado elogió o criticó

**Elogios**
- [1:46:47] bananandamos: «Buenísimo» al saber que ya está vivo en su sitio.
- [2:08:23] CUENTI: «Buenísimo» antes de preguntar por lo técnico.
- [2:22:37] Oregon Health: «Buenísimo» antes de la pregunta de privacidad.
- [3:19:56] Chekia: «veo mucho a mi abuela ocupando esto». El host cierra con «Un fuerte aplauso para el solo número 10, su trabajo» [3:20:31].
- [3:42:57] DeepBonds: «Yo la ocuparía harto. [risas]»
- [2:53:41] Vocanize: el host calma al presentador con «No te preocupes. [risas]».

**Críticas**
- [0:34:45] BodyCart: cuestionan que todo dependa de la IA habiendo datos objetivos disponibles.
- [1:15:06] SuperTracker: el jurado nota en la demo precios inconsistentes (108 contra 165), presupuesto excedido y «carne de carbonada, que no sé qué vamos a hacer con eso en el asado».
- [1:19:50] scrapi.fast: no dijeron nada sobre la oposición de los dueños de sitios a ser scrapeados («no mencionaron nada al respecto»).
- [1:29:38] Adsombroso: «del demo no alcancé a entender mucho dónde entran en el juego las reglas de meta».
- [1:39:38] Shadow: escepticismo sobre el timing de la idea.
- [1:44:33] bananandamos: «No me quedó tan claro» cómo se interactúa con el juego.
- [1:55:29] BrainFlow: el grafo parece aumentar la saturación en vez de bajarla.
- [2:19:10] Felipe: «Curioso el criterio, pero okay», sobre consultar la tasa de la Fed para decidir si casarse. Antes había quedado expuesto que parte de las cifras eran alucinadas [2:18:36].
- [2:39:01] wakai: el problema no quedó claro; [2:40:09] tampoco dónde está la parte humana.
- [2:48:01] Eska: «A mí no me queda claro» cómo se evalúa al deudor.
- [3:04:31] Hop: al preguntar, sale a la luz que la llamada era simulada en una web.
- [3:51:13] Pasa el dato: «los repuestos se compran en repartes, así que está mal puesto ahí» (un dato de la demo estaba mal).
- [1:08:14] Tiqn: lo comparan con SafeLine, presentado antes: «Igual que los otros muchachos o tienen una mejor tecnología».

Fuera del jurado, varios presentadores admitieron límites al ser preguntados: scrapi.fast reconoció que rotar IPs «es poco ético» [1:20:22], Shadow corre en sandbox [1:41:17], Hop simuló la llamada [3:04:31] y Felipe alucina parte de las probabilidades [2:18:36].

## Relevante para nuestro proyecto

- **faro** [1:32:40]: es lo más cercano a lo nuestro, cámara del teléfono más YOLOv8, Claude 3.5 y ElevenLabs, con aviso por audio y vibración. Le preguntaron si funcionaba en ese momento en el teléfono, dónde corre (infraestructura) y qué modelos de visión usan y cómo.
- **Imagination Lab** [0:46:17]: usa computer vision de gestos «para entrar a Real World». Le preguntaron por guardrails y por la diferencia con Minecraft, Lego o Roblox. Reconoció que por ahora solo funciona la voz.
- **Record.AI** [0:35:57]: cámara o Meta glasses con face embeddings y asistente de voz para «seguir mirando a los ojos» a la persona. Le preguntaron de dónde salen los datos en la vida real.
- **SkillLab** [2:56:12]: análisis de video segundo a segundo con agentes por disciplina. Le preguntaron si el análisis corrió en vivo o estaba pregenerado, y a quién evalúa cuando hay dos personas en cuadro.
- **Tiqn** [1:05:23] y **SafeLine** [0:59:26]: audio en tiempo real. Les preguntaron qué modelo usan, si funciona con español chileno, por qué transcriben solo una voz (latencia) y qué pasa si el aviso llega tarde.
- **Hop** [3:01:07]: lo expusieron por simular la integración real («¿hasta dónde llegaron?»).
- **GreenLight** [3:27:18]: el único con contexto industrial (ejemplo de lámparas para salmones de COPEC). Le preguntaron dónde vive el contexto de la empresa.
- **django-security-suite** [3:11:45]: defendió no depender de un vendor porque «lo puedes levantar en una Rosberry» frente a Cloudflare.
- No hubo proyectos de minería, mantenimiento ni seguridad laboral, y ninguno usó sensores aparte de la cámara (Brecha).
