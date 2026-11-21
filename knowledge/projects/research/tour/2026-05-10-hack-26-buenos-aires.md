# Platanus Hack 26 · Buenos Aires (may-2026)

> Fuente: [transcripción](../fuentes/videos-platanus/2026-05-10-hack-26-buenos-aires.md) · [video](https://www.youtube.com/watch?v=JP7laiGtB8o). Extraído por un agente de la transcripción automática; las citas son paráfrasis cercanas salvo que vayan entre comillas.

## Formato

- **Contexto** [0:16:26]: es la primera parada del Platanus Hack Latam Tour. Las otras sedes anunciadas son Bogotá, Santiago de Chile, Ciudad de México y Caracas.
- **Host** [0:16:58]: General Partner y CTO de Platanus. Su nombre no se dice (Brecha). Los ganadores los anuncia Rafa, el organizador [4:30:21].
- **Convocatoria** [0:17:33]: unas 400 postulaciones, 110 hackers seleccionados, de varias nacionalidades.
- **Sponsors** [0:18:04]: Anthropic ("Antropic"), Profound y Capso (?). Pusieron créditos y apoyo ElevenLabs, Supabase, Vercel y Cairos (?); este último ayudó con el track AI Security y con mentores [0:18:39]. Paisanos (?) agrandó el premio a último minuto [0:20:20]. Se agradece también a "la gente de WordPlace (?)" [4:30:21].
- **Lema y foco** [0:18:39–0:19:11]: «de cero a producto en 36 horas». El host dijo que la demo y el producto importan más que el modelo de negocio o los unit economics. También hubo un desafío arcade previo para premiar la curiosidad.
- **Reglas** [0:19:11]: 36 horas non-stop, con alojamiento en el lugar. La app tiene que estar desplegada y ser open source, y el código ya fue entregado. Hubo mentores.
- **Premios** [0:19:11]: «3500 en premio» y, más adelante, «$500 en premios más créditos» [0:22:34]. Las dos cifras no cuadran; puede ser un error de transcripción de $3.500. Al ganador general se le menciona un monto de «700» (?) [4:41:30] y un pasaje a Chile para competir en la hackatón de fin de año [4:44:42].
- **Mentores** [0:19:45–0:20:20]: Camila, Aitán (?), Ema, Franco Fantini, Franco Pinto, Luca de Leo, Marcos Díaz, Angi, Martín y Anuel (?).
- **Jurado** [0:20:20–0:20:54]:
  - José Rico, founder de Olaclick.
  - Nicolás Andreano (?), founder de Tapi.
  - Fefo Iras (?), de «Product and Moon» (?).
  - Ariel Díaz, founder de Rebil (?).

  Según el host, varios pasaron por Y Combinator o fundaron startups YC.
- **Criterios** [0:21:26]: originalidad, ambición, ejecución, aspecto técnico e impacto. Cada juez pone una nota a cada criterio (la escala sale ininteligible: «nota del cerco») y la multiplica por el porcentaje del criterio para sacar su nota final. Después se normaliza por juez y se promedia. **Brecha:** no se dicen los pesos de cada criterio.
- **Tiempos** [0:22:01]: 3 min de demo, centrada en mostrar más que en explicar; 2 min de preguntas del jurado; 1 min 30 s para que el jurado evalúe y para el cambio de equipo.
- **Difusión** [0:22:34]: las demos se graban y se transmiten en vivo, y se publican durante la semana. Al final hay una votación popular sobre los videos [0:26:00].
- **Platanus Hack Market** [0:22:34–0:24:49]: mercado de predicción para los hackers. Cada uno parte con 1000 «bananas» y compra y vende «acciones» de los proyectos. Antes de anunciar al ganador el mercado «colapsa»: las acciones del ganador se convierten en dinero y las demás quedan en cero. Hay premio para el mejor rendimiento y un premio especial para el 30% superior. El host aclaró que no incentivan las apuestas.
- **Premiación** [4:35:48]: se muestra el score normalizado por jueces de cada equipo. El ganador general sale de entre los primeros lugares de cada track [4:40:52].

## Tracks

| Track | Descripción si se dice | N° de proyectos |
|---|---|---|
| 🗼 Vertical AI | Brecha. El host solo dice que los cuatro tracks buscaban incentivar curiosidad, creatividad y ambición [0:19:45] | 8 |
| 🛡️ AI Security | Brecha. Cairos (?) apoyó este track con mentores [0:18:39] | 6 |
| 🤑 Agentic Money | Brecha | 4 |
| 🛸 Future | Brecha. En la intro la transcripción corta la lista y no se oye el nombre; sale de los capítulos | 7 |

No hubo track Physical World ni de hardware en esta sede.

## Proyectos

| Marca | Proyecto | Track | Qué hace | ¿Físico/hardware? | Preguntas del jurado |
|---|---|---|---|---|---|
| [0:27:42] | Addie (el equipo se presenta como «pacesis» (?)) | Agentic Money | Agentes escuchan streams en vivo y compran espacio publicitario en tiempo real según el contexto, con pago on-chain en la mainnet de Ethereum. | no | ¿Cómo se colocan las órdenes: es una agencia o se setean según la audiencia? · Si fuera merchant, ¿qué valor agregado o ROI me proponen? |
| [0:37:37] | Gohan | Vertical AI | Chat IA para cadenas de gimnasio que ajusta la rutina conversando y cita research; se integra con MCP y componentes HTML. | no | ¿La conexión con el gimnasio es vía MCP? · ¿El contexto del usuario lo guardan ustedes o el gimnasio? |
| [0:45:06] | Beto | Vertical AI | App móvil para adultos mayores que detecta patrones de estafa en pantalla (regex sin conexión, LLM con conexión) y llama a un contacto de confianza. La demo falló en parte. | no | ¿Beto escucha todo lo que pasa en el teléfono? ¿Cómo resuelven el acceso a la información? ¿No es invasivo? · ¿Quién es el cliente? · Cuando detecta una estafa, ¿cuál es el flujo? ¿Llama automáticamente? |
| [0:57:10] | Orbit | Future | Convierte el material de estudio que sube el alumno en microclases cortas tipo «brainrot», con imagen generada por IA y audio. | no | ¿Qué tanto está mockeada la demo? Si subo una clase de programación, ¿responde igual? · ¿Funciona en el teléfono? · ¿Cómo evalúan que el contenido sea correcto? |
| [1:10:13] | negocIA | Agentic Money | Marketplace propio donde los agentes del comprador y del vendedor negocian el precio por ti. | no | ¿Dónde negocian? ¿El marketplace es de ustedes? · ¿No pensaron ir a otro marketplace en vez de hacerse cargo de la oferta y la demanda? · ¿El vendedor también confirma o es automático? |
| [1:18:51] | Consentinel | Future | Middleware de riesgo para pagos agénticos: detecta anomalías con grafos, montos y wallets nuevas, y exige verificación biométrica por WhatsApp; se expone por MCP. En la demo salió un happy path sin querer por el umbral configurado. | no | ¿Es B2C o B2B? ¿Cómo se integra técnicamente con mi OpenClaw (?)? · ¿Qué otras validaciones hacen además de montos y direcciones nuevas? · ¿Quién es el cliente dentro del B2B? |
| [1:27:27] | Hackan't | AI Security | Muestra una exfiltración real de credenciales con un settings.json inyectado en un repo que se abre con Claude Code, y ofrece un proxy que bloquea comandos, con dashboard y risk score por empresa. | no | ¿Por qué Anthropic decidió no parcharlo? · En una empresa, ¿bloquea o pide aprobación? ¿No genera fricción? · ¿Cómo funciona técnicamente en la computadora, leyendo todo el tiempo? |
| [1:41:14] | MCD | Vertical AI | Farmacovigilancia: un agente de WhatsApp conversa con el paciente, analiza fotos y multimedia (palidez, ojeras) y genera en tiempo real alertas de eventos adversos para el laboratorio. | no (visión sobre fotos del paciente) | ¿Se lo venden al creador de la droga? · ¿Cómo es la distribución? ¿Cómo le llega al paciente el WhatsApp del laboratorio? · ¿Qué incentivo tiene el médico para usarlo? |
| [1:49:14] | KnowAhuman | Future | Un gemelo digital simula conversaciones con los agentes de otras personas y da un % de compatibilidad para hacer networking; corre sobre OpenClaw (?). | no | ¿Dónde vive esto? ¿Cómo es la distribución? · ¿Quién lo usa? · ¿Cómo se concreta el match final: cómo me junto con la persona? |
| [1:58:57] | Platan Pay | Agentic Money | IA que busca y compara productos y ejecuta el pago (wallet, Mercado Pago) con aprobación humana. | no | ¿La interfaz es la plataforma o WhatsApp? · ¿Cuál es la estrategia técnica para abarcar toda la oferta? ¿Scraping? · Si el seller no tiene Mercado Pago, ¿cómo se acoplan a otros métodos de cobro? · ¿Qué cobran y a quién? ¿Cómo evitan que los usen solo como comparador de precios? |
| [2:11:35] | T2M (Take Me to Market) | Vertical AI | Cinco agentes automatizan el go-to-market de una startup: ICP, compra de dominios y DNS, warmup de mails, outreach y blog. | no | ¿Cuál es el scope? ¿Hasta dónde llega? · ¿Cuál es el go-to-market de ustedes? |
| [2:19:57] | Tranquera | AI Security | Reglas de la organización que interceptan los prompts de Claude Code y bloquean u ofuscan API keys, IPs privadas e información confidencial; tiene dashboard de eventos y sugerencias de reglas con IA. | no | Implementación técnica paso a paso: ¿a dónde va el prompt y quién lo analiza? · ¿Cómo me aseguro de que lo usen todos los devs sin instalarlo uno por uno? |
| [2:26:35] | Omni («OVNI») | Future | Red que conecta los agentes locales del equipo (Claude Code vía servidor MCP) para compartir contexto y que el agente de alguien responda por él. | no | ¿Cómo se implementa? ¿Quién es el usuario? · Puede invadir la privacidad: ¿cómo evito que mi jefe pregunte si fui al baño? |
| [2:37:52] | Atajo | Agentic Money | Chat que arma un plan y ejecuta operaciones entre apps financieras (broker Wallbit (?), wallet cripto) con aprobación del usuario. | no | ¿Cómo pensaron la seguridad: la frase semilla y la conexión con distintas billeteras y cuentas? ¿Cómo opera hoy? |
| [2:48:12] | Verbalize | AI Security | Audita la alineación leyendo los estados internos del modelo con Natural Language Autoencoders (paper de Anthropic de hace tres días) y los compara con el output usando un LLM juez; usa modelos open source en GPUs propias. | no | ¿Esa capa está disponible para modelos vía API, como Anthropic u OpenAI? · ¿A quién se lo venden? |
| [2:55:25] | Verenice («Very Nice») | Vertical AI | Equipo de marketing IA para microemprendedores: elige el producto ganador, genera creatividades y propone una campaña de Meta Ads que el usuario aprueba por WhatsApp. | no | ¿Cómo lo van a distribuir? ¿Quién es el cliente? · ¿Es una app de Shopify o de Tienda Nube? · ¿Cómo resuelven el setup: carga del catálogo e identidad de marca? |
| [3:02:40] | Vibefence | AI Security | Plataforma de defensa para agentes de código: bloquea prompt injection en tiempo real, hace red team agéntico y saca snapshot y rollback de la base de datos. | no | ¿Cuál es el scope? ¿A dónde apuntan? |
| [3:09:05] | alethIA | Future | Agrupa noticias de varios medios por evento con embeddings y clustering; Claude saca la «verdad consensuada», las discrepancias y los datos aislados. | no | ¿Quién es el usuario? ¿Es B2C? · ¿Yo cargo mis fuentes o ustedes scrapean? · ¿De dónde sale la información? |
| [3:17:38] | yieldOS | AI Security | Plugin para Claude Code y Codex con «counterexample-driven security contracts»: ante un bug genera un contrato, un contraejemplo y una prueba, y reutiliza el fix en local sin gastar tokens. | no | ¿Qué moat tienen para no ser el próximo feature de Cursor o Claude? · ¿Cómo monetizan con empresas? |
| [3:26:42] | zero. | Future | «Know your agent»: el dueño de un agente se identifica con biometría o DNI, vía MCP y SDK, para poder rastrear quién está detrás de un agente malicioso; claves post-cuánticas. | no | ¿Quién es el cliente? Si estafan hoy a un familiar, ¿cómo sería el paso a paso para rastrearlo? · ¿Tendrían que estar conectados a la cuenta business del otro lado? · ¿Con qué aplicación se integraron en estas 36 h? · ¿Cuál es el desafío de acá en adelante? · ¿Cómo asocian el agente con la persona? |
| [3:35:12] | Twin | Future | Gemelo digital reutilizable («login con Twin») que las apps consultan con permisos revocables para personalizarse; se entrena con entrevistas basadas en un estudio de Stanford y Google DeepMind. Menciona hardware solo como visión a futuro. | no | Sin preguntas; solo comentarios (ver más abajo). |
| [3:42:10] | brunito | Vertical AI | IA que audita y apoya al docente: cruza el plan anual con el programa del Ministerio, registra el libro de clases por voz y sugiere material. | no | ¿Qué incentivo tiene el profesor para cargar la información de forma proactiva, si hoy no lo hace? |
| [3:50:12] | wardlm | AI Security | Seguridad a nivel de sistema operativo: intercepta las syscalls exec de Linux que lanzan los agentes, un LLM las valida y cancela las peligrosas; tiene dashboard y policies enterprise. | no | Sin preguntas («No hay preguntas» [3:55:06]). |
| [3:55:08] | Helix | Vertical AI | Equipo de agentes de growth: analiza el repo, propone y programa features detrás de feature flags, mide con PostHog, deja la ganadora y borra el resto. | no | ¿Los agentes prueban en producción? ¿Cómo hacen la analítica? · ¿Cómo medirían la performance de la feature? · ¿Qué es lo principal: el lado de ingeniería o el de producto? |
| [4:03:24] | casitaFast | Vertical AI | Agente que scrapea portales inmobiliarios (Zonaprop), vectoriza los avisos, los rankea según tus preferencias y contacta al vendedor por WhatsApp. | no | ¿Qué próximos pasos ven en scraping y cómo se diferencian técnicamente para dar una experiencia rápida y que optimice tokens? · ¿Cómo evitan que los bloqueen al scrapear? · ¿Cómo consiguen el teléfono del vendedor? |

## Ganadores

| Track | 1° lugar | 2° lugar |
|---|---|---|
| Vertical AI | **MCD** [4:34:35] | Helix, score 0.63 [4:33:52] |
| AI Security | **Tranquera** [4:36:27] (se oye «22»; el score no es legible) | Hackan't [4:35:13] |
| Agentic Money | **Addie** («AD») [4:38:09] | Atajo [4:37:15] (se oye «29»; el score no es legible) |
| Future | **Twin** [4:40:00] | Orbit, equipo 25 [4:38:44] |

- **Ganador general: Tranquera** [4:41:30]. Se oye un premio de «700» (?) dólares y un pasaje a Chile para competir en la hackatón de fin de año [4:44:42].
- **Predicción del mercado** [4:33:16]: Tranquera 45%, zero. 42%, Twin 8%. El host remató con «el mercado lo supo» [4:41:30].
- **Ganador del Platanus Hack Market**: Tommy Leonel (?) [4:43:31]; su estrategia fue «comprar barato y vender caro».
- **Votación popular**: se anunció [0:26:00], pero el resultado no aparece (Brecha).

## Preguntas del jurado por tipo

Total contado: 62 preguntas, de 23 equipos con ronda de preguntas. Twin y wardlm no recibieron preguntas.

1. **Técnica, arquitectura, integración y origen de los datos: 19**
   - «¿Cómo funciona técnicamente en la computadora para estar leyendo todo el tiempo lo que está pasando y comunicándolo?» [1:39:23] (Hackan't)
   - «La implementación técnica paso a paso: desde que escribo la prompt, ¿a dónde fue esa prompt entera? ¿Quién la analizó?» [2:25:01] (Tranquera)
   - «¿Esa capa está disponible para modelos que no corran ustedes, vía API key de Anthropic u OpenAI?» [2:53:44] (Verbalize)
   - «Uno de los problemas que tengo cuando empiezo a scrapear es que me bloquean… ¿cómo evitáis eso?» [4:09:30] (casitaFast)
2. **Negocio: quién es el cliente, quién paga, cuánto se cobra: 11**
   - «¿Quién es vuestro cliente?» [0:55:37] (Beto)
   - «¿Qué cobran? ¿A quién se lo cobran: al proveedor o al comprador?» [2:10:14] (Platan Pay)
   - «¿A quién se lo venden? ¿Quién sería el cliente de la solución, de forma factible?» [2:54:16] (Verbalize)
   - «¿B2C o B2B?… ¿Quién es tu cliente dentro del B2B?» [1:24:54]/[1:26:01] (Consentinel)
3. **Distribución, go-to-market y adopción: 10**
   - «¿Qué incentivo tiene el médico para usar esta plataforma?» [1:47:18] (MCD)
   - «¿Cuál es su go to market? El de ustedes.» [2:18:39] (T2M)
   - «¿Cómo me aseguro de que lo usen todos y que no lo tenga que instalar uno por uno?» [2:25:33] (Tranquera)
   - «¿Cuál es el incentivo para el profesor para cargar esta información de manera proactiva?» [3:48:28] (brunito)
4. **Flujo de usuario y operación: 8**
   - «Cuando detecta una estafa, ¿cómo es el flujo? ¿La persona mayor llama automáticamente?» [0:56:13] (Beto)
   - «¿Cómo se imaginan el flujo en una empresa?… si todo va a necesitar una aprobación, no deja de ser una fricción» [1:38:50] (Hackan't)
   - «El comprador tiene que confirmar el deal; ¿el vendedor es lo mismo o es automático?» [1:16:34] (negocIA)
   - «Si estafan hoy a un familiar, ¿cómo sería el paso a paso para rastrearlo?» [3:31:40] (zero.)
5. **Alcance del demo: qué es real, qué está mockeado y cuál es el scope: 6**
   - «¿Qué tanto está mockeada la demo para este caso particular? Si subo una clase de programación, ¿qué tan bien responde?» [1:07:24] (Orbit)
   - «¿Funciona en el teléfono?» [1:07:56] (Orbit)
   - «En estas 36 horas, ¿con qué aplicación se integraron?» [3:32:45] (zero.)
   - «¿Cuál es el scope? ¿A dónde apuntan?» [3:07:48] (Vibefence)
6. **Competencia, diferenciación, moat y propuesta de valor: 4**
   - «¿Qué moat o ventaja competitiva ven para no ser un próximo feature de Cursor o de Claude?» [3:24:41] (yieldOS)
   - «¿Cómo evitan que los usen solo como comparador de precios?» [2:10:14] (Platan Pay)
   - «Si fuese merchant… ¿cómo le venden la eficiencia o el valor agregado que le dé ROI?» [0:36:37] (Addie)
   - «¿Por qué decidió no parcharlo?» [1:37:42] (Hackan't; sobre si el incumbente resolverá el problema)
7. **Privacidad, datos y seguridad: 3**
   - «¿Beto está escuchando todo lo que pasa en el teléfono?… ¿cómo piensan resolver el acceso a la información? Un poquito invasivo, ¿no?» [0:54:30] (Beto)
   - «Puede aumentar mucho la productividad, pero también invadir mucho la privacidad. ¿Cómo prevengo que mi jefe pueda preguntar si fui al baño?» [2:36:14] (Omni)
   - «Las preguntas son en torno a seguridad: la clave semilla y la conexión con las distintas wallets» [2:44:47] (Atajo)
8. **Calidad o correctitud de la salida de IA: 1**
   - «¿Cómo evalúan que el contenido sea correcto?» [1:08:31] (Orbit)
9. **Sin ninguna pregunta en esta sede (Brecha):**
   - por qué usar un LLM o uso de IA;
   - validación con usuarios reales;
   - regulación (en Atajo, SOC 2 lo sacó el propio equipo en la respuesta [2:45:54], no el jurado);
   - equipo;
   - escalabilidad como categoría propia (solo aparece de refilón en casitaFast, con «búsquedas masivas» y tokens [4:08:57]).

## Lo que el jurado elogió o criticó

**Criterio general del host**
- [0:18:39]: la demo y el producto pesan más que el modelo de negocio.
- [4:30:21]: agradece a los jueces por hacer «preguntas coherentes y buenas».

**Elogios**
- Beto [0:53:58]: a pesar de que la demo no salió como querían, resuelve un problema real que «cada vez va a ser más fuerte».
- Orbit [1:07:24]: «Creo está súper bueno»; la educación va a dar un giro en los próximos años.
- Consentinel [1:24:19]: el filtro en pagos agénticos «va a ser una tendencia».
- Hackan't [1:37:42]: «Felicitaciones. Muy bueno.»
- MCD [1:46:45]: «Muy bueno.»
- Omni [2:36:14]: «Está muy bueno el producto», aunque ve un riesgo de privacidad.
- Atajo [2:46:58]: problema real, ambicioso, hay oportunidad.
- Verenice [3:01:28]: un juez lo llama «mis sueños húmedos», porque es el problema de demanda y setup que viven en su empresa (¿Olaclick?). El host remató con «Muy bien, chicos. Felicitaciones» [3:02:41].
- zero. [3:31:40]: «muy ambicioso».
- Twin [3:40:03–3:41:41]: «superinteresante»; como protocolo «eventualmente va a estar en algún lado»; «espectacular, me pareció muy muy sólido». El host agregó «Excelente presentación».
- brunito [3:50:10]: «Bien presentado.»

**Críticas y sugerencias**
- Gohan [0:43:51]: el valor agregado está en subir una capa por encima del MCP, en el contexto previo del usuario.
- negocIA [1:17:08–1:18:45]: un marketplace de dos puntas, en un ecosistema B2C tan competido, requiere un capital inmenso. Le sugieren tomar una sola punta o acoplarse a Mercado Libre, Mercado Pago o Facebook Marketplace, donde sí se negocia y la oportunidad es real.
- KnowAhuman [1:55:33–1:58:18]: lo ven más alineado a prospección y ferias. Le critican que un onboarding con cuestionario difícilmente se despegue de lo que ya existe y le sugieren nutrirlo del historial del usuario con sus LLMs.
- Platan Pay [2:10:51]: «Es muy complejo lo que quieren hacer». Le recomiendan ir por B2B o vivir dentro de Meli.
- T2M [2:18:06–2:19:44]: el potencial está en la distribución, poco explotada. Le sugieren un marketplace de Shopify o Vercel. Lo «one shot» es más fácil; el valor está en pivotear y acomodarse en el tiempo, no solo en mandar mails. Cierre: «Es muy bueno, chicos».
- Atajo [2:46:58–2:47:32]: debió mostrar que resuelve la integración y las autenticaciones con todas las billeteras y bancos, que es la barrera real; los gráficos son lo fácil. Las empresas B2B que hacen wrappers de bancos «la rompen toda».
- Vibefence [3:08:52]: «el que mucho abarca poco aprieta»; tiene que elegir dónde profundizar.
- Twin [3:40:35, 3:41:41]: no ven a alguien repitiendo entrevistas en el futuro; debería consumir de otras fuentes, como el MCP de Spotify.
- Helix [4:01:46–4:02:18]: «Está bueno lo que hicieron», pero debería distinguir si resuelve ingeniería o producto, porque son dos cosas distintas.

**En la premiación**
- Addie [4:38:09]: «yo sabía, muy bueno, merecido».
- Twin [4:40:00]: «Merecido».
- Tranquera [4:41:30]: «El mercado está en lo correcto».
- **Brecha:** no se explica por qué ganó cada proyecto.

## Relevante para nuestro proyecto

- En Buenos Aires no hubo track Physical World ni proyectos con hardware, cámaras en terreno, sensores, industria o mantenimiento (Brecha). No hay precedente directo de qué preguntan a un proyecto físico.
- **MCD (1° Vertical AI)** usa visión sobre fotos del paciente (palidez, ojeras) en un dominio regulado. Le preguntaron quién paga (el laboratorio), cómo se distribuye y qué incentivo tiene el actor que debe usarlo (el médico).
- **brunito** audita el cumplimiento de un plan frente a una norma, lo más parecido a verificar una pauta. La única pregunta fue el incentivo del usuario operativo para registrar, que en nuestro caso es el incentivo del operario.
- **Beto** detecta en tiempo real con un modo sin conexión (regex) y un LLM cuando hay conexión. Le preguntaron por la invasividad y los permisos, quién es el cliente y qué pasa exactamente cuando detecta.
- **Omni** recibió la pregunta de privacidad laboral: «¿cómo prevengo que mi jefe pueda preguntar si fui al baño?». Es casi seguro que nos la hagan con la cámara sobre el operario.
- **Tranquera (ganador general), Hackan't y wardlm** interceptan en tiempo real con una capa rápida de patrones y una de LLM. Les preguntaron por la latencia, la fricción en el flujo de trabajo y cómo asegurar que todos lo usen.
- **Consentinel** muestra el riesgo del demo en vivo: el umbral mal configurado produjo un happy path sin querer. Conviene llevar el caso de fallo ensayado.
