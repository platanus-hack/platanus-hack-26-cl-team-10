# Platanus Hack 26: Caracas · Presentaciones finales

> Fuente: <https://www.youtube.com/watch?v=6mIvorbU_T0>. Transcripción automática de YouTube (español), sin corregir: los nombres propios y términos técnicos pueden venir mal escritos. Los capítulos salen de la descripción del video. Generado con `scripts/yt_transcript.py`.

## Descripción del video

```text
De cero a producto en 36 horas. Los mejores hackers de Venezuela presentan lo que construyeron en 36 horas, en la cuarta edición de Platanus Hack 26: Latam Tour,  en Caracas.

0:00 Espera inicial
0:33 Introducción / recap
17:34 Constancia | 🤝 Trust
32:33 Rastro | 🤝 Trust
40:03 SmartTraffic | 🤝 Trust
53:44 mus3o | 🧊 Three-Dimensional
1:01:27 Manito | 🚨 Emergencies
1:12:48 Arkangel | 🛡️ AI Security
1:19:08 Mapz | 🧊 Three-Dimensional
1:26:19 Gotchu | 🛡️ AI Security
1:41:15 VanGUARD | 🛡️ AI Security
1:49:23 ZeroID | 🤝 Trust
1:57:37 Céflow | 🧊 Three-Dimensional
2:04:54 Tridi | 🧊 Three-Dimensional
2:15:30 HAWK | 🛡️ AI Security
2:25:06 Arvi | 🧊 Three-Dimensional
2:31:52 Quórum | 🤝 Trust
2:39:03 Presente | 🚨 Emergencies
2:46:46 Veridian | 🛡️ AI Security
2:53:34 sIsA: Sistema de Identificación Seguro y Anónimo | 🤝 Trust
3:01:26 Qubbot | 🧊 Three-Dimensional
3:11:55 Aló Mamá | 🚨 Emergencies
3:20:01 AGENT ZERO | 🛡️ AI Security
3:27:54 Meshy | 🚨 Emergencies
3:33:59 Deliberación del jurado
3:52:35 Premiación y cierre
```

## [0:00:00] Espera inicial

**[0:00:09]** [música] [música] [música] [música] de Yomi en en Caracas.

## [0:00:33] Introducción / recap

**[0:00:36]** Para el el equipo de Platanus eh viajamos desde Chile para hacer eh esta hackathon junto a ustedes. Es la cuarta hackathon que hacemos este año fuera de Chile. Empezamos con Buenos Aires, después eh después México, Ciudad de México, después Bogotá, ahora Caracas y vamos a eh hacer nuestra última edición de este año en Chile. Eh vamos a partir eh saludando también a Ignacio. Ignacio es CTO de Yomi y nos quiere dar también eh la bienvenida, así que un

**[0:01:10]** fuerte aplauso aplauso para Ignacio. Adelante. ¿Qué tal? ¿Cómo están todos? Imagino un poco cansados. Fue un fin largo para ustedes. Eh quería primero preguntarles ¿para quiénes de ustedes este es su primer hackathon? Podríamos decir que es como la mitad. Bastante impresionante. Em ha sido uno largo, eh que este es el

**[0:01:44]** tercero que hacemos en la oficina y de hecho es el primero que que ha durado tanto. Eh los anteriores eh habían sido eh bueno, no habían sido de quedarse acá eh y en general no el fin completo, ¿no? Eh. Yo por mi parte, yo también estuve en un en un hackathon hace ya como como 10, 12 años, por ahí. Eh, eso fue antes de mi primer trabajo en programación. Eh, fue en la Universidad de Columbia en Nueva York, eh, y fue una experiencia

**[0:02:16]** increíble. Fue ese fue 24 horas, tampoco tan largo como este, pero fue una experiencia increíble eh a ver y donde conocí a muchas personas y y entendí lo que lo que era estar con un problema un tiempo. Claro, en ese momento no no había todavía gente de ahí, era todo a mano. Obviamente, me imagino que lo que lo que pudimos presentar ese día no no le llega ni a los pies a lo que van a tener ustedes hoy eh, teniendo en cuenta la la tecnología que ahora tienen en sus manos. Eh, pero eso me emociona mucho, me emociona poder ver que que pudieron hacer estas 30 y estas 36 horas.

**[0:02:48]** Eh. Y espero que de la misma manera que yo estuve en un hackathon hace 12 años, eh, y ahorita estoy como CTO de la empresa de tecnología más icónica de Venezuela. Eh, ustedes, estoy seguro que en de aquí en 12 años muchos van a poder de eh estar en una posición muy increíble. Eh, sea tan sea en Venezuela, sea en empresas eh globales, eh, sea en otros países, eh, pero quisiera que fuese en Venezuela, pues quisiera que que podamos todos todos aportar a a lo que está

**[0:03:20]** pasando ahorita en la reconstrucción del país. Eh, entonces nada, para desearles todo el éxito y y nada, que que gane el mejor. [aplausos] [aplausos] Gracias, Ignacio. Bueno, vamos a hacer un breve un breve repaso de lo que fue este fin de semana en Platons Hack 26 Caracas. Carita feliz.

**[0:03:58]** Eh. Antes de eso voy a explicarles muy rápidamente qué es Platanus para los que nos están viendo en el stream. En Platanus eh nos dedicamos a invertir en startups en etapa temprana. Comúnmente eh somos el primer ticket de inversión para estos equipos. Eh. Lo acompañamos con la inversión y además con una comunidad técnica muy fuerte de founders y CTOs. Esta iniciativa de Platanus Hack también son parte de eh agrandar nuestra comunidad técnica y acercarnos a a muy buen talento aquí en Latinoamérica. De hecho eh para esta Hack por ejemplo

**[0:04:30]** recibimos más de 400 postulaciones. Todos los que están en esta sala eh 100 hackers fueron eh las mejores postulaciones que pudimos ver. Eh así que también siéntanse orgullosos orgullosas de estar aquí. Y bueno, quería agradecer rápidamente también a nuestros sponsors. Eh esta Hack eh está auspiciada por Anthropic. Cada hacker tenía crédito para usar eh Cloud durante todo el fin de semana y obviamente ya conocen a Yomi. Eh muchas gracias también eh por habernos recibido eh en su oficina. Eh quería pausar un segundo para hacer

**[0:05:04]** un agradecimiento un poco más completo. A esta hora mi memoria eh no es la mejor. Así que quería agradecer también eh a toda la toda la ayuda del equipo Yomi que desde hace más de un mes están hablando como eh con nosotros muy de cerca. Eh. De primera Dan eh a a Dani, a Jana, a Arelis, a Johan, a Sebastián, Alejandro, Víctor, a Bea, a Natalie, a Marcos, a Henry, a Yomaira, a Yeni y a Eruis. [risas] A todo el equipo de Kaseya eh de verdad fue un gusto trabajar con ustedes. Eh lo

**[0:05:37]** hemos pasado increíble y espero que eh disfruten junto con nosotros el resto de las presentaciones. Un aplauso igual para Yomi, por favor. [aplausos] Perfecto. Ahora, sobre la hack, vamos a explicarle les voy a contar un poco lo que fue, esto fue el viernes ahí con más energía,

**[0:06:10]** eh, con menos canas tal vez. Estamos muy emocionados empezando el viernes en la noche, eh, después tuvimos una comida con nuestros mentores, eh, ahí está Bruno que nos acompañó desde Chile, cada equipo tenía, eh, un mentor que los iba guiando desde el brainstorming hasta, eh, la implementación de de su proyecto. Eh, tuvimos algunos algunos caídos en algunos caídos en en la guerra, eh, junto con Nacho también del equipo

**[0:06:45]** de plátanos, y hubo momentos de estrés también que tuvimos que, eh, tomar medidas drásticas. [risas] Razonable, razonable. Y ahora, vamos entonces, eh, a hablar un poco más de la competencia en sí, eh, la idea de esta competencia era era ir de cero a producto en 36 horas, entendiendo producto como una solución, una implementación técnica, dejando por esta competencia de lado la parte de, eh, modelo de negocios, etcétera.

**[0:07:19]** Eh, nos interesa mucho también la parte de curiosidad más desafío, eh, y en este caso, eh, parte importante de esta hackathon era que eran 36 horas, teníamos 3000 dólares en premios, eh, nos quedamos a alojar como ya vimos en algunas fotos, eh, Anthropic, Yomi, Eleven Labs, Capso, Render, Cacheado, eh, sponsors de esta hackathon. Y es importante también que las aplicaciones que ustedes crearon tienen que estar deployadas, eh todo acá es open source, y además parte importante era su interacción con los mentores eh cuidadosamente

**[0:07:52]** seleccionados. Ahora, cada equipo eligió un track eh o es es decir, un tema en el que trabajó durante el fin de semana. Estos eran los cuatro temas. En primer lugar, eh AI Security, eh cómo avanzamos en inteligencia artificial eh sin que se vuelva un peligro. En Trust, cómo creamos sistemas que nos permitan interactuar con entidades eh sin la necesidad de confiar eh ciegamente. Por otro lado, eh emergen- emergencias, cómo prevenimos o actuamos rápidamente ante emergencias.

**[0:08:25]** Eh esto claramente dado el contexto del del último terremoto en Venezuela. Y eh también eh tres dimensiones, que es eh explorar en base a las nuevas capacidades que nos están dando la IA, y específicamente en crear eh productos, proyectos que que que exploten la parte 3D. Es- estuvimos también con mentores, rápidamente eh los pueden ver aquí. Eh hay algunos que están también presentes eh eh acá mismo. Eh quiero que demos fuertemente un

**[0:08:58]** aplauso a todos los mentores por acompañarnos. [aplausos] [aplausos] Y vamos a saludar ahora a un pequeño typo, [risas] pero vamos a a dejarlo, ya conocen a a Diego. Ahora son socios. Eh bueno, pero

**[0:09:30]** eh voy a presentar rápidamente también a los jueces que gentilmente vinieron para acá. Eh Diego Ramos es CTO en Dugu. Eh, Dugu es una startup early stage eh un e-commerce eh enfocado en mascotas. Eh. Lo que me llamó la atención también de Diego es que él eh hizo en paralelo ingeniería y medicina. Así que es ingeniero y doctor. Por otro lado eh tenemos como ya ya conocieron a No, Diego Ramos he repetido claramente.

**[0:10:03]** A Ignacio, que es CTO en Yumi. Y por último eh tenemos a a Juan Vargas, que es founder de Big Bob, una software factory en Chile y nos acompañó también en la organización. Los criterios de evaluación. Importante. Los jueces ya los conocen muy bien. Los voy a repasar. 15% originalidad, 20% ambición, 20% ejecución, 25 aspecto técnico y 20 de impacto. Ya los explicamos en la en en la en la presentación inicial, así que por ahora voy a avanzar.

**[0:10:36]** La evaluación es cada cada juez asigna de cero a cinco puntos en cada una de estas dimensiones. Después obtenemos eh normalizamos los puntajes de cada juez eh según todas las notas que ha puesto. Esto permite eh poner a todas las las notas de los mismos jueces en una escala. Eh después promediamos los puntajes de cada juez y los ponderamos por sus notas. Y por último le aplicamos una escala lineal de cero a 100. Simplemente para que sea más fácil digerir el número.

**[0:11:10]** Eh de hecho, algo que implementamos nuevo para esta hackathon es que al final de las presentaciones y cuando llegamos a las premiaciones vamos a liberar los puntajes de cada uno de ustedes para que los vean su dashboard. Y pueden conocer qué tan bien están respecto al promedio o si están dentro del del top. Son 3 minutos de demo. Eso significa que mientras empiezan a hablar, 3 minutos hasta que terminan de hablar. 2 minutos eh de preguntas y un un minuto 30 para que los jueces evalúen y para

**[0:11:44]** que pase adelante el siguiente equipo. Tenemos 3,000 dólares en premio, como ya lo dije antes. Eh la demo se va a grabar, de hecho está hay un streaming funcionando que ya lo mandamos por Discord y se publica durante la semana. Cuando el el proyecto se publica de esta forma para que ustedes lo puedan agregar a su portafolio eh el equipo que en un periodo que ya vamos a dar gane más votos del público se lleva también un un premio de 400 dólares. En este caso ganó un proyecto que tuvo

**[0:12:16]** 613 puntos. Y ahora sí eh tenemos además una pequeña sorpresa y es que em habilitamos un mercado. Nuevamente no queremos incentivar de ninguna forma la ludopatía pero se nos ocurrió un juego interesante y es que eh cada hack todos empiezan con 1,000 bananas en una aplicación que ya vamos a mostrar el QR y el ganador se lleva un premio de 100 dólares. Eh el top 30% se lleva eh una

**[0:12:50]** una camisa de Suba Base y vamos a intentar predecir quién es el ganador de la hack por medio de por medio de medio de un de un mercado estilo Polimarket, se van a convertir en traders eh y van a intentar apostar por quién es el ganador. Okay, acá está el mercado. Espero que no hayan bugs. Si hay bugs se solucionarán. Okay.

**[0:13:24]** Ya viene el mercado en camino. Atentos a Discord. Okay. Vamos a empezar con la primera presentación. Vamos a llamar adelante al equipo.

## [0:17:34] Constancia | 🤝 Trust

**[0:17:36]** Bueno, nosotros somos Credenciales Constancia. Primero que todo. Hoy en día se estima que más del 90% de currículums que están en línea pasan por un tipo de sistema de inteligencia artificial que se encarga de descartarlos o aprobarlos. Esto significa que este sistema está automatizado. Eso eh no solamente de parte de los negocios que lo adoptan, sino también que los currículums que se mandan está este sistema también está automatizado. Existen agentes que son capaces de aplicar a millones, digo, múltiples, miles, décimas de vacantes

**[0:18:10]** dentro de estos negocios y automatizar el proceso de entrega. Entonces, tenemos agentes de un lado, agentes del otro. Eh esto no solamente involucra un factor de volatilidad, sino que no siempre los currículums, ya sea por la persona que está utilizando los servicios o por los propios agentes que optimizan el tiempo, eh la compatibilidad de eh el currículum con el trabajo, eh puede que los currículums no sean confiables. Nosotros queremos eh aumentar esta confiabilidad. Eso lo hacemos con nuestra eh Constancia. Constancia es un sistema que

**[0:18:45]** se encarga de procesar eh cartas de trabajo eh digitalizadas, encriptándolas con criptografía, y de esta manera, en la blockchain, podemos darle al empleado, que es el que eh es dueño de sus propios datos, eh la manera de probar los hechos que ha hecho durante su trabajo, las experiencias que tiene, de una manera en donde no exponga su nombre, edad, cargo o cualquier otra o atributo privado que él no quiera exponer al exterior y de esta manera las

**[0:19:17]** empresas pueden saber eh que de qué se trata eh su experiencia. Ahora vamos a ver el ejemplo. Aquí tenemos a nuestro empleado Carlos, él está en ah, perdón, aquí tenemos a Carlos que es nuestro empleado, él está en la empresa Andrómeda, por ejemplo, y él quiere buscar un nuevo trabajo. ¿Qué pasa? Que bueno, se cansa de que los CV siempre se lo devuelven, de que no terminan de confiar en la experiencia que él dice tener. Entonces, para aquí es donde viene nuestro sistema Constancia. Siguiendo el flujo que viene dado por nuestro eh no nuestro, sino el estándar W3C que seguimos e

**[0:19:50]** implementamos, eh la primera es la compañía que ya está registrada va a llenar los datos del empleado y del certificado en este formulario, donde va a emitir el el documento. Entonces, acá se empieza a procesar esta información para crear tanto el contenido de la capa visual, donde vas a ver el el certificado como los datos y eso, pero también incrustando un token donde vas a tener la firma, que es lo que va a garantizar que esos datos no hayan sido modificados, no hayan sido eh

**[0:20:24]** dañados en ningún de ninguna forma y que se verifique que esta constancia de trabajo sí viene de la empresa que dice el la información. Entonces, aquí, como se puede ver la capa visual, es tal cual como cualquier certificado, sin embargo, tiene el token incrustado y okay. Aplausos. [aplausos] Pero bueno, entendí.

**[0:21:11]** Ajá, ¿por qué enfocarse específicamente en constancias de trabajo cuando esto parece una solución para cualquier documento que tenga que emitir cualquier ente y deba ser verificado? Sí, este, ciertamente se pudiera tener como una forma general, sin embargo, eh por como lo vemos nosotros, también es que muchos eh estas plataformas tienen ya como sistemas legacy, por así decirlo, en cómo ya guardan esa información para pasar los certificados y etcétera. Y nosotros creemos eh sentimos que si nos centramos en un solo campo,

**[0:21:44]** eh podemos como adaptarnos a darles esa transformación de pasar esos esa información a nuestro sistema más fácil que si nos globalizamos y luego quizás Eh bueno, continuando con la idea, hay en todo un mercado ahí fuera eh que es con respecto a los sistemas ATS, que es para el tema del reclutamiento. Estos sistemas los usan muchísimas empresas y últimamente esos sistemas tienen muchos eh sistemas de inteligencia artificial que ayudan a hacer el match como dice mi compañero, pero no hay una manera real de saber que esos documentos que te mandan eh y la experiencia que dicen tener son lo que dicen ser. Entonces, esto ayudaría a tener un apoyo extra en

**[0:22:16]** el que ah con esa automatización podemos hacer o descartar incluso aquellos currículums o constancias que no realmente no son verdaderas. Entonces, sería todo un plus que le podríamos dar al mercado que ya de por sí está en crecimiento, pero que les hace falta esta pa- esta parte de confiabilidad con respecto a la información que hay allí. Eh O sea, ¿por qué el día de mañana, o sea, por ejemplo, productos grandes que si LinkedIn no

**[0:22:49]** pueden in- eh emplear la tecnología que ustedes están empleando y tener el moat que ustedes están buscando tener? Eh bueno, por lo que he visto en algunas empresas, realmente LinkedIn lo usan más que todo para captar, pero usualmente por detrás las empresas utilizan otros software que no necesariamente LinkedIn. Esto va más de cara es a la empresa que es la interesada en que tú consigas una vacante, eso cuesta dinero. Y el tiempo que tú inviertes en en recibir miles de currículums también es cuestiones en las que a lo mejor necesitas alguien urgentemente y todo ese filtro que tiene que hacer una persona que inclusive teniendo su trabajo automatizado por la

**[0:23:21]** IA pues lo pierde y no lo tiene ahí a la mano. Entonces con este tipo de sistemas realmente no sería tanto de cara a LinkedIn porque LinkedIn es la plataforma para captar toda esa información para la parte Gracias. [aplausos] [música]

**[0:26:36]** [música] [música] [música] [música] [música]

**[0:27:18]** [música] [música] [música] [música] Sí.

**[0:29:15]** [música] [música] [música] [música]

**[0:30:03]** [música] [música] [música] [música] [música]

**[0:30:49]** [música] [música] [música] [música] Hola.

## [0:32:33] Rastro | 🤝 Trust

**[0:32:33]** Hola, nosotros somos Rastro. Y bueno, eh en Venezuela y realmente en muchas partes del mundo, se recolecta una gran cantidad de dinero a nivel de donaciones. Pero aquí existe una pregunta. Muchas veces cuando nosotros donamos, no sabemos a dónde va exactamente ese dinero que estamos donando. Porque puesto las organizaciones a veces no muestran esa trazabilidad de a dónde va lo que nosotros estamos dando. Eso genera que muchas personas no quieran donar, ya que no confían en que genuinamente lo que ellos están dando,

**[0:33:07]** el dinero que están dando, la organización sí lo está utilizando para el fin que dijo que era. De esa forma, las organizaciones confiables normalmente llegan a perder este cierta cantidad de personas que les donen y a su vez también eh, existe menos cantidad de donaciones. Por eso creamos Rastro. Rastro es una plataforma para donar de forma transparente. Nosotros este queremos crear una forma de donar de forma segura. Funcionamos como una especie de intermediarios entre lo que sería eh, el donador y la organización o

**[0:33:42]** la ONG. En este caso, nosotros eh, funcionamos como una bóveda segura. Donde el donador nos entrega la donación y nosotros le entregamos a la organización el dinero por tramos. Donde en el primer tramo se le genera se le entrega una cantidad muy pequeña de dinero y aquí ellos nos entregan ciertos documentos que se con los cuales se va a verificar que efectivamente el dinero sí es usado para el fin que ellos dijeron que funcionaba su fundación. Si es verificado, de entonces de esa forma se le abona completamente toda la donación.

**[0:34:19]** Okay. Eh, aquí está la aplicación. Nosotros empezamos como un usuario queriendo realizar una donación y buscamos una organización a la cual donar, basándonos en la reputación que ellos tienen que en este caso eh, de los datos que cargamos está tiene una 80% de confiabilidad. Aquí están los datos de la trazabilidad, dando la los aportes recibidos y la trazabilidad de eh los de los gastos que han realizado las empresas. Eh podemos donar en USDT con nuestra wallet asociada a nuestra cuenta de Google. Em Aquí nos damos 50 USDT

**[0:34:55]** y se nos muestra eh cómo va a estar representada este gasto. Primero se le hace un porcentaje de de de se le hace la transferencia a la empresa de un porcentaje y se divide en los diversos tramos que puede abarcar eh a medida que la empresa va haciendo gastos. Luego, eh si yo quiero registrar una empresa, me eh me voy al apartado de registros, yendo a la información, envío la revisión y aquí estoy eh optando para una postulación a registrarme en esta

**[0:35:31]** institu en esta en esta plataforma. Y aquí tenemos nuestra apartado para subir gastos. Tiempo. [aplausos] Me parece super interesante esto, pero hay algo que no me quedó muy claro, que quién es quién verifica que el gasto realmente ocurrió más allá de una factura que que puede ser falsificada. Este, bueno, tenemos un sistema, un

**[0:36:06]** un agente de inteligencia artificial que este verifica estas facturas con el rif, tanto de nosotros como de la persona a la que se la vamos a mandar y este la razón. Este, ¿cómo? Eh también toma las facturas y evidentemente a futuro una especie de vídeo, porque los vídeos no se pueden falsificar tan fácil con IA y gracias a eso, este agente toma las tres partes eh, un agente entrenado y nos dice si es

**[0:36:38]** falso o si es verídico. Y bueno, además de eso también en el sistema todas las transacciones que se hacen del que se nos hacen a nosotros para poder darle dinero a las organizaciones ah, están al público. Cualquier persona puede acceder a estas transacciones. Eh, algo que a mí no me quedó claro es este, o sea, yo como persona que quiero donar a una fundación eh, o sea, la fundación abre como un pote y yo dono ese pote a través de su aplica de de de su página eh, o con o sea, ¿cómo funciona

**[0:37:14]** exactamente esa parte? Y dos, este, ¿por qué la fundación aceptaría recibir la la donación por partes y no este, de un solo canje? Porque a veces lo que están buscando es ese solo canje para cubrir X y Y costo que por partes no funciona. Okay, bueno, eh, eh, realmente la fundación debería acceder es para poder generar más confianza en su fundación, ya que ellos al no tener las trazas, nosotros estamos generando precisamente esa trazabilidad para que las personas que quieran donar puedan decir, okay,

**[0:37:46]** esta sí es una organización confiable, voy a donar hacia ti. Nosotros estamos dándole esa ventaja, de ustedes poder ver, okay, esto sí es algo confiable y así generarías más personas que quieran donar para tu fundación. Y lo de cómo funciona, sí, bueno, sí sería como una especie de bóveda, como usted dijo, como un pote que nosotros, tipo, eh, la página, sería como una, tendríamos la cuenta y ahí llevaríamos como el dinero, básicamente. Y nosotros sí se lo transferimos directamente a la ONG. O sea, somos el intermediario. El donante nos lo entrega a nosotros y nosotros a

**[0:38:18]** la ONG. ¿Tiempo? Ya. [aplausos] Sí, presenta ahora SmartTraffic, equipo

**[0:39:41]** 20. Se prepara equipo Messi. Es el equipo 15. Hola, ¿sabían ustedes que el 50% de la

## [0:40:03] SmartTraffic | 🤝 Trust

**[0:40:05]** población venezolana que maneja han caído en la matraca de un fiscal de tránsito? Bueno, Venezuela es literalmente el peor país en el índice de corrupción de toda América. Además, ¿ustedes sabían que todos los días se estima que se que mueren cinco personas en accidentes de tránsito vial o siniestros viales. Entonces, aquí hay una necesidad. La necesidad es que tenemos que generar de alguna manera confianza vial en Venezuela, apoyando la seguridad vial del país. Es por ello que nosotros desarrollamos Smart Traffic. Básicamente, Smart Traffic es un conjunto de modelos de inteligencia

**[0:40:37]** artificial que nosotros hemos entrenado para verificar y para detectar eh lo que viene siendo eh infracciones de eh infracciones de tráfico este en el entorno vial en distintas eh partes del país mediante la instalación de cámaras inteligentes. En particular, ahorita les tenemos una demo de unos compañeros que están justamente en este momento abajo, en el elevador del SCCC, simulando un semáforo real, con una cámara real. Y el sistema nos hace la detección de las placas como si estuviera en un semáforo en rojo. Fíjense que aquí se están generando las eh las multas

**[0:41:11]** automáticamente partiendo de lo que viene siendo eh las placas detectadas por nuestro sistema. Una vez con esto eh Okay. Ya vamos con él. Se va a usar el tiempo. Vale. [resoplido] Listo. Okay. Una vez con esto

**[0:41:42]** en nuestro sistema automáticamente estas multas van a estar llegando. Fíjense que aquí están toda la lista de las multas, así como todas las eh las placas de los de los elementos que estamos registrando. ¿Esto para qué? Para que el ciudadano tenga trazabilidad de lo que realmente se le está multando y no venga un fiscal de tránsito cualquiera a decirle, "Ah, mira, te comiste la luz." ¿Dónde están las pruebas? No hay pruebas. Entonces, bueno, lo tenemos aquí. Pero no solamente nos quedamos en eso. Nosotros también tenemos un servicio para ti, para mí, en el en el nos estamos protegiendo también de eh posibles situaciones mediante choques, mediante accidentes de tráfico,

**[0:42:17]** en el cual es no podemos dar suficiente evidencia. En este caso tenemos una demo también en la que nosotros vamos a simular un choque, porque bueno, obviamente no vamos a chocar un carro en esta demo. Pero vamos a simular un choque y vamos a ver cómo las distintas cámaras que tenemos programadas se conectan al mismo tiempo en el lugar del choque para tener ese evento en diferentes ángulos y así protegernos nosotros de este mal que nos puede causar cualquier tipo de confusión en el sentido vial del país. Eh Bueno, eh ¿por qué funciona eh nuestro

**[0:42:51]** sistema? Básicamente, nosotros no solamente queremos generar conciencia. Nosotros lo que queremos hacer es salvar vidas también. Se estima que con instalaciones como esta de las cámaras en los semáforos que lo que hacen es promulgar el cumplimiento de las normas de tránsito eh hay un 24% de menos muertes por accidentes viales, así como en Estados Unidos, que es donde nosotros tenemos esas estadísticas se estima que al retirar esas cámaras que hacen que la gente cumpla esos cumpla esas normas de tránsito. [aplausos]

**[0:43:34]** Buenas. Lo que le quería preguntar es cómo específicamente están haciendo la detección de de matrícula y si fue como están usando los pesos como de YOLO, por ejemplo, algo así, ya entrenado. Exactamente, es un Ah. O o le hicieron fine tuning encima o algo así. No, no, realmente es un modelo de de inteligencia artificial YOLO, que lo que hace es fijarse realmente en un solo objeto de una serie de imágenes o videos. Exactamente. Y entonces, mediante un mecanismo un poquito similar a lo que viene siendo OCR, se detectan automáticamente las placas y bueno, se registra la multa. Exactamente.

**[0:44:09]** Eh, y dónde lo entrenaron específicamente. Eh, Kael. Okay. Tanto como tu cámara, como la que hay en los semáforos, como la que haya del vecino que tenga el carro. Como sea, cualquier cámara que esté conectada a nuestro sistema genera una red que permite generar evidencia en cualquier sitio, en todo tiempo. Exactamente. Y si es, o sea, el el modelo es de Yolo, entonces. Este, qué data utilizaron para la prueba. Eh, básicamente nosotros agarramos un dataset de un montón de este de videos

**[0:44:45]** que tenemos de cámaras CCTV. Para posteriormente eh, nosotros tomamos un montón también de videos aquí para poder comprobar que nuestro sistema realmente está detectando las placas este correctamente y bueno, fíjense que aquí tenían el demo real, pues. También algo a aportar es que nuestro modelo permite ajustar la raya donde en teoría está el paso del semáforo automáticamente, es decir, no tiene que estar explícitamente la cámara en el semáforo, sino que puede estar un poquito antes, un poquito después y el modelo lo ajusta automáticamente hasta

**[0:45:17]** donde no debería pasar. Okay. [aplausos] Gracias. Meshi. Y se prepara Price Team 10. [aplausos] Literalmente se había caído el wifi,

**[0:45:55]** literalmente. Ah, pero ya agarró. Te lo voy a dejar aquí entonces. Okay. Ahora hay que ver que esté conectado Messi, ¿no? Sí. [música]

**[0:46:41]** [música] [música] [música]

**[0:47:25]** [música] [música] [música] [música]

**[0:49:33]** [música] [música] [música]

**[0:51:34]** [música] Sí. Todos, eh, quiero empezar con una

## [0:53:44] mus3o | 🧊 Three-Dimensional

**[0:53:45]** petición. Quiero que levanten la mano todos aquellos que pasaron por la universidad y les mandaron a leer PDFs larguísimos. Ahora quiero que la dejen levantada si realmente se leyeron todos esos PDFs. Claramente hay un problema, ¿no? Pero, ¿en dónde tenemos el problema? ¿En el contenido que nos mandan a aprender o cómo nos muestran esa esa información? Imaginen en bachillerato haber tenido alguna herramienta que, en vez de alguna herramienta de estudio para, en vez de sencillamente memorizar textos y

**[0:54:18]** fechas, poder vivir los acontecimientos que se vivieron en la época o, en cuestiones de biología, explorar las células, microorganismos de cerca, descubrirlos. ¿Y si empezamos a, en vez de solamente leer sobre un tema, pudiéramos entrar en él? Para eso creamos Museo. Museo es una plataforma que te permite pasar de una experiencia de estudio basada en texto, en memorizar, a experiencias interactivas en un espacio 3D donde las

**[0:54:50]** ideas tienen un lugar. Ahora vamos a pasar al demo. Aquí podemos ver el lobby y, eh, le podemos pedir tanto, eh, que analice nuestros apuntes y nos dé varias salas de aprendizaje o sencillamente pedirle un prompt. Tenemos un prompt con un tema de biología que vamos a generar. Ahí pueden ver cómo se genera el mapa a tiempo real. Cada sala es un subtema de ese temario completo. Y, este, tenemos un modo examen, un modo eh exploratorio. Ahora vamos a presentar el exploratorio. Cada tótem es, eh,

**[0:55:24]** digamos, un concepto, ¿verdad? Y las personas van aprendiendo, van a su propio ritmo. Acá tenemos una ficha. Pueden ver incluso las fuentes de donde saca para que no sea de una fuente, bueno, cualquiera. Este, podemos ir entre salas, puedes ir a tu ritmo, en verdad. Vas, te devuelves si no captaste completamente un tema. Aquí pueden ver a este Aris, que es nuestro asistente que, bueno, es tu tu guía, como todo museo tiene. Y una de las cosas que más emocionados estamos de mostrarle es el cuadro en vivo, que es, digamos, ese esa inversión que queremos conseguir para

**[0:55:57]** que las personas puedan realmente vivir el aprendizaje y que formen una, o sea, que tengan una experiencia más eh interactiva. Y también tenemos una cosa más que queríamos el siguiente paso de inmersión, no solamente hacerlo para web, para eh móvil, sino también que sea compatible con VR. Acá pueden ver al compañero este viéndolo todo. Y este, a ver, si si no se la guea. Y en tema de historia y de biología son los que hemos conseguido mejores resultados. Acá podemos ver una batalla

**[0:56:30]** de la batalla de los 24 de junio. Sí. Y este, bueno, muchas gracias a todos por escucharnos. Eh quien lo quien quien lo quiera probar es bienvenido, por favor, pruébenlo. [ovación] [aplausos] Acá le tuvimos que meter más trabajo

**[0:57:07]** para que funcionara. Él analiza tus eh PDFs y ya te saca, digamos, la esa sub subdivisión. De hecho, creo que tenemos uno ahí, no sé si lo puedes mostrar rápidamente, pero sí, tú le das una serie de apuntes, eh y él te lo a ver, en fuentes, exacto. En fuentes tú adjuntas el archivo. Desde Carabobo, exactamente. Sí, también de la batalla de Carabobo. Lo podemos generar con Aris y esto puede

**[0:57:46]** tardar un poco. Entonces, si quieren vamos haciendo otra pregunta. En el aspecto técnico, ¿cómo es que están actualmente generando las imágenes 3D y también la distribución de como de lo de la figura dentro del espacio? Las imágenes 3D no las estamos generando todas nosotros, consumimos, hicimos un MC inverso a bibliotecas de assets 3D, comparamos los assets 3D, algunos los modificamos y cuando no conseguimos assets 3D compatibles los creamos mediante el LLM. Y el layout de la habitación

**[0:58:18]** específicamente como quién lo decide, como dónde van las figuras dentro del espacio. El layout lo decide el análisis que hizo previo cuando analizó el documento. Muchas gracias. Sí, por ejemplo, con el modelo 3D, o sea, acaban de poner esto, ¿verdad? Y este fue el que se generó que es más o menos como que las los cuartos del tema, pero por ejemplo, el que estábamos viendo de la célula, ¿eso también lo generó el prompt o lo hicieron aparte y si lo si lo hace el

**[0:58:52]** prompt, o sea, cómo se genera? Eso lo generó el prompt a partir de primero assets que tenemos en el MCP de biología, de naturaleza, esos son las áreas que hemos visto que mejor resultados dan. Este y también a partir de figuras que el mismo tiene con el el motor gráfico que que es con three three GS y el React three fiber. [aplausos] [música]

**[0:59:52]** [música] [música] [música]

**[1:00:34]** [música] [música] [música] [música] Mmm.

## [1:01:27] Manito | 🚨 Emergencies

**[1:01:27]** Bueno, en Ciudad Piar, como en muchos lugares en La Guaira, eh 43% de las personas no tienen ingresos o menos de 50 dólares al mes. Y 45% de las personas eh perdieron sus ingresos por por el tema del sismo. Entonces, el problema que pasa con organizaciones como Impactemos es que en Ciudad Piar, como en lugares en La Guaira, todos dependen de nosotros y de donaciones externas, y eso no es sostenible en el tiempo. De esta forma entra la solución, Manito. Manito innova en dos puntos específicos.

**[1:02:00]** El primero es en la aceleración de censo y registro de datos a través de llamadas automatizadas. Les voy a mostrar esta primera parte. Nos vamos a la página de Manito, vemos que todavía no hay un registro de alguna víctima. Y voy a hacer un pequeño ejemplo de yo una persona como víctima llamando a Manito. Hola, soy Manito de Impactemos. Ahorita no hay una persona disponible, así que te atiendo yo con unas preguntas cortas para registrarte. ¿Cómo te llamas? Eh vale, Manito, me llamo Miguel y bueno, estoy aquí. Mucho gusto, Miguel. ¿A qué te dedicabas

**[1:02:37]** antes del terremoto y desde hace cuánto? Bueno, antes del terremoto yo era recepcionista, pero bueno, lastimosamente el edificio en el que trabajaba se derrumbó. Lo siento mucho. ¿Y desde hace cuánto te dedicas a eso? Bueno, yo tenía 10 años trabajando en eso y ahorita no sé qué voy a hacer. Lo siento mucho. ¿Alguien de donde trabajabas te podría recomendar como un doctor, tu jefe o un compañero? Si es así, dime su nombre y nosotros la

**[1:03:09]** contactamos más adelante. Eh bueno, te podría mandar el contacto de mi jefe, que eh se llama José Pérez y este te puedo dar su número después. Listo Miguel, estoy armando tu perfil y te escribimos con los próximos pasos. Listo, de esta forma podemos ver que se registra el perfil, esto es en cara a la organización. Tenemos ya por lo menos una data mínima de este perfil, pero por supuesto en un

**[1:03:42]** escenario real vamos a tener más información del censo y esto nos va a permitir entonces el segundo paso, que es la otra parte en la que innova este sistema, que es que a través de toda esta información podemos generar no solo estadísticas de impacto real que necesita esa comunidad, sino también por ejemplo, nosotros nos especializamos en el impacto educativo. Que es eh a partir de esto, cuál es la certificación que nosotros le podríamos otorgar a esta persona para que pueda conseguir trabajo. De esta forma entra otra entidad, un tercero, que son las compañías privadas en este país que están comprometidas a sacar a esta gente

**[1:04:14]** adelante y que eh les les prometerían vacantes. Eso. [aplausos] Gracias. De esta forma Manito intenta resolver un problema que en Venezuela que bueno, solo se puede resolver hablando. Gracias. [aplausos] Hola, ya sí. Eh mi pregunta es cómo

**[1:04:52]** están como ya reconociendo la voz y después que quién está guiando la conversación y cómo cómo lo están alineando para que haga las preguntas adecuadas. Eh el reconocimiento de voz lo hace un modelo de este speech to text eh que lo lo hace Eleven Labs, este probamos distintos modelos y Eleven Labs es el que hace el reconocimiento más más dentro de lo que probamos. Este y la idea es que este sistema también se adapta para que voluntarios hagan los que son los que reciben la llamada. Sin embargo, cuando no hay voluntarios, atiende la inteligencia artificial. Este Este es el sistema de Bacop, en teoría. Pero puede permitir que, bueno, que el

**[1:05:26]** que el proceso de registro sea acelerado. Para el demo, eh, ¿no llegaron a integrar con algún proveedor de telefonía o algo así? Por ahora solamente en la en la web. Eh, para el demo no, pero estamos en contacto con Telefónica para justamente realizar eso. Eh, y una pregunta, por ejemplo, ¿quién yo llamo y digo X y Y profesión, quién valida que de verdad tengo esa profesión y toda esa parte? Perfecto, eso es una es una buena

**[1:05:57]** pregunta porque por temas de tiempo en el demo no nos eh enfocamos mucho en eso. Si te das cuenta, nosotros solo hacemos una pregunta en el demo para verificar, que es que buscamos un tercero, pero nosotros desarrollamos cuatro técnicas distintas que son para verificación. Una de ellas, que este tuvimos que acortar por temas de tiempo, es que se empiezan a hacer preguntas a la persona acerca de su profesión. Y dependiendo a, bueno, son distintas variables, se hace a través de un proceso de inteligencia artificial un análisis entre ellos de emociones, de cómo responde la persona, de certeza. Tú puedes verificar que una persona sabe de

**[1:06:31]** lo que está hablando y por ende que que que efectivamente hizo ese trabajo y tiene esa experiencia. Y nosotros, después, de esa forma podemos eh se genera un score en el que nosotros podemos certificar, este, mira, esta persona efectivamente sabe de esto. Y eh entra la ONG que le recomienda un curso para certificarse. Y que puede ser muy corto o si si todavía le falta mucho, puede ser más largo. Y de esa forma, a la cara de la de la empresa privada, ellos dicen, bueno, ya esta es una persona que está lista, a esta persona le falta un poco. Y y bueno, está lista preparado para entrar, ¿no?

**[1:07:06]** Gracias a ustedes. [aplausos] Arcángel y se prepara Maps Team 16. [música]

**[1:07:45]** [música] [música] [música] [música]

**[1:08:32]** [música] [música] [música]

**[1:10:25]** [música] [música] [música] [música]

**[1:12:09]** [música] [música]

## [1:12:48] Arkangel | 🛡️ AI Security

**[1:12:48]** Esta es una dirección IP. Y este es un equipo que está conectado la red wifi del hackaton. Y esto es un puerto. Y detrás de este puerto conseguimos un servicio de base de datos. Una base de datos con un tamaño aproximado de 3 GB con 427 tablas. Pero no nos detuvimos ahí. Logramos acceder y leer data personal de usuarios, pagos y conciliaciones bancarias. Todo protegido. Ahora, un agente de IA nos ayudó a conseguir

**[1:13:20]** estas vulnerabilidades. Y nos planteamos la siguiente pregunta, si un agente puede externamente entrar, ¿quién está vigilando tu computadora? Y de ahí nace Arcángel. Un agente IA que vive dentro de tu computadora y protege. Se da cuenta de todos los cambios, investiga qué está sucediendo y encima te da soluciones de forma autónoma para poder hacerlo. Nuestra visión no es solo bloquear un puerto, sino que nosotros queremos entender qué herramienta está haciendo cosas indebidas.

**[1:13:52]** Porque cambiar una configuración es normal, incluso abrir un proceso. Pero la combinación, tiempo y momento pueden ser otra cosa. Ahora, la estamos lanzando el ataque el sistema que utilizamos para hackear el sistema. Y ya se lanzó. Y Arcángel ha detectado el el ataque. Ahora, entremos a ver la evidencia que que propone. Excelente.

**[1:14:24]** Esta es la evidencia. Y con esto nos ayuda a entender cuáles son los próximos pasos que podemos tomar que podemos tomar. Empezamos el día de hoy viendo cómo la inteligencia artificial puede acceder a un sistema desde afuera. Y Arcángel viene aquí para mostrarles cómo la inteligencia artificial puede proteger desde adentro. Muchas gracias. [aplausos] Eh, bueno, mi pregunta va más hacia

**[1:14:58]** producto, eh, exactamente qué decisión concreta ayuda a tomar el lo que ustedes están presentando, que eso fue como que lo que no entendí y bueno, también cómo lograron bypass, eh, que Claude les hiciera basically como un funnel para entrar a las computadoras de los demás, si es que de verdad eso fue lo que logró, que tampoco entendí bien. Sí, bueno, para lo que hicimos fue usar otro modelo de inteligencia artificial, porque con modelos Anthropic no se puede. Entonces, usamos un modelo Usamos un modelo de Dixie que no tiene

**[1:15:33]** el safe word activado y no se reusa a realizar ese tipo de task. Básicamente, mi prompt fue, okay, dentro de esta red Wi-Fi encuentra vulnerabilidades dentro de los dispositivos que están conectados. Entonces, dentro de esos dispositivos encontró alrededor de cuatro proyectos corriendo con los puertos expuestos y vio que habían varias bases de datos que tenían eh, por defecto un nombre y un password que son los típicos que usas para levantar ah cuando estás iniciando. Y bueno, de ahí lo que nos planteamos fue, okay, ¿cómo podemos hacer que un AI agent detecte en

**[1:16:07]** mi computador que alguien está intentando hacer un acceso indebido? Y ahí fue donde nació Arcángel. Arcángel lo que hace es eh, observar procesos, ver los logs, ver qué cambios están eh, ocurriendo en tu computador y si encuentra alguna anomalía, la reporta. Y bueno, dependiendo de la anomalía, te dice, okay, puedes hacer esta configuración eh, y tú puedes aprobar o rechazar los cambios que te está proponiendo Arcángel. ¿Qué tipos de ataques, eh, principales serían los los que ustedes monitorean y pueden detectar?

**[1:16:41]** Bueno, Arcángel está pensado actualmente para detectar eh un AI agent malicioso que se haya infiltrado dentro de dentro de tu computador y esté, por ejemplo, intentando encontrar environment keys eh que tengas dentro de tu computador y eh subirlas a a su página para luego hacer un drenado. Pero realmente la idea de Arcángel es que se adapte a cualquier tipo de ataque anómalo que pueda un agente externo intentar eh realizar sobre tu computador.

**[1:17:14]** Nuestro enfoque es en las redes Wi-Fi públicas, que es el riesgo de seguridad más grande y es como pudimos entrar aquí, ver qué está abierto en localhost, qué tiene una contraseña muy sencilla y acceder desde ahí. Esos son los ataques que buscamos responder. [aplausos] [música]

**[1:18:10]** [música] [música] [música]

**[1:18:55]** [música] [música]

## [1:19:08] Mapz | 🧊 Three-Dimensional

**[1:19:08]** Hola, nosotros somos Maps y te llevamos directo a la puerta. Actualmente con los GPS actuales de realmente tener referencias es muy complicado, más en ciudades como Caracas que hay autopistas, que hay elevados que van unos por encima de las otras, que todas las entradas vienen unas detrás de otras y no están bien este referenciadas. Entonces, bueno, gracias a esto en todos los procesos de envío y todos los procesos de de de viajes casi el 60% del tiempo se pierde en los últimos 100 metros, ¿okay? ¿Qué es esto? Cuando te preguntan, mira, ¿de qué color es el

**[1:19:40]** edificio? Eh, ¿cómo se llama la calle? Esto está cerca de dónde. Entonces, queremos evitar perder ese tiempo. Maps te lleva al punto exacto, a la entrada exacta del a la entrada exacta de del establecimiento con este la ruta sobre la calle sin sorpresas en la vía, es decir, te avisa con tiempo antes de que lo veas, este te avisa si hay policías acostados, si hay huecos, si hay algún tipo de señalización, pa este señales de alto, si hay algún cruce, eh semáforos, todo eso. No solamente somos un mapa.

**[1:20:15]** Aquí tenemos la diferencia entre cómo se vería un una autopista normal en Caracas con el los GPS que tenemos 2D y esto es cómo verías desde la vista del conductor con Maps, ¿okay? No solamente somos un mapa, nosotros podemos mostrar de forma este 3D todos estos elementos en la visibilidad que tienes dentro de tu parabrisas. Acá tenemos una demostración, este, este, bueno, una demostración de cómo se

**[1:20:48]** ve, este, bueno, no funciona el video, pero de cómo se ven las señalizaciones, este, cuando vas manejando, esto es un screen record cuando tienes la vista de la pantalla, o sea, lo pones como si fuese un Google Maps en en el dashboard del del carro. Después hicimos un pequeño prototipo para una reflexión en el parabrisas y se vería de esta manera que no se ve, no sé por qué no se pone el play del video, pero básicamente es que lo, este, reflejas en otro dispositivo y eso se refleja en en el parabrisas y te da las direcciones. Eh, así se ve cuando llegas a una

**[1:21:20]** ubicación de forma intuitiva, este, te deja en tu destino, no tienes que perder tiempo ubicándote en un mapa o pidiendo referencias. Y bueno, también funciona a pie. Les voy a mostrar un poquito, eh, el el demo, este, esta es la página principal del mapa, esta es la zona que más recorrimos, por la que tenemos más información de, eh, policías acostados, huecos, eh, cosas así, aquí ponemos cualquier tipo de, estas ya las tengo guardadas estas direcciones, pero puedes poner cualquier punto. Y aquí ves toda, eh, la maqueta en 3D, eh, puedes ver tu ruta, aquí cambias la

**[1:21:55]** ruta, este, a cualquier lugar. Y una vez que le das a conducir, pues te lleva a a esa vista que les mostré anteriormente. Gracias. [aplausos] Por lo que entiendo, aló, ajá, por lo que entiendo los datos los consiguieron ustedes mismos grabando en esas calles por donde transitaron. Es una combinación de varios factores.

**[1:22:27]** Eh, escaneamos y analizamos varias imágenes satelitales de las zonas en donde estuvimos también tomando vídeos y fotos, entonces al final y con mapas de la ciudad, entonces al final todos esos datos se contraponen unos con otros y tenemos no solamente la vista satelital que nos permite saber la altura de los edificios, sino también qué elementos hay en ese en esa calle, o sea, semáforos, pasos peatonales, toda toda la información la tenemos. A mí lo que no me quedó lo que no me quedó tan claro es es qué problema resuelve esto y cuál es la

**[1:22:59]** ventaja sobre la navegación 2D tradicional en Google Maps o Waze. Esa es una buena pregunta, lo hablamos mucho con nuestro este con nuestro coach. Eh en Venezuela las calles están muy mal señalizadas, no es como en otros países en donde tú dices, mira, yo vivo en Bartolomé 445 y te lleva exactamente a la puerta de tu casa, aquí todo se maneja por eh direcciones de referencias, en la panadería tal cruza a la izquierda y tres cuadras más allá y está mi casa. Entonces cuando tú pides un delivery, de hecho Amazon aquí no existe, o sea, no no hay forma de que llegue a tu casa, es muy difícil darle esa dirección de tu casa, aquí

**[1:23:32]** simplemente en el mapa tú seleccionas cuál es tu edificio y todas las este todas las rutas llegarían, ¿okay? Te lleva directamente a la puerta, exacto, así. O sea, tú buscas es que el wifi está mal, pero okay. Tú buscas aquí si puedes marcar alguno de otro edificio. Tú buscas aquí cuál es tu edificio, simplemente lo seleccionas y la ruta se va a hacer, no tienes que saberte ni cómo se llama la calle, ni cómo se llama el edificio, ni de qué color es el edificio, que es lo que más preguntan los deliveries. Y para complementar eso, este como tenemos el render 3D, a veces cuando ponemos una ubicación en Google Maps normal no te da exactamente el punto,

**[1:24:04]** sino que es una zona eh aproximada y puede tener una un algún tipo de error, acá como estamos complementando ese mapa, eh es mucho más exacto eh el punto donde te deja y bueno, de la manera que mostré en la presentación, lo puedes ver, no es como que te vas a a ubicar en un mapa 2D donde estoy parado, sino que pones la cámara y te te muestra exactamente en donde está tu destino. Como si fuese un videojuego, prácticamente. En GTA te va saliendo en el vídeo. Perdón. Perdón. Gracias. [aplausos]

**[1:24:37]** Gracias. Team 6, Gotchu. Y se prepara Vanguard, team 22. [música]

**[1:25:14]** [música] [música] [música] [música]

**[1:25:58]** [música] [música] Organizaciones globales enfrentan 2000

## [1:26:19] Gotchu | 🛡️ AI Security

**[1:26:21]** ataques por semana y eso en Venezuela puede verse como 17, pero no 17 ataques cada semana o incluso cada año, sino 17 ciberataques cada minuto. Todos acá hemos desarrollado distintas soluciones que bueno, van a tener clientes en el futuro, pero ¿un poco han pensado qué tan segura es esta solución? No se preocupen, we got you. Desarrollamos una plataforma [risas][grito ahogado] desarrollamos una plataforma de seguridad eh para pequeñas y medianas empresas eh que bueno, no cuentan

**[1:26:55]** todavía con esta infraestructura. Eh Gotcha se integra en su proyecto y también revisa el código de su aplicación, de su web de manera cero intrusiva y esto para eh detectar vectores de ataques y eh guiándolos desde el análisis hasta la solución. Básicamente tratamos de ofrecer una solución completa que pueda hacer tanto análisis externos como análisis internos por medio de las URLs y cualquier cosa que pueda acceder interna externamente cualquier persona como por medio de un repositorio en

**[1:27:28]** GitHub que ustedes mismos le puedan subir. Tenemos por aquí, vamos a hacer un pequeño ejemplo. Este repo que está por acá lo voy a empezar a analizar. Y mientras se analiza también les quiero compartir todo lo relacionado al tema de vigilancia. Porque aparte de las soluciones que ofrecemos tanto de auditoría interna como externa también estamos monitoreando constantemente los diferentes sitios web de amenazas para ver si alguno de ellos se correlaciona con su repositorio o con su aplicación y así poder detectarlo eh de manera adecuada y yo poder ofrecerle soluciones a ustedes para que puedan

**[1:28:00]** implementarlo de su dentro de su dentro de su infraestructura. Básicamente con el reporte que se genera que todavía se debe estar generando empezamos a ofrecerles una cantidad de pasos que pueden a tomar desde desde la desde la desde la app y así poder solucionar la directamente, porque ella crea crea un pequeño sandbox en el cual una gente ve, entra y repara el daño y sube un y sube un PR. Y ustedes, obviamente, tienen como el human interloop para poder hacerlo y para poder aceptarlo para que pueda integrarse. Ahora bien, eh las empresas, bueno, se

**[1:28:34]** ahorran entre 1.9 y 2.2 millones de dólares cuando utilizan eh sistemas automatizados de inteligencia artificial para pues cuestiones relacionadas con seguridad. Y esto hace que en casi 100 días, pues la la vulnerabilidad sea solventada, algo que Gotchu lo hace en minutos. Y adicionalmente, pues, nos estamos enfocando en un mercado global de 400 millones de pymes y a nivel nacional de 100,000. Y finalmente, pues, pueden escanear el QR, incluso probar también eh Gotchu, y nosotros lo que hacemos es arreglar esto que es

**[1:29:06]** importante sin romper lo que ya está funcionando. Muchas gracias. [aplausos] Aló, ya ahí sí. Bueno, mi primera pregunta es cómo cómo se diferencia esto versus, por ejemplo, la skill de review de Codex más un please fix. Claro. Eh pues, implementamos un montón de infraestructura por detrás. Tenemos un montón de infraestructura en LangChain que básicamente está constantemente monitoreando eh en redes sociales, en

**[1:29:40]** blogs de hackers y este tipo de cosas y que te permite directamente agarrar eh crear dentro de la propia página web unos pasos que tú puedes agarrar como agente que la agarre, te resuelve y te mete un PR sin necesariamente cambiar el repositorio a menos que tú se lo permitas. Eh mi pregunta va más hacia la infraestructura de eh de Gotchu. Lo que, o sea, como yo lo veo es que, hoy en día la gente hace como herramientas de inteligencia artificial que no son eh I Neref en el sentido de que están codiadas y están modeladas las

**[1:30:14]** arquitecturas de inteligencia artificial detrás de esto, sino que simplemente se conectan por ejemplo a Skills de Cloud o bueno, cualquier o sea, cualquier modelo de inteligencia artificial este, entonces ¿en qué mi o sea, mi pregunta es como cómo ustedes validan que realmente la alerta que están levantando Gochu es real, sabes, como las métricas que hayan utilizado o cómo validan la precisión, o sea, los falsos negativos, los falsos positivos, toda esa parte que es importante y bueno, Cloud no te especifica cómo lo hace. De acuerdo, gracias por la pregunta. Primero teníamos como teníamos un subset

**[1:30:47]** que de de pequeños ataques que son los más ataques más comunes y esos ataques literalmente lo que hacemos es a promedio de código agarrar, inspeccionar el código y ver si se hace bien. Y dependiendo de un score qué tanto esté dañado, por así decirlo, el código de la aplicación, agarramos y desplegamos un agente que básicamente no es que entrenamos, pero que sí eh le pusimos una cantidad de safe bars alrededor para evitar y de que dañe la aplicación por algún sentido, por algún medio de algún breaking change en general y que en general pueda agarrar y resolver el problema con la información que ya hay en internet actualmente. Básicamente lo

**[1:31:19]** que digamos que es como una pequeña infraestructura que se va retroalimentando de sí. Pero es data sintética. O sea, estos ataques. Los ataques en general. ¿Estos? ¿Con los que entrenaron el modelo? No, no entrenamos el modelo. O sea, le pusimos como unos safe bars. Lo que tenemos es una cantidad de código de ataques de CVs que son los más normales y ahí les atacamos. [aplausos] [música]

**[1:32:27]** [música] [música] [música]

**[1:33:05]** [música] [música] [música]

**[1:35:00]** [música] [música] [música] Sí.

**[1:36:28]** [música] [música]

**[1:40:11]** [música] [música]

**[1:41:14]** Más que nada, muchas gracias por apostar

## [1:41:15] VanGUARD | 🛡️ AI Security

**[1:41:17]** por Vanguard en el mercado de hackers y esperar ahora, pero empezando porque hoy en día las startups que nacen en días, horas y semanas, las tres operan con un set de tres tarjetas, GitHub, Supabase y Cloudflare, las cuales todas están desconectadas, todas se mantienen con normativas en inglés y con sus diferentes procedimientos de seguridad. Pero nada más en el año pasado hubieron diferentes fallos en Lovable y Su en Supabase, los cuales dejaron inhabilitados, fallas de seguridad, vendiendo datos de todo tipo de

**[1:41:50]** de todo tipo de startups y programas en estos mismos. Aquí nace Vanguard. Vanguard es del equipo 22. Antes conectabas el Supabase y el repositorio y rezabas en que eso no le iba a pasar más nada nunca. Ahora, con cada push, cada revisión, cada merge y cada interno que está a las 4 de la mañana subiendo código, hay revisiones continuas. Es autónomo. Supabase, GitHub y Cloudflare conectados todos en uno. Adelante. Ahora les vamos a mostrar una pequeña demo, la cual los invito a escanear, ya que aquí van a poder revisar hasta sus propios GitHub personales. Que un adelanto, les hicimos scraping a todos y

**[1:42:23]** hay muchos proyectos con muchas fallas individualmente de sus proyectos públicos. Okay. Ajá, pon. Empezando por la demo, que cuando ustedes entran, van a ver a Vigía. Vigía es nuestra asistente, la cual los va a guiar por Vanguard, como también les puede explicar paso a paso cada detalle que consigue Vanguard. Cuando conectan el WhatsApp, llega el mensaje de cada notificación de un push, merge o revisión sospechosa, lo cual que genera una llamada en la cual podemos

**[1:42:57]** resolver en el momento a las 4 de la mañana lo que el interno subió y lo que nosotros no nos hemos cuenta en ese push que está haciendo Cloud de un workflow de 3 horas. Ahora, a las 4 de la mañana si tienen una revisión. Y lo más importante, todo conectado bien CP y con sus propias skills. No van a tener ni que aprender a utilizar Vanguard, ya que está conectado con Cloud y con Codex, que es la primera herramienta que puede permitirte de manera interna, porque solo maneja lectura, revisar todo sin cometer fallos, sin romper el código y sin romper base de

**[1:43:30]** datos, eliminando datos de usuarios reales. Aquí ya sí pueden registrarse y los invitamos a que revisen sus propios proyectos, ya que de verdad sí hay fallas peligrosas y archivos de claves API. Muchas gracias. [aplausos] Hola. Bueno, la la primera pregunta que es la misma que le hice al grupo anterior con un producto similar es como ¿Cuál es la diferencia entre esto versus como o el o

**[1:44:03]** el elemento diferenciador de esto versus la skill de review de Codex, por ejemplo, de una PR o algo así? Bien. Em Principalmente, además de que con Vanguard puedes identificar si hay algún problema o existe alguna vulnerabilidad a la hora de que alguien haga un pull request hacia el la rama merge main, que normalmente es la de producción, no solamente eh vemos el problema, sino que puedes interactuar y y el se toma acción directamente, por ejemplo, eh apenas se detecta que hay una una un posible fallo eh o que hay algo que está mal, que no

**[1:44:37]** debería unirse o llevarse al me al main, alguna credencial expuesta, eh puede ser alguna dependencia que está desactualizada, el si tú tienes tu sistema conectado con Vanguard, el se corta directamente el pull request, o sea, no solamente identificativo, sino que también es eh toma acción ante los problemas. Eh de hecho, desde el panel puedes ver revisar todas las verticales, están la vertical de Supabase, que sería el backend as a service, este, también tenemos la de Cloudflare, revisar cómo está la salud de de todos tus servicios, tené implementamos también el wiki del

**[1:45:09]** repo, donde eh directamente al conectar tu GitHub, el sistema es capaz de analizar todo tu repositorio, darte una explicación de sobre qué trata, eh arriba hay un diagrama de de de flujo que explica más o menos cuál es el flujo del del proyecto. Eh y bueno, lo importante de de de Vanguard es que precisamente todo lo que tú identificas dentro de la aplicación puedes generar un prompt de IA, ¿okay? Para pasárselo a tu propia IA e incluso tenemos un MSP y nos conectamos con un MSP a cualquier inteligencia artificial. Entonces, ella solamente lee lo que se

**[1:45:43]** reporta en Vanguard y lo trabaja ella por su lado. ¿Y por qué decidieron hacer una plataforma para esto versus, por ejemplo, no sé, una GitHub Action que corriera Code Review? Como que tiene como la como análisis de pull request y como proponer cambio. Precisamente con la idea de que hay muchos programadores ahorita en esta nueva revolución de la IA que no son lo suficientemente técnicos. Entonces, de repente a la hora de montar un GitHub Action se le puede complicar y por lo tanto queríamos montarlo como una interfaz visual, de tal manera de que si ellos quieren simplemente conectarse por vía MSP, ellos prontean a su IA de

**[1:46:16]** preferencia y simplemente la IA toma las decisiones, maneja con su cerebro, con todo su, de repente si tienen un Obsidian o un prompt generado de su proyecto, ya sabe la IA qué decisión tomar y así le facilita mucho más el flujo de trabajo y reduce su fricción. Además también puedes conectar más de un repo. Gracias. [aplausos] Adelante Zero ID y se prepara Cflow Team.

**[1:47:12]** [música] [música] [música] [música] [música]

**[1:48:01]** [música] [música] [música]

**[1:49:19]** Sí.

## [1:49:23] ZeroID | 🤝 Trust

**[1:49:23]** Pero antes quisiéramos que levanten la mano si saben la cantidad de empresas que que cuentan con sus datos personales. Muy bien. Exacto. Entonces, ¿qué sucede? La mayoría de los sitios web que ingresamos hoy en día estamos constantemente entregándole nuestros datos, pero lo hacemos a ciegas. Eh según una encuesta el 73% siente poco o ningún control sobre lo que hacen con sus datos y el 61% cree que las

**[1:49:57]** políticas de privacidad no explican bien cómo se usan sus datos. Por ello nuestra propuesta una plataforma de identidad digital que te ayuda a que el usuario indique qué datos desea dar a quiénes se los está entregando y de manera transparente cómo se manejan estos datos. Ahora bien, esta propuesta se sustenta en tres pilares: control, trazabilidad y confianza. Sabemos hoy en día que nadie lee las políticas de privacidad las al darle

**[1:50:31]** aceptar. Por eso queremos un poco más de transparencia y cerrar un poco esa brecha entre las políticas de privacidad y lo que en realidad nos están diciendo con todo ese texto larguísimo. Por eso una de las principales funcionalidades de Zero ID de Zero ID es que nosotros entendamos como usuarios qué es lo que estamos entregando como tal y qué nos están exigiendo. Además tenemos un trust score basado en métricas de todos los estándares de manejo de data a nivel de países.

**[1:51:07]** Perfecto. Bueno, para aquellas personas que no pudieron responder que ellas son las que están conscientes de todas las personas que o todas las empresas que tienen su data personal, esta es la solución. Tenemos Cifrado ID. Básicamente Cifrado ID nos permite registrarnos de una forma sencilla, ¿cómo? Mediante nuestro pasaporte. Ustedes pensarán que puede ser un poco personal, pero es mejor tener toda la información en una empresa que sí tenga eh registros o la información de forma cifrada

**[1:51:41]** a tenerla en muchos empresas que puedan tenerlo, pero de forma eh cruda. Nosotros cargamos la información con nuestro pasaporte, luego Cifrado ID utilizando OCR toma los datos, las personas, en este caso los usuarios pueden rellenar qué datos les interesa llenar extra y luego podemos poder podemos con podemos iniciar sesión con diferentes eh empresas que decidan trabajar con nosotros mediante un SDK. En este caso podemos hacer la

**[1:52:15]** demostración utilizando esta página que creamos que se llama Expreso Caribe. En este caso podemos darle continuar con Cifrado ID, nos hace el envío de la petición y en este caso nos llegará al teléfono. Acá podemos colocar nuestro usuario. Tiempo. madre. [aplausos] Eh yo tengo una pregunta que es que ¿cuál es la propuesta de valor para

**[1:52:50]** los negocios como tal eh para que a ellos les incentive utilizar su plataforma? Porque nosotros entendemos hoy en día lo todo el problema de del data sharing, porque somos ingenieros, o sea, coders, pero a mi mamá eso no le importa ni está remotamente lejana a que le vaya a importar eso, pues. Entonces, eh, entiendo la pregunta, muy buena, gracias. Y creo que ahí sería un tema de más de concientización. Los data breaches que hemos experimentado a lo largo de todo este tiempo han causado catástrofes a nivel muy grave de identidad y de y de

**[1:53:27]** privacidad. Entonces, lo que queremos es entender que el 100% de Zero Knowledge es imposible a día de hoy porque tenemos que las empresas lo necesitan. Pero sí podemos concientizar al usuario de cómo esta plataforma va a usar tus datos y cuál es el el trust score de la misma para con tus datos. Qué cosas te está pidiendo que son normales dentro de un tipo de plataforma de este estilo y de su edad, si es una startup, si Uber te está pidiendo cosas que no necesita en realidad, hay que dudar un poquito de eso. En este caso, Uber le hicimos el análisis y está completamente okay, pero

**[1:54:01]** hay muchas otras plataformas que también consideramos el hecho de que tienen que pedir legalmente, según su país, ciertas cosas, eso no les quita trust score. ¿Cuál es el incentivo de las plataformas? Tener más tasa de eh transparencia para con el usuario. Y eso generar más confianza a través de nuestro login. ¿Qué safeguards tienen ustedes con el tratamiento de la data para que el usuario se sienta cómodo de sí darle

**[1:54:34]** estos datos además tan sensibles a ustedes? Bueno, principalmente porque nos basamos en el cifrado, que utilizamos una una estructura que se llama eh Tree Merkle. Básicamente, con esto nos encargamos de asegurar que la información que el usuario nos da, primero, sea cifrada, no esté guardada de forma cruda en nuestra base de datos. Segundo, para nosotros compartirla con los los con las demás empresas, el usuario debe darnos su aprobación. Eh, les comentamos el el apartado de

**[1:55:08]** el score para que el usuario tenga un conocimiento, mira, te están pidiendo estos datos, esta empresa tiene este este puntaje, pero tú vas a tener la respuesta final de si decides darlos o no. Tiempo. Gracias. [aplausos] Cflow, pase adelante. Team 18 y se prepara Tridi, Team 26. [música]

**[1:56:02]** [música] [música] [música] [música] [música]

**[1:57:01]** Sí. Repito la pregunta. ¿Cuántos de ustedes a día de hoy siguen Otra vez.

**[1:57:36]** Tercera pregunta.

## [1:57:37] Céflow | 🧊 Three-Dimensional

**[1:57:37]** [risas] Eh, ¿cuántos de ustedes escriben el 80% de su código? Okay, veo que ninguno. ¿Qué les parece si les digo que hay una profesión en donde uno de sus procesos fundamentales, como es la digi, eh, perdón, la planificación digital, eh, todavía hace el 80% de su trabajo manual? Esta es la odontología. El 80% de su trabajo es manual. Se tarda de dos a cuatro días por trabajo, eh, por planificación. Y en el caso de querer delegarlo por falta de tiempo, necesitan hasta 300 dólares por planificación. Por eso creamos Safe Flow. Básicamente, Safe Flow disminuye un 75%

**[1:58:10]** de tiempo y ahorra hasta 30 horas al mes en la creación de planificaciones digitales para tus pacientes odontológicos. Pero primero, antes de pasar con el demo, queremos explicarles qué es la planificación dental. Básicamente, es una representación detallada de tus dientes en una que tiene precisión milimétrica y te permite evaluar cuáles son las mediciones tanto de tus dientes como de tus encías, de tu estructura ósea, etcétera, para poder hacer una buena planificación sobre tu tratamiento. Ahora sí, vamos al demo. Uy, sorry. Aquí estamos visualizando

**[1:58:43]** un modelo que está constituido a partir de la re, ah, sorry. Está constituido a partir de la, el modelaje 3D de unas placas tomográficas. básicamente lo que hacemos es que tomamos los diferentes cortes y reconstruimos un modelo 3D para poder visualizar la estructura ósea de todo el cráneo del paciente. Y como pueden ver también tenemos eh toda la gráfica de lo que es el diente y las encías del paciente, que básicamente lo tomamos de un escaneo intraoral, que son herramientas y escáneres que hacen los odontólogos de forma tradicional. No estamos inventando o agregando un

**[1:59:16]** proceso nuevo en su en su planificación, sino que ya estamos reutilizando cosas que ya hacen. Como pueden ver, este paciente justo le hace falta 200, uno en la parte superior y una parte de ahí en la parte inferior. Si nos vamos, por ejemplo, a esta visualización, que es de la parte superior, podemos ver cómo aquí se detalla mucho más el diente y podemos ver el mapa de calor de lo que es la eh ¿Cómo se llama? La punta de contacto, sorry, de eh cómo hace contacto con otros dientes. Para los que no sepan, es muy importante que un diente haga con- contacto con su antagónico, es decir, que se mantenga

**[1:59:48]** principalmente siempre eh en contacto en la boca cerrada. Ahora vámonos a el resultado de nuestra planificación. Básicamente, a partir de inteligencia artificial, nosotros podemos analizar los planos de toda la boca, incluyendo la tomografía y también la parte de eh la estructura ósea y la distancia que hay de forma precisa entre los diferentes dientes para poder generar implantes basados eh 100% en inteligencia artificial. Es un proceso, un workflow completamente lineal, en donde el la misma inteligencia artificial se encarga de analizar el paciente, ofrecer la

**[2:00:21]** solución y de una vez generar el mismo implante. Aquí podemos ver cómo ya se presenta eh los diferentes implantes, aquí hay uno el superior, el inferior, y podemos ver cómo está el implante en este lugar. [aplausos] Eh mira, uno, yo creo que uno de los desafíos más importantes en la intersección de la IA y la medicina es toda la validación de la data. Eh, yo leo muchísimo del tema y

**[2:00:54]** cuando ves que publican modelos que si en las revistas más importantes de investigación eh, la validación que viene por detrás, o sea, toda la data que sirve para precisamente la validación son millones de millones de de de entradas que sirven para validar esa data y en pacientes reales, nunca en pacientes sintéticos. Entonces, o sea, que si yo fuese odontólogo, qué seguridad me da a mí que el modelo me está proponiendo algo basado en una data que fue validada por millones de pacientes y no por la nube tan intangible de cloud, pues.

**[2:01:28]** Eh, sí, justo este paciente es un modelo real, eh, de hecho, mi compañero por acá es odontólogo, creo que es el primer odontólogo que viene a un hackathon. Pero básicamente, eh, nos dio un resultado que en la ubicación del implante solo de un margen de error del 0.02 mm respecto al resultado que ya operaron y fue, eh, digamos como que evaluado y validado, ¿no? Eh, justamente nosotros visualizamos esto más en una etapa como de una especie de autocomplete de cursor para odontólogos en donde te acelera el trabajo, no te da el resultado final de una vez, sino Ajá, y, o sea, si tú eres odontólogo, tú

**[2:02:03]** debes de saber que ya eh aplicaciones y y programas como estos existen porque yo también los he visto. ¿Qué de distinto tiene esto que ustedes están proponiendo con lo que ya existe? Eh, bueno, muy buena pregunta. Principalmente nació la idea fue porque estos programas, aunque digamos que son netamente a que aunque sean digitales son con procesos muy específicos, es decir, yo me puedo tardar haciendo esta misma planificación aproximadamente dos semanas y este es tardío para el paciente, es tardío para mí y puede presentar muchos problemas.

**[2:02:36]** Yo quería verificar con un paciente que ya operé, que ya se le colocó los implantes, qué tanto era la tasa de digamos de objetividad o que o que de la correcta colocación del implante podía ser. Eh fue donde detectamos que era un 0.2 mm, que es prácticamente nada a comparación a un promedio IA que o una información de la IA de la colocación de los implantes. [aplausos] [música]

**[2:03:39]** [música] [música] [música] [música] [música]

**[2:04:28]** [música] [música] [música] Y quiero que eh tomemos el ejercicio de

## [2:04:54] Tridi | 🧊 Three-Dimensional

**[2:04:55]** recordar cuál era la discusión de la IA hace un año. Hace un año estábamos pasando o pensando cómo venir del chatbot a la gente. Y hoy los agentes básicamente es un tema resuelto, o sea, ya todo el mundo usa gente, todos los proyectos son agénticos. Y nosotros vinimos acá con un objetivo y una misión que es descubrir qué va a ser lo próximo el próximo año, lo próximo en los próximos 5 años. Y descubrimos que physical AI is the new sexy. Este ahorita el nuevo reto es que una red neuronal mueva un robot, es decir, un hardware físico e interactúe con el

**[2:05:27]** mundo real. ¿Cuál es el gran problema? ChatGPT, como vieron en la presentación creo que el viernes, fue entrenado bajo todo el concepto de internet, con toda la información de internet y todos los libros del mundo. Pero para el mundo del physical AI no existen estos datos. No existe una un gran recorcet de movimientos que puedan ser utilizados. Entonces, por eso hicimos 3D. Nosotros básicamente convertimos videos normales en data simulada bajo un entorno de físicas reales y después vendemos los datos que generamos. Entonces, vamos de una vez al demo. Lo primero que les quiero mostrar es que esto no es un

**[2:06:01]** robot eh o no es un render, no es un video, es literalmente un robot que eh entrenamos acá localmente con 29 verticales o bueno, 29 movilizaciones. Y aquí esto es básicamente lo que hace 3D. Agarramos un video, eh lo traqueamos y lo ponemos en una simulación. Eh aquí un poquito del recorrido que hicimos con 10 millones de parámetros, 40 y 60 millones de parámetros que entrenamos a nuestro modelo. Este es nuestro output que ya lo van a ver y vamos de una vez con la demo o la la Sí. Dejamos acá.

**[2:06:34]** Como ven, al puede estar moviéndose, el robot va a estar interactuando en tiempo real y todos los movimientos que hace el robot es básicamente bajo sus propias capacidades. Entonces, dejamos de grabar y lo metemos directamente en la simulación. ¿Qué pasa en la simulación? Todo lo que captura en el video lo mete en esta simulación y nosotros podemos eh jugar en dónde queremos eh que este robot se desempeñe. Puede ser en un depósito, puede ser en en piedra, puede ser en eh con viento extenso. ¿Por qué? Porque nunca las condiciones son ideales. Podemos hacer que este robot

**[2:07:07]** camine con la data entrenada y podemos empezar a entrenar esto. Nosotros lo entrenamos para que vean que no es fake. Ahorita tenemos una Mac por acá con una red neuronal que está entrenando en base a ciertos videos que le pasamos y está generando ciertos outputs. Todo esto es la red neuronal y el output general de de Tridi es este record set de datos que vendemos en base a todo lo que el modelo aprendió durante todos estos días. Y cuando le das a descargar, te da todos los archivos ONNX que le pasas al hardware y básicamente es hacer que un robot camine y tenga conciencia sobre su

**[2:07:42]** entorno. Gracias. [aplausos] Hola. Hola. Buenas. Eh mi pregunta es si bueno, a cuando están implementando esto, pudieron buscar en internet y ver cómo qué es lo que existe actualmente sobre cómo detectar movimiento y cómo Bueno, una de las cosas que investigamos, que fue muy curioso, fue Actualmente hay una empresa que recolecta datos en la India que prácticamente pone a trabajadoras que usan mucho trabajo manual, o sea, para

**[2:08:15]** como empaquetado o amarrar cosas, con una cámara acá arriba y grabando las manos y todo el movimiento. ¿Qué pasa con eso? Eso actualmente es la es una de las formas para poder tener este tipo de información y poder luego dársela a robots. Sin embargo, es limitada de tener precisamente la mano de obra y estar en el lugar correcto para para poder generar esa información. No Rubén. En compañías como Figure AI, eh, Tesla, etcétera, que están ahorita obviamente

**[2:08:48]** impulsando el tema de los humanoides, el el proceso con los que ellos han entrenado a su a sus robots se parece a esto o digamos ustedes están reinventando la rueda o agarrando algo que ya existe. No necesariamente el proceso en que Tesla está entrenando sus robots es agarrando mucha data de videos físicos y este no necesariamente poniéndolas en simulación. Lo que pasa es que nuestro valor acá es que nosotros podemos usar videos de TikTok y ponerlos en simulaciones específicas para generar datos a escala, no depender de un input de usuarios eh fidedignos, pues.

**[2:09:24]** ¿Con cuántos eh videos entrenaron la red? No entrenamos el la red principal con videos, lo entrenamos directamente o sea, nos mostraron como una red neuronal ahorita. Sí, sí, sí. Pero la red neuronal básicamente lo que hace es poner al robot y que los propios sensores empiecen a actuar. Este nosotros usamos una arquitectura MLP porque toda la red neuronal tiene que ser sumamente rápida en la cuestión de del movimiento de sensores. Entonces, nada, eso. Listo. [aplausos] Muchas gracias.

**[2:10:00]** Que pasa adelante Hawk, team 23 y se prepara Arbi, team 2. [música] [música]

**[2:10:42]** [música] [música] [música]

**[2:11:23]** [música] [música] [música] Sí.

**[2:13:15]** [música] [música] Sí.

**[2:14:44]** [música] [música] [música] [música]

**[2:15:29]** La siguiente evolución de la IA son los

## [2:15:30] HAWK | 🛡️ AI Security

**[2:15:31]** agentes. Estamos viendo como la los agentes han cambiado el mundo y el y el día a día de no solo nuestras vidas como ciudadanos, sino de las empresas. Por ejemplo, el crecimiento que ha tenido empresarialmente las las IA agénticas en el último año ha sido de alrededor del 30% y se estima que de aquí al 2033 será alrededor del 2000% en crecimiento. Esto generará un retorno de la inversión enorme y el alrededor del 83% de las de las de las organizaciones ya planifica tener un una IA agéntica dentro de sus

**[2:16:05]** sistemas. Pero todo viene con un riesgo. Este año hemos visto bastantes hackeos debido a la IA y a gente que se han descontrolado y han infiltrado este en bases de datos o han liberado información que no deberían. Agentes que están entrenados, pero cometieron errores. Vimos el hackeo de Hugging Face, vimos el hackeo hace poco de PHP y se estima que hay 56% más brechas este año que el año pasado, según IBM. Y las operaciones, según CrowdStrike, de las de las adversarias de la IA ha aumentado un 89% solo este año. Uno de los principales problemas

**[2:16:41]** es que la IA utiliza el mismo hardware para protegerse que para controlarse. Como dicen en Apple, este este este tipo de control no es el que deberíamos utilizar. O sea, en el mismo silicón está el software que te está regulando, que te está controlando, y el software que está operando la IA agéntica. En en Apple ya tienen una solución, dentro de un mismo silicón están utilizando distintas procesadores para la IA y para la protección de la IA. Nosotros estamos desarrollando algo parecido, pero para los entusiastas de la IA que quieren desarrollar agentes en su en su dormitorio o en sus empresas o

**[2:17:15]** en sus startups. Pero esto es Hawk. El sistema utiliza un silicio separado, lo que lo que vamos a utilizar es un Raspberry Pi en este caso, un Raspberry Pi 4B, que está conectado en paralelo a la network y eh todo lo que pase, todo lo que está tratando de hacer la gente, todos los los requests que hace, van a pasar a través del Raspberry. Después el Raspberry este eh tiene una una agente completamente local, una IA completamente local que hemos entrenado en eh Granite, una una IA de

**[2:17:49]** de IBM y bueno, por ejemplo, aquí tenemos lo las pruebas de los del que estábamos haciendo ayer. Recibimos un un 98% de retorno en el en el en el mensaje cada vez que de las, de las 100 eh request malas que o maliciosas que mandamos, 98 no las frenó en menos de un milisegundo con la IA que tenemos dentro del dentro del Raspberry Pi. Entonces, ahora les vamos a mostrar, les vamos a mostrar una demo. Okay. Ajá, aquí tenemos, esta es la aplicación

**[2:18:22]** móvil, esta funciona en el, en el, en el teléfono, tiene su hash, tiene su key y este es el, este, este es tu agente dentro de Cloud, en una computadora. Esto funciona con Codex, Cloud y Open, Open Code. En este caso ya podemos ver, por ejemplo, aquí que está diciendo en esta Tiempo. Gracias. Eh Eh, mi pregunta es, ¿qué modelo específicamente están corriendo en la

**[2:18:54]** Raspberry Pi y cómo está categorizando los requests? Es un Run Light, este, cuatro de 800 millones de parámetros. Y y eh, ¿qué tipo de modelo es, es un LLM? Yes. Eh, es un LLM, pero está reentrenado con Lora, fine tuning hecho por nosotros a través de eh procesos de TLDR, que vendría siendo Too Long, Too, Too Large Don't Read. Eh documentación que libera Google o

**[2:19:27]** Anthropic sobre brechas de seguridad, sobre mal prácticas de la IA y la comunidad las compacta y las lleva a pesos para ir a reentrenar eh eh modelos. Nosotros hicimos el entrenamiento durante estas 36 horas y hicimos eh análisis adversariales hasta que logramos tener este modelo que corre en al menos 500 MB de RAM. Y y ¿por qué decidieron usar un LLM versus un modelo como System One, un clasificador, algo como Jeff? Porque en principio eh esto está pensado para que sea un agente autónomo capaz de comunicarse.

**[2:19:59]** Este está en que ahora el poder de cómputo no daba para abastecer todo lo que decíamos para nuestra nuestra versión cero. Sin embargo, la idea de esto es que el agente sea capaz de interactuar con más dispositivos y pueda notificar que es lo que ya hace a través de la aplicación que es que notifica si hay algún tipo de interacción no permitida dentro de las reglas de nuestro de nuestro nuestro agente o nuestro modelo notifica y confirma si el usuario o el en este caso owner permite que estas operaciones sigan

**[2:20:35]** ejecutándose. Ahora lo hacemos a través de una aplicación a futuro podría ser a nivel de de que sea escalable, ¿no? O sea, lo que se quiera. Por eso decidimos usar ese tipo de modelo. Eh, hoy por ejemplo, no sé, Cloud ya tiene su evaluación de permisos que hace un request y te dice como si está seguro o no, y además hace un request a como un servicio aparte que ya hace una inferencia y te lo devuelve como Yes. Ahí hay una hay una de una que lo que pasa es que si bien lo hace muy bien, no tenemos que queja de lo que hace al día de hoy Antropic o Open AI

**[2:21:07]** el detalle está en que es un estándar actual, no la cero confianza y el dividir las las responsabilidades. No es lo mismo que quien está ejecutando sea quien se audita a que un externo audite la ejecución de un tercero. Es por esto que al el lo va a aplicar Apple también lo está aplicando Google, ¿qué hacen? Tienen servidores con los datos en una stack y quien posee las llaves y el acceso para leerlos, editarlos, modificarlos

**[2:21:40]** está en otro servidor. De esta manera, si se ve comprometido una de las dos partes no podrían eh, de manera automática obtener toda la información o romperlo. Ese es el modelo que nosotros aplicamos un agente que se infiltre dentro de la computadora no va a ser capaz de detener al Raspberry Pi que está en un software aparte con un canal cifrado ma traqueando la información. [aplausos] [música]

**[2:22:39]** [música] [música] [música] [música] [música] [música]

**[2:23:24]** [música] [música] [música]

## [2:25:06] Arvi | 🧊 Three-Dimensional

**[2:25:06]** Hola, buenas tardes. Nosotros somos Arvi. Eh, bueno, nosotros venimos de Puerto Cabello, una ciudad muy turística, igualmente toda Venezuela en general creo que muy turística a nivel de historia. Entonces, se ve en cada esquina un evento, un lugar que fue eh protagonista de un evento histórico, pero los turistas muy a menudo no saben lo que están viendo o en qué lugar se encuentran realmente a nivel de historia o a nivel de turismo, en caso de que no sea de historia. Para eso traemos a Arvi. Que es un eh utilizamos inteligencia artificial y realidad aumentada para tener un guía turístico o

**[2:25:39]** en cualquier otra área, por ejemplo, la educación, por ejemplo, el marketing Y en otras áreas que podamos idear Es un agente o un asistente, un ayudante de realidad aumentada Entonces, bueno, lo dejamos de una vez con el demo Para que el mismo realidad aumentada presente el producto Acá vemos un mapa que es como una persona que está en la ciudad, por ejemplo, y encuentra lugares turísticos donde puede hacer la simulación Entonces, inicia la simulación, en este caso creamos un lugar que se llama Cubo negro

**[2:26:12]** Apuntamos, detectamos el piso Y acá tenemos un Simón Bolívar Que hicimos Y puedo decir que venga hacia mí O puedo mandarlo Puedo mandarlo hacia allá, hacia la tarima, por ejemplo Con Juan Y le puedo hacer preguntas, ya que estoy Acá mismo con el micrófono Eh Le puedo preguntar, por ejemplo, acerca de la eh cuéntame acerca de la pérdida del castillo de San Felipe

**[2:26:52]** ¿Dónde se reproduce el audio? Ah Por la presentación, ya se ve el mapa Acá creo Defenderé este castillo hasta el último aliento Tu plaza ha caído, coronel El rey retoma lo suyo He perdido una batalla, pero Pásame

**[2:27:24]** El celular [risas] Pero también también hay otro tipo de de funcionalidades interesantes, por Por también tiene detección de objetos. Eh, esto es muy útil. Y le puedo decir, ¿qué es esto? Ah, un cuaderno. De tantas cartas en campaña que mis secretarios apenas daban abasto.

**[2:27:58]** Quizás algún día alguien escriba en uno como este lo que hoy vivimos. Entonces, tiene así más funcionalidades. Hay otro tipo de Y bueno, eso es eso es eso es Arvi. [aplausos] Eh, bueno, superchévere la presentación.

**[2:28:39]** Mi pregunta va orientada hacia eh ¿quién es el usuario persona para este este producto? Yo siento que hoy en día hay cosas demasiado humanas y, por ejemplo, toda la parte del turismo uno quiere estar presente y vivirlo, quizás no verlo tanto por por por una computadora o por una pantalla. Sí, bueno, nosotros somos de Puerto Cabello. Puerto Cabello es una ciudad superhistórica, muy turística. Hay muchos lugares, justamente se nos ocurrió por esto. Pensamos en un ejemplo como el Fortín Solano, que es un

**[2:29:10]** castillo que está en la punta de un cerro y que desde ahí puedes ver los cañones disparando hacia los barcos que que que atacaban el puerto, los barcos neerlandeses, o de repente ver la toma de Puerto Cabello en el malecón. Todo ese tipo de de de situaciones que puedas simular y disfrutar del turismo, pues. Eh, es básicamente para para los turistas en en ciudades o o en lugares donde donde se mueve mucho este, este rubro. Por ahora, el contenido que tiene está un poco mock, no sé, está Bolívar, ciertas cosas, pero no es que puedo

**[2:29:42]** pedirle cualquier cantidad de información de historia, ¿no? Sí, eh, hay que preparar los modelos, realmente hay que preparar los modelos dependiendo del tipo de, de lugar. Sin embargo, nosotros durante el, la, las 36 horas desarrollamos con un pipeline que nos permite desarrollar nosotros también estos modelos mucho más rápido, estas animaciones más rápido. Pasa por primero con generación de imágenes de Yemini de, de los personajes, luego con Meshia y creamos los modelos, le creamos la textura, los riguiamos y ahí mismo descargamos algunas animaciones y con script de Blender, usando la CLI de Blender con Python, también podemos de forma rápida crear algunas animaciones

**[2:30:15]** simples y o incluso a, aligerar también los modelos, hacer alguna algunas mejoras, por ejemplo, en el caso de Simón Bolívar, le pudimos dibujar la boca o había una batalla de, de unos soldados que no nos, no nos alcanzan a demostrar, esa la animamos incluso con Blender, con script de Python y con la CLI de, de Blender. Si ahorita le hacía una pregunta abierta, como por ejemplo, ¿qué opinas del metro de Caracas? Cuéntame la historia del metro de Caracas, ¿lo hubiese respondido? Sí, puede ser que lo podamos probar ahorita. Sí, hay chance. Ah, bueno, después lo podemos probar. Gracias.

**[2:30:49]** [aplausos] Lo siento. Gracias. Quiero ser justa con todos los grupos. [música]

**[2:31:26]** [música] [música] [música]

## [2:31:52] Quórum | 🤝 Trust

**[2:31:52]** Eh, ¿sabían que generar una votación para 21 millones de personas en la región cuesta alrededor de 25 a 170 millones de dólares? Parece costoso, ¿verdad? Pero creo que creo que es aún más costoso es tener un resultado que no se que no se respete ni votos que se puedan verificar. Por eso creamos Quorum. Quorum es una infraestructura de decisiones colectivas donde ya no ya ya disculpe, ya no necesitas eh creerle a quien cuenta los votos, sino tú mismo lo verificas.

**[2:32:24]** En Quorum cuando en Quorum eh necesito que que los hackers nos ayuden con esta votación con su credencial básicamente vamos a conectarnos hacia Pátunus y nos va a decir qué credencial realmente pertenece a un hacker o no y vamos a elegir al presidente de este evento. ¿Okay? Cuando nosotros realizamos eh la verificación facial para cubrir a a los votantes básicamente eh hay un modelo de IA que corre independientemente en cada dispositivo y el rostro, no se

**[2:32:57]** preocupen, nosotros no lo tenemos, solo tenemos un hash cifrado de sus datos biométricos que viajan en el momento en que la votación está abierta para verificar que no haya un rostro que quiera hacer duplicidad y por lo tanto abusar del del método. Al finalizar la votación eh estos datos cifrados van a son eliminados. Cuando un votante escoge a su candidato se genera un voto y estos votos se encadenan eh con el el el último voto anterior, es decir, si alguien intenta, no solamente

**[2:33:31]** burlar la verificación de identidad o la credencial de un hacker, sino que además intenta burlar eh eh la cantidad de votos que que que hay en la votación no lo va a lograr porque la cadena lo va a rechazar porque tiene que estar eh de alguna manera interconectado entre entre ellos mismos. Entonces, bueno, nada. Básicamente esos quórum, vamos a dar unos segundos más para para para la votación que tenemos tiempo y em podemos decir, vamos a ver, bueno, ahí van ahí van los votantes, esto quiere

**[2:34:04]** decir que cada uno de estos votantes que ingresaron con su credencial hicieron una prueba de conocimiento cero y y gracias a eso pudieron votar. Entonces, ahora sí, podemos decir que bajo bajo una votación libre, nuestros nuestros presidentes serán Ignacio y Rafael. Muchas gracias. Bueno, eh una de las cosas para

**[2:34:37]** aprovechar los 13 segundos que nos quedan es que eh cada una de las personas en su dispositivo acaban de de estar interconectados en una red para la votación y ahora mismo su dispositivo puede descargar todo el JSON completo para verificar que estar que que efectivamente estos fueron los votos reales y la participa la participación completa de de la votación. Gracias. ¿Qué impide que se pudieran enviar

**[2:35:12]** caras em fabricadas, digamos, incluso con IA eh para tratar de crear resultados eh no reales. Sí, bueno, em en primer lugar, antes de obtener una verificación facial, nosotros usamos a la misma base de datos de Pátanos de los hackers en Venezuela como nuestro sistema de identificación nacional para la votación. En primer lugar, sin sin ni siquiera tienes la credencial, no puedes llegar a esa a esa a esa parte. Y y eh la la parte de la verificación facial

**[2:35:46]** eh básicamente genera una huella eh biométrica que la compara con con con los datos que tenemos de los inscritos. Y eh como les dije antes en la presentación, esta huella biométrica solo vive en el momento de la votación y justo cuando la la votación cierra, eh la huella biométrica se elimina para proteger a todos los involucrados dentro del de de la votación. Em su solución [carraspeo] versus como otros sistemas de voto online también

**[2:36:18]** como descentralizado y cosas así, como qué es lo que trae o la diferencia. Eh nosotros creímos eh quisimos crear una una estructura una una estructura para decisión colectiva. Eh no lo mostramos, pero bueno, mi amigo César, él es presidente de la conjunta de condominio de su edificio y siempre se siempre se tiene en en dentro de un colectivo es muy difícil tomar una decisión. Entonces, nosotros eh queríamos ampliar el producto a a través de de la descentralización, eh crear contratos inteligentes donde

**[2:36:52]** César incluso podría introducir todo este presupuesto y en cuanto a los resultados de las votaciones, el presupuesto se podría dividir. Y bueno, creo que eso sería una diferencia. Yo quisiera añadir a la respuesta que lo más difícil del blockchain eh no no es desarrollar blockchain y más bien es realmente la adaptación. Entonces, creemos que nosotros, eh, el valor de nuestra propuesta de, de este, de esta infraestructura de toma de decisiones colectivas frente a

**[2:37:25]** otros, es que es muy rápido. En menos de 3 minutos podemos, pudimos decir quién, quién fue el presidente y cada uno de ellos, que fueron los que votaron, más o menos como 20 votos vi, eh, se pudieron dar cuenta que hicieron una certificación con su credencial y una verificación se entiende tía, en menos de 10 segundos. [aplausos] Muchísimas gracias. [música]

**[2:38:18]** [música] [música] [música] Eh, muchachos, si pueden ir escaneando

**[2:38:56]** este código, lo vamos a usar más adelante. Gracias.

## [2:39:03] Presente | 🚨 Emergencies

**[2:39:04]** ¿Por qué esperar a que ocurra una emergencia? De los más de 400.000 adultos mayores que se encuentran en este país solos, eh todos ellos pertenecen a ser los padres de los más de 8 millones de venezolanos que tenemos afuera. 8 millones de venezolanos que están preocupados por sus padres acá, que tienen que estar pendientes escribiéndoles todo el tiempo y de los cuales es muy difícil mantener una comunicación constante. Una prueba de esto es un caso que quizás muchos conozcan, que es el de

**[2:39:36]** Silvia y Rafael Sandoval, que en el 2020 lamentablemente fallecieron y encontraron sus cuerpos dos días después. Por casos como este que eh ocurren muy constantemente y no hay data de de los mismos, les traemos presente. Es una aplicación que convierte cualquier teléfono Android en una especie de reloj de mesa. Es un reloj de mesa inteligente interactivo para personas vulnerables en en este caso lo lo especificamos en personas mayores,

**[2:40:09]** pero puede ser cualquier persona vulnerable que viva sola y que necesite algún cuidado. Eh [carraspeo] es una pantalla interactiva donde tiene quizás un monitoreo de consumo de medicamentos, manda alertas y muy importante, eh está siempre un always on escuchando eh palabras clave para activar una alerta. Palabras clave como emergencia, alerta, ayuda, entre otras palabras. Entonces, al mencionar alguna de las palabras, él siempre está escuchando y se activa.

**[2:40:46]** Si Carmen no le responde, él procede a llamar a su hijo. Supongamos que el hijo recibe la llamada, pero el hijo no responde. Vuelve a intentar hacer la llamada a otra persona, a otro vecino de confianza. En el caso esa persona no contesta, vamos a la instancia mayor. Vamos a emergencias, ¿sí? Pero emergencias necesita un contexto. Entonces, si en el dado caso que esta

**[2:41:20]** persona cae enfrente de la cámara, mira, tenemos una IA que eh nos da un contexto de imagen que eh le va a ser útil a a emergencias. Esperamos que eh emergencias conteste. Y eh como la persona posiblemente esté caída, ya tenemos el contexto, eh ya tenemos eh tenemos además una foto que

**[2:41:53]** le puede ser útil más adelante. Además, tenemos la pantalla que va a tener el familiar, que la deben tener ustedes, eh en caso que se su que escanearon el código QR, y además tenemos un OCR para eh escanear récipes y informes médicos y poder tener eso en un en una base de datos y que el papá sepa cuando no le queda eh medicamentos el el hijo, perdón. Gracias. [aplausos]

**[2:42:32]** Em si Carmen le pasa esto y luego no aparece, sabes, ponte que está lejos del celular, no tiene cómo hablarle a la a la persona, a su hijo o a emergencias, ¿hay alguna eh una información que de forma automática le le le transmiten a al al a la persona que está del otro lado del teléfono? Sí, pudiera transmitirle pudiera transmitirle que la mamá no respondió y que no está en la foto. no lo hace. Por ahora no. Adicionalmente también

**[2:43:04]** quienes escanearon el código al inicio Se darán cuenta que les debió haber llegado una notificación durante la presentación. Porque lo que hace es que el sistema envía una alerta mediante Telegram. Enviando la foto Y la alarma de lo que está ocurriendo. Me gustó fue la presentación. Yo tenía una pregunta que es que Eh Para como que hacerlo salir del de de la caja por decirlo de una manera si no lo hubiesen hecho en un teléfono en que lo

**[2:43:37]** hubiesen hecho y por qué. Creo que lo escogimos específicamente en un teléfono Porque es una forma barata y accesible de tener esto. Esto es una simple aplicación que descargas en un teléfono Android incluso de generaciones antiguas funciona. Entonces es abaratar costos. Dando uso a algo que a un producto que todos tenemos en casa y no lo estamos usando. Ese Android viejo que está en la gaveta. Sí pero si no lo hubiesen hecho en un teléfono en que lo hubiesen hecho y por qué. Creo que se puede implementar en algún

**[2:44:09]** dispositivo en algún desarrollar si en algún Raspberry algo algún agente específico en un hardware diseñado por nosotros. Pero creemos que este es como el foco y el factor diferenciador de nosotros a diferencia de un Alexa o cualquier agente de estos. Incluso hablando de dispositivos pudiera ser una SP32 que hasta cierto punto de capacidad incluido algunos módulos pudiera seguir detectando lo que viene siendo el sonido. Que es la razón principal. Gracias.

**[2:44:46]** [aplausos] [música]

**[2:45:28]** [música] [música] [música] [música]

**[2:46:13]** [música] [música] [música]

## [2:46:46] Veridian | 🛡️ AI Security

**[2:46:47]** Bueno, primero que nada, buenas tardes. Este Hoy le venimos a presentar Veridian. ¿Por qué Veridian? Veridian, este Lo que intenta hacer es que hoy en día no hay sistemas que conozcan quién es realmente quién entra a tu cuenta. Eh, después de que lograste entrar No se vuelve a comprobar quién eres. Si fuiste tú o fue otra persona. Entonces, con contraseñas filtradas, con códigos 2FA robados, con sesiones robadas

**[2:47:20]** Cualquiera puede entrar Y nunca sabemos si realmente fuiste tú. Veridian Sí conoce la forma de hacerlo. Clasifica, este El comportamiento de usuario y las rutas, este eh, que pueden ser más afectadas Y según Eso, la IA toma decisiones sobre, este, si realmente fuiste tú En base a tu comportamiento y logra Permitirte el acceso o bloquearte. Lo más interesante es que se integra en tu back-end con tres líneas de código.

**[2:47:54]** Eh En la primera corrida logra clasificar automáticamente, eh, todas las rutas según el tipo de vulnerabilidad. Y bueno, ahora, este, vamos a darle a la mejor parte, vamos a dejarlo en vivo. Usar Veridian muy fácil. Eh, entras a la landing Y puedes entrar con tu cuenta de Google. Aquí Eh, ya tengo mi panel iniciado. Y, eh, conozcamos a Ana. Ana es una contadora Que que suele acceder A sus facturas a

**[2:48:28]** través de su programa de contabilidad Y suele hacer movimientos normales Como, eh, ver las facturas Eh, puede retroceder, puede volver a ver las facturas Algo que, unos movimientos que haría de manera natural. Ahora, ¿qué pasa si tenemos eh, una persona en otro dispositivo, eh, otra IP, eh, que hace movimientos más agresivos, que que no permitan eh, que que tengan como algún algún tipo

**[2:49:01]** de spam diferente, eso nos va a aparecer en nuestro dashboard de Veridian y aquí podemos ver la hora en que se le bloqueó ese ese acceso, por qué se le bloqueó y podemos ver todo el historial de actividad que que tuvo junto a todos sus usuarios, junto con las rutas críticas que que ha tenido esa al momento de hacer el el primer scan, como las próximas actividades. Gracias.

**[2:49:41]** Em, bueno, tengo dos preguntas. Uno, si midieron tasa de de falsos positivos, creo que esto se presta mucho a a que hayan alertas cuando realmente no lo no lo hay. Si quiere, responda eso primero. Eh, sí. En las pruebas que que hicimos con agentes y también manuales, había aproximadamente un 3% de de falsos positivos. Esto también hay que someterlo a pruebas externas, debido a que somos nosotros mismos los que estamos auditando el funcionamiento.

**[2:50:13]** Pero también el funcionamiento de Veridian eh, consta en que existe un clasificador antes del agente. El clasificador eh, lo que lanza son alertas, pero no te bloquea directamente. Cuando un usuario obtiene una alerta, el el agente evalúa esa alerta y según tus patrones de comportamiento, por ejemplo, patrones de navegación, patrones de de tiempo que pasas en pantalla, eh, o que tardas en darle a botones, él puede, eh, bloquearte o no. Y el punto es que si te bloquea, él te

**[2:50:45]** da, te envía un correo al que tienes registrado en tu cuenta y por allí puedes desbloquear en caso de que seas tú. Y esto, eh, depende también del tipo de ruta al que estás ingresando. Eh, ¿cómo funciona el clasificador? El clasificador, sobre todo, eh, toma tu IP, eh, datos sobre tu dispositivo, eh, horarios donde tú sueles conectarte y por allí lanza alertas y la ruta, sobre todo. Eh, si es una ruta crítica, por ejemplo, eh, que tú estés cambiando

**[2:51:18]** datos de una cuenta de pagos, es una ruta que que mira, sobre todo. Por ejemplo, si tú estás entrando a un barra home, no te, no, no es lo mismo que tú estés entrando a la otra ruta. Y eh, mi pregunta es como, ¿es un chequeo determinista de regla o es un modelo de aprendizaje? Sí, pero es una combinación. Es una combinación. Tiene tanto una parte determinista como una parte donde sí entra el, como el juzgado de, de la gente. Exacto. Y [aplausos] Muchas gracias.

**[2:51:55]** Que pase adelante Sisa. Team One. [música] [música] [música]

**[2:52:34]** [música] [música] [música]

**[2:53:14]** [música] [música] [música]

## [2:53:34] sIsA: Sistema de Identificación Seguro y Anónimo | 🤝 Trust

**[2:53:35]** ¿A cuántos de ustedes les preocupa cómo se gestiona su información en internet? ¿Cuántos de ustedes saben cómo se gestiona esa información una vez que está en internet? Según IBM, una de cada tres personas en Latinoamérica tiene esta misma preocupación. Y particularmente en Venezuela, alrededor del 89% de las personas desconfían en las demás personas de su entorno y a su vez el 67% de las personas desconfían en las instituciones que gestionan sus datos. Cédulas, eh carnet estudiantil, licencia de conducir, todo eso. Tantos documentos que al final lo único que tienen es la misma información.

**[2:54:08]** Tienen el nombre, tienen la cédula, tienen el tipo de sangre, tienen si está soltero, no está soltero. Y al final, ¿para qué tenemos tanta información si lo que necesitamos es una misma cédula? ¿Por qué necesitamos tantos documentos si podemos tener una sola credencial? Nosotros, en Tajatech, tenemos SISA, el sistema de identificación seguro y anónimo. ¿Y cómo funciona ese sistema? Bueno, sencillo, tienes uh esta identificación que tiene tus datos, esto se le vende al gobierno. Ellos emiten la nueva credencial, la nueva cédula, cédula 7.0 si se quiere. Desde WhatsApp.

**[2:54:44]** Tenemos okay. Un momento, problemas técnicos de la validación de datos. Tenemos un bot con Capso, el cual nos manda la verificación de la información que queremos compartir particularmente y eso nos garantiza las cinco garantías de seguridad. Tenemos la integridad, la autenticidad, confidencialidad, disponibilidad y no repudio. Por ejemplo. Fuimos al bar el otro día, él tenía cara de chamito, entonces nos preguntan, mira cuál eh él es mayor de edad, ¿quieres compartir este dato? Pasa el hash y

**[2:55:18]** bueno, así mismo con la licencia de conducir, con cualquier data que se necesite. En un hospital tiene mayores privilegios. Se les concede. Así no tengo que estar compartiendo data que al final de cuentas, por ejemplo, a la discoteca no le interesa si yo tengo si tipo de sangre O positivo, simplemente le interesa saber si yo soy mayor de edad. Y bueno, como podemos ver allí, él valida, tenemos también este hop en local que se puede instalar y él te da la la confirmación por acá. Para finalizar, los invitamos a que a

**[2:55:50]** partir de este momento tomen el control de sus datos y que nunca más vaya alguien más a tener el control de lo que ustedes compartan. Muchas gracias. Y disculpen. Eh ya que sobró un poco de tiempo, también tenemos un manejo de los datos encriptados. Eh y tenemos un portal donde la persona puede revisar su cédula, eh datos sobre ellos y el historial donde fue eh donde se intentó usar la identificación. Así sea del lado positivo o negativo, tú

**[2:56:24]** dices si la aprobaste o la o la cancelaste en ese momento. Y lo más importante de esto es que tú das acceso solo a los datos que quieres dar. Vale, eh gracias por la presentación. Este, entiendo la finalidad del producto, pero al fin al mismo tiempo, por ejemplo, ese un bar eh puede validar la la edad de la persona que quiere entrar al al local eh gratis con la cédula, okay, hay mucha más información

**[2:56:57]** ahí, pero el bar no se queda con nada de eso. Eh ¿Qué resuelve real, o sea, qué va valor agregado le da al local para que quiera pagar por ese producto? Eh en en este caso pusimos el ejemplo del bar porque es un dato verificado que uno solo, pero podrían ser distintos tipos de promociones que o cosas como que si tú eres residente del estado Chaca de del municipio Chacao, tienes tal edad y trabajas en el y tienes tipo sangre tal, te dice si verificaste la daste.

**[2:57:33]** Trámites, cualquier cosa que quieras realizar, lo puedes hacer. Además, eh planeamos también poner la validación a a través de WhatsApp, de manera que este barcito pueda validar con teléfono. Lo que pasa es que con la validación de software de hardware toma un poquito más de tiempo. Además de que estamos usando el principio de mínimos privilegios. Ese entonces el bar solo va a tener tu edad y todos tus datos están restringidos. Tu cédula, dónde este eh tu tu tu nombre, etcétera. O sea, es el tema es que sean los mínimos privilegios para todos. Ajá, ¿por qué decidieron usar eh un

**[2:58:13]** dispositivo físico en vez de apalancarse en la tecnología NFC del celular? Me parece como más lógico que la persona cargue ese identificador directamente en el celular, ¿no? De hecho, revisamos cédulas como la de Chile y la de la Unión Europea, que yo puedo revisar con el RFID y me sale toda la información de la persona. Lo que queremos esto es como más que todo fragmentar la data de forma de que si yo la leo con el teléfono, yo no tenga acceso, o sea, probablemente a todo, porque la de Chile tengo entendido, por lo que investigamos, que tú al leerla con el teléfono puedes ver la dirección

**[2:58:45]** de la persona, estado civil, nacionalidad y todas esas cosas. Pero ustedes mismos no no definen, o sea, el ID lo crean ustedes en el celular, no no definen qué datos se comparten. se lo vendemos El primer cliente es el Estado. Ellos Esto es una cédula 7.0, si se quiere. Muchas gracias. [aplausos] Pasa. [música]

**[2:59:40]** [música] [música] [música] [música] [música]

**[3:00:24]** [música] [música]

## [3:01:26] Qubbot | 🧊 Three-Dimensional

**[3:01:26]** ¿Cuántas personas no han tenido una idea en algún momento de que desarrollar alguna aplicación o crear algún sistema sin y no la han podido llevar a cabo porque no tienen ni la más mínima idea de programación? Eh El día de el día de hoy la IA escribe muchísimas líneas de código a una velocidad que ni siquiera imaginamos. Es imposible ver y revisar esas líneas de código a la a la misma velocidad. Ocasionando también que dentro de esas mismas líneas queden eh eh datos expuestos, eh alguna brecha que no podamos verificar.

**[3:01:57]** Eh Lo anterior. Lo anterior. Eh según Veracode, más del 45% del el generado por la IA en el 2025 traía fallas de seguridad. Más de 2000 traía vulnerabilidades y en 5600 apps. Es por ello que tenemos Cubot. Es un agente eh y una plataforma en el cual eh te ayuda a desarrollar software a través de la voz en crear un mapa isométrico de en 3D. Bueno, aquí está el código QR para que podáis descargarlo de la

**[3:02:40]** Okay, este es básicamente Cubot. Eh primero voy a entrar con un proyecto de prueba, este se llama plátanos. Y básicamente lo que hace Cubot es que nos genera un entorno 3D isométrico donde podemos ver eh cómo está distribuido nuestro proyecto y aparte tenemos un agente que lo que hace es analizar el proyecto y nos coloreas eh cierto directorio con amarillo rojo para saber si hay un archivo que tiene alguna vulnerabilidad. Por ejemplo, yo puedo expandir cada uno de estos archivos e ir navegando eh dentro de cada uno de

**[3:03:14]** ellos. Inclusive puedo eh puedo abrir un editor de código para corregirlo yo, ¿no? Am, vamos a a crear un proyecto nuevo. Vamos a cerrar este proyecto para que vean más o menos cómo funciona el onboarding. Proyecto rápido. Tenemos el proyecto. Proyecto crear. Okay, tenemos aquí nuestro bot que se va a encargar de guiarnos a a a crear nuestro proyecto desde cero. Le escucho. O use los botones. ¿Ya

**[3:03:47]** programa o está empezando? Estoy empezando. Perfecto. ¿Quiere que use Next.js, Vercel y Supabase Eh no no usé Supabase y comencemos. Listo. Arranco con Next.js. Entonces básicamente lo que va a hacer aquí nuestro bot es que vaya armando nuestro proyecto y nosotros podemos ver en tiempo real cómo va creando cada uno de los directorios. Cada uno de cada uno de nuestros documentos. Y aquí al lado también podemos ver todo

**[3:04:22]** el historial que va que que. Que está realizando nuestro agente. No no prefiero esperar a que termines. Entonces bueno la capacidad de esto eh la verdad es bastante varia tenemos herramientas inclusive que funciona como cualquier editor de código. Vamos a darle aquí en cancelar. Por por lo menos aquí podemos ver el explorador de archivos que tenemos y aquí arriba lo que nos muestra es una

**[3:04:54]** sección con todas las integraciones que detecte nuestro nuestro sistema. Tiempo. Gracias. [aplausos] Eh. Okay. Ajá este no está superchida su su idea sobre todo para personas que. Eh by coders. Eh pero quiero preguntar. Creo que o bueno al menos de mi punto de vista el

**[3:05:27]** el mayor aporte o el mayor como que valor agregado es poder visualizar en 3D qué está ocurriendo y cómo está organizado el proyecto porque al final del día. Yo mismo que eh me encargo de codear muchas veces lo hago hablando pongo el el a con me pongo a conversar con con codex y y lo voy haciendo. Este. Qué mode tienen ustedes para que el día de mañana Cloud no haga esta herramienta para poder ver en 3D el el proyecto o chat GPT etcétera

**[3:06:40]** conectado para que perdón está habilitado para que lo puedas conectar a cualquier proveedor de de LMS eh pero siempre lo selecciona uno no no decide en base a la tarea que es la la que mejor puede usar para ahorrar etcétera [aplausos]

**[3:07:34]** adelante aló mamá team 27 y se prepara [música]

**[3:08:10]** [música] [música] [música] [música]

**[3:08:54]** [música] [música] [música] [música]

**[3:10:49]** [música] [música] [música] Sí.

**[3:11:52]** Dos, uno, go.

## [3:11:55] Aló Mamá | 🚨 Emergencies

**[3:11:55]** Pedir ayuda en Venezuela no es tan simple. Tan solo el año pasado se registraron 155 feminicidios y el agresor frecuente era la pareja. A su vez se documentó un aumento del 196% en las desapariciones forzadas. Estas son algunas de las razones por las cuales creamos a lo mamá. Es un sistema de alerta encubierta con IA de voz que detecta coacción en una llamada y avisa a tu familia incluso sin señal, fingiendo ser tu mamá. ¿Cómo funciona? Un poquito más cercano. Yo tengo aquí mi teléfono, pónganse que yo estoy en un taxi y me siento insegura, veo que el conductor se desvió. No quiero, quiero

**[3:12:28]** alertarle a alguien, pero no quiero que él se dé cuenta, simplemente presiono eh unos botones eh que van a enviar una alerta a este es el panel eh de control que tenemos. Esta alerta lo que hace es que dispara una llamada de una agente que es se supone que es mi mamá. Tengo en la aplicación puedo asignar este una frase clave, puedo asignar este una frase, ya, la vamos a mutear un ratico. Este una frase clave que significa que estoy en riesgo y otra frase clave que significa que estoy a salvo. Entonces ahora hablo con ella,

**[3:13:02]** voy a poner acá, vamos a ver si se escucha, eso creo que sí. Hola, ¿me escuchas? Ay, sí, ahora sí te oigo. Y entonces, cuéntame, ¿cómo vas, pues? No, estoy bien, estoy ya llegando a la casa, pero voy con Andrés. Ah, bueno, qué bueno que vienes con Andrés. ¿Y por dónde andas ya? Es que papá no para de preguntar por ti. No, no, voy llegando, voy voy llegando, te dejo. Hablamos ahorita, chao. Bueno, como pueden ver, nuestra palabra clave era Andrés. Eh saltó una primera alarma eh que era cuando yo presioné los botones. Luego, al confirmar que sí estaba en peligro,

**[3:13:36]** saltó una segunda alarma eh rastreando siempre una transcripción de todo lo que hay en la llamada, ubicación en tiempo real, así sea que estés en movimiento y en la aplicación tú puedes setear cuáles son estas personas de emergencia, este y se les notifica tanto eh por WhatsApp, como pueden ver, aquí estamos todas nosotras que somos el equipo, somos la familia de esta persona asignada y se le se le envía las coordenadas exactas con incluso le el chat, solo que bueno, lo corté por tiempo. Va preguntando eh un poco también a averiguar qué está ocurriendo y te hace un resumen eh para

**[3:14:09]** entender un poco eso. Eh en Discord pueden ver todo esto en vivo, también es importante destacar que esto también funciona sin señal, sabiendo que en Venezuela hay muchas zonas que no funciona así. Vamos a hacer una pequeña prueba, voy a poner el teléfono en modo avión. Okay. Eché para atrás. No, no. Y aquí aparece esta nueva alarma, aquí no hay alarma porque bueno, no tiene señal, pero de todas formas también notifica a las personas que tienes en tus contactos y tiene la ubicación en

**[3:14:41]** tiempo real. Esto es vital porque sabemos que bueno, en el interior del país hay muchos temas de señal y es útil. A la vez eh realmente puedes eh meterle eh por lo menos un audio de tu mamá para que agarre esa voz y es útil porque por lo menos si tienes una pareja, como eh puse al inicio, que capaz hay maltrato o algo, puedes pretender básicamente que es tu mamá o un pariente. Este listo. Gracias. [aplausos] Hola, eh qué ventaja tiene la llamada en

**[3:15:16]** específico versus solamente accionar el botón de SOS en en este caso de uso específico, por ejemplo. Bueno, por lo menos siento que el caso que acabo de mencionar de violencia doméstica puede aplicar porque es difícil este llamar porque a veces únicamente un mensaje de texto no no es instantáneo. A estas llamadas porque estás en una crisis y es difícil disimularlo. Entonces, esta llamada de tu mamá muchas veces es como que Como pueden ver, también lo educamos que fuera venezolana, que fuera, o sea, como que tú lo puedes ir como que educando y le puedes poner, como les dije, la voz de tu pariente. Entonces, de cierto modo, este te ayuda a salir de esa

**[3:15:48]** circunstancia. También, como puse el ejemplo de que estás en un vehículo, que te sientes inseguro y todo eso. Mi pregunta va más enfocada específicamente como cuál es la diferencia entre que me llame y diga Andrés versus que yo apriete un botón de solo de pánico sin tener que decir ninguna palabra. No, ninguna, en verdad. Bueno, en el caso de uso de, por ejemplo, estás tomando un taxi y notas, como comentaba mi compañera, eh que se puede que se haya desviado de la vía, no quieres utilizar el teléfono, claramente escribir ayuda a un compañero

**[3:16:21]** a o una amiga. Eh veo que es una manera sigilosa de demostrar que estás acompañado y de dar una nota de ayuda que llame directamente a tus familiares para que estén atentos a ti. Pero creo que lo principal es la la transcripción de voz, o sea, tú escribes en todo momento la conversación, lo que está pasando y lo que eso es lo que está pasando. Genera un reporte que también, al fin y al cabo, es evidencia. Puede este generar un PDF, de hecho, que puede ser evidencia para cualquier caso de acoso o algo y se puede este, no si lo puedes abrir, eh puedes incluso tenerlo como

**[3:16:56]** respaldo para fuentes este para acudir a la policía o algo, un caso específico. Uno tiene que que previamente, me imagino, configurar tu cuenta de Lo Mamá, poner la palabra de del el ajá, y las puedes poner más de una palabra de peligro. Sí, puedes poner una frase. Una frase de peligro y una frase de de que digo, pero varias [carraspeo] opciones distintas. Porque, por ejemplo, en este caso, por ejemplo, dijeron, "Estoy con Andrés." Pero imagínate que que que yo estoy con Diego, no puedo decir "Estoy con Andrés" porque ya Diego es sí, como así.

**[3:17:28]** Okay, okay. Eh, pero que tengas varias opciones según distintos escenarios. Eh. Sí, exacto. La idea es usar un comodín que se adapte a la situación. Por ejemplo, yo pienso en "¿Le diste la comida a Audi?" Ah, al perro. Y ya que bueno, utilizamos un modelo para detectar ese esa frase. No tiene que ser literalmente dicha, sino bueno, "¿Le diste la comida a Audi?" "¿Preparaste la comida de Audi?" Cualquier cosa. Y que sea algo instantáneo. [aplausos] Muchas gracias.

**[3:18:08]** Adelante, Agent Zero. [música] [música]

**[3:19:18]** [música] [música] [música] Terminando.

**[3:19:52]** Vayan escaneando aquí.

## [3:20:01] AGENT ZERO | 🛡️ AI Security

**[3:20:01]** Somos Agent Zero, el guardia que aprende de cada ataque tus agentes de IA. Hemos hablado mucho sobre atacar y defender, nosotros tenemos una manera disruptiva de tratar a la ciberseguridad para las aplicaciones que tienen agentes de chat. En Venezuela ya conversa con clientes, como podemos ver, el agente de inteligencia artificial mía de Mercantil ha generado más de 26 millones de conversaciones y entre ellas más de 11 millones han sido para restablecer contraseñas. Además, el CICPC reportó que el 80% de los ciberataques iban destinados a la Fintech.

**[3:20:33]** Esto tiene un costo. En Latinoamérica, el ticket promedio son 2.5 millones eh de dólares por cada brecha. Además, recientemente hubo una brecha de datos de 3.2 millones de de venezolanos. Y por último, ajá, eh recientemente, esto fue muy curioso, en un banco en el Táchira, una sola banda con 200 cuentas falsas de un banco logró extraer 10 millones de dólares. Y por eso creamos Agent Zero, del nombre Zero Day, para aquellas vulnerabilidades que aún no conocemos y que ayudamos a preparar a todas las aplicaciones en

**[3:21:06]** cualquier área, retail, Fintech, eh cualquier empresa que lo tenga. Un guardia entre la gente de la IA y tus datos que convierte cada ataque en una regla nueva. ¿Cómo lo hacemos? Eh en medio de cada mensaje tenemos cinco agentes de LLM que están realizando un montón de actividades, pero no ejecutan ninguna tarea de ciberseguridad. Todo cae en el código. Para ello, lo que hacemos nosotros es establecer políticas de seguridad. Estas políticas cada empresa debería tener y el el el sistema está hecho para ser generalizable, políticas que están

**[3:21:40]** basadas en reglas y valida- validadores, que son funciones, básicamente, ¿okay? Entonces, ¿qué tenemos? Un aprendizaje por refuerzo para la seguridad de agentes. Tenemos un agente que cuando recibe un mensaje, nuestro model armor determina si es sospechoso. Y si lo marca como sospechoso, inicia una sesión de engaño en el que va a intentar manipular a la persona que está escribiendo y le va a seguir la corriente. Lo va a incitar a seguir con su ataque y va a aprender de la forma en que lo está haciendo para protegernos. En el caso de que no

**[3:22:11]** funcione, simplemente le vamos a validar las reglas de seguridad para que continúe. Y lo bueno, lo vamos a ver en vivo. Genial. Entonces, hackers, ya sé que colocaron el QR, ya pudieron entrar. Pueden ver que tienen literalmente un chat donde pueden escribir y pueden ir eh interactuando con ellos. Acá vamos a poder ver las diferentes interacciones que ustedes están teniendo de manera en vivo. Entonces, tenemos interacciones, tenemos espacios seguros que prácticamente cuando genera un ataque está entrando a ese espacio y los diferentes ataques que han venido vean llegado a hacer durante el tiempo hasta

**[3:22:44]** ahora. Entonces, tenemos cuatro momentos o seis momentos donde eh llega un punto donde tenemos que generar esta interacción que están haciendo en estos momentos, pero están haciendo parches. Prácticamente todo lo que ustedes están haciendo, que son las interacciones, Right. Okay. [aplausos] Aló, ahí sí.

**[3:23:26]** Ya, el la pregunta que bueno, no alcanzamos a ver la demo específicamente, entonces no sé como que es lo que sucede, pero el como la misma pregunta que los otros que eran como proxies de agentes, etcétera, que es como cómo se diferencia esto de un skill de review y y como analizar. De hecho es un paquete o un módulo que está en el medio y pueden instalar con las reglas de la propia empresa. ¿Qué es lo que está haciendo realmente acá? El validador o las las políticas al final del día son este catálogo de funciones que nosotros podemos tener CRUD, por ejemplo. Eh

**[3:23:59]** obtener el ID, obtener el teléfono, obtener la dirección. Y cada vez que nosotros tenemos un agente que por ejemplo va a solicitar un refund o algo por el estilo, un cambio de contraseña, él lo que está haciendo es ver si cumple o no cumple con parámetros. Este agente que tiene en el medio lo que va a detectar es si está intentando bypassárselo, ya sea por prone injection o porque tiene un documento malicioso en el medio y él va a separarlo en dos. Si él detecta que es un engañoso le va a seguir la corriente hasta para ver, porque se está creando un grafo en ese proceso, hasta donde llega. Y aquí lo que estamos haciendo es aprendiendo patrones. Cuando mencionaba

**[3:24:31]** que se creaba un parche es porque al final si detectamos que efectivamente existe una brecha, porque existe una brecha en el momento por ejemplo de eh generar un refund, porque o que obtuve por ejemplo información de un pedido que no era mío, yo lo que voy a hacer es cancelar la función dentro de mi whitelist posible de request refund o get number ID de X producto y automáticamente toda la aplicación deja de ser vulnerable a esa brecha en específico porque se generó una nueva política. Y acá está llamando el por cada request que se le hace a la aplicación.

**[3:25:03]** Eh no en esta primero pasa por un model armor, que es simplemente un rejects muy complejo, donde nosotros tenemos una lista de las principales vulnerabilidades, empezando por injection, el bueno aquí te lo puede decir específicas que están todas, eh anulación, cambio de rol. Muchas gracias, un fuerte aplauso. [aplausos] Nos queda el último, Meshi. Ahí vienen.

**[3:25:59]** [música] [música] [música] [música]

**[3:26:51]** [música] [música] [música]

## [3:27:54] Meshy | 🚨 Emergencies

**[3:27:54]** Bueno, nosotros somos el equipo número 15, somos Meshi. Este, ¿qué es Meshi? Es una o una una SOS que sale de tu teléfono así no tengas internet. ¿Qué pasa cuando se va la luz en Venezuela? Se cae la señal y nadie sabe que tú necesitas ayuda. Este, por ejemplo, en algunos estados del país hasta 16 horas pueden estar sin luz, pues no tener señal en zonas montañosas o en ocasiones de emergencia como durante el terremoto que no había ni electricidad ni señal y entonces necesitas enviar una una SOS a un

**[3:28:27]** contacto de emergencia. Bueno, nosotros con enviamos una SOS que salta de teléfono en teléfono a través de una red eh mesh, a través de Bluetooth, desde el teléfono que está sin conexión, este, se conecta a varios teléfonos por nodo, por la red mesh, hasta que llegue encuentre un teléfono que tiene internet. Este, se conecta a nuestro servidor y se comunica a tus contactos a través de Capso para enviarle una alerta o un mensaje de tu emergencia y también se conecta a un un LLM en el cual tú le puedes preguntar si

**[3:29:01]** necesitas una respuesta rápida. Vamos ahora con la demo. Okay, vamos a presentar el demo. Okay, en en nuestro caso hicimos una prueba con tres celulares. Uno sería, por así decirlo, la la persona que está desconectada,

**[3:29:33]** en este caso sería este, no tiene modo avión, este el teléfono en la cual uno que es el familiar de emergencia y del medio sería como el nodo en la que sí tiene internet. Los tres este estos dos estarían conectados por Bluetooth a través de la red mesh. Entonces, la idea sería en el en el teléfono que está totalmente desconectado enviar una señal SOS, enviar el mensaje, enviar la gravedad. Envíalo. Okay.

**[3:30:09]** Como se conecta a través de Bluetooth, okay. Perfecto, ahí tú ves de teléfono a Bluetooth y se conecta a través a través de internet a través del teléfono modo eh nodo. Mhm. En este caso a mí me llegó el mensaje de SOS estando offline el teléfono de la de la persona. Exacto. En este caso, por ejemplo, yo al familiar me meto en este enlace y eh automáticamente puedo este enviar un mensaje diciendo que voy para allá o que dónde estás. Lo envío. Eso se envía se procesa a través de la eh de la comunicación

**[3:30:43]** [resoplido] mesh de Bluetooth. Tarda unos segundos y ya llega el mensaje. Yo también a través este de la aplicación puedo enviarle una consulta al LLM conectado, por ejemplo, me golpeé la cabeza y estoy sangrando. Entonces, Tiempo. Okay. Ya. Eh, mi pregunta es como, bueno, pude ver que era como un fork de Bitchat modificado. Ya, pude ver que era un fork de Bitchat

**[3:31:16]** modificado para poder hacer estos request. El mi pregunta es como, ¿por qué decidieron al final como agarrar esto, forkearlo y modificarlo versus como integrar esta gente, este servicio conectado a Bitchat default no más? Bueno, en este caso nosotros decidimos este agarrar esa función y bueno, no nos dio tiempo de explicarlo. Este, la idea es integrarlo a una super app. En este caso usarlo como un SAS, un servicio en la que se puede integrar a cualquier este aplicativo. En este caso nosotros este tuvimos como ejemplo a Yumi, en la cual podemos este integrarlo y hacer una red mesh en la cual este se

**[3:31:49]** convierta en las acciones y así se evita la debilidad en la que tenemos que tener los los teléfonos activados. Sí, este, por ejemplo, yo conocí Bitchat luego del terremoto, la descargué, eh no no encontré nodos cercanos, nunca pude como utilizarla así, pero qué ocurre, este, nosotros encontramos una limitante y es que decirle a las personas, miren, descárguense esta aplicación para una emergencia puede ser un poco complicado, pero este, ¿cuáles son, por ejemplo, las apps que están más descargadas actualmente en Venezuela? Yumi, Cachea. Entonces, podemos implementar este botón

**[3:32:22]** de SOS eh el día de mañana en una de cualquiera de estas super apps, por ejemplo, en Yumi, a través de un mini botón que luego pase a nuestro flujo o a través de Cachea en un en un widget acá que igual pase luego a nuestro flujo. Eh, yo tengo una pregunta, si el teléfono cierra la aplicación antes de que se envíe la alerta, o sea, el SOS, ¿qué pasa con esa alerta que quedó ahí como en el limbo? Bueno, este, previamente, cuando tú inicias la aplicación por primera vez, él te pide unos permisos. Está abierta

**[3:32:56]** en segundo plano, este, tiene permiso de tener el Bluetooth activo. Y, este, por ejemplo, no sé si lo notaron, pero el nodo de, el que se conectó al servidor, el de mi amigo Alejandro, él tenía la aplicación cerrada en ese momento, la tenía en segundo plano, igualmente pasó el mensaje y le llegó mi contacto de emergencia. Y, por ejemplo, ¿qué ocurre con estas aplicaciones que ya están utilizadas en, acá en Venezuela? Por ejemplo, los rides casi siempre tienen su aplicación activa. Entonces, es una ventaja por ahí.

**[3:33:35]** [aplausos] Bueno, llegó el momento de la verdad. Estamos cansados. Eh, los jueces van a revisar los puntajes. Eh, en pocos minutos tendremos noticias.

## [3:33:59] Deliberación del jurado

**[3:34:21]** [música] [música] [música] [música] [música]

**[3:35:14]** [música] [música] [música] [música]

**[3:37:25]** [música] Ah.

**[3:38:41]** [música] [música] [música]

**[3:40:29]** Sí. Mmm.

**[3:42:37]** [música] [música]

**[3:44:19]** Mmm. [música] [música]

**[3:46:45]** [música] [música] [música] [música]

**[3:47:36]** [música] [música] Sí.

**[3:48:14]** [música] Venid todos.

## [3:52:35] Premiación y cierre

**[3:52:37]** Okay, ahora sí. Entonces, el ganador de Plátanos Hack 26 edición Caracas es Pero primero que todo, ¿qué dice el mercado? Primero que todo, ¿le creemos al mercado? El mercado dice

**[3:53:12]** que con un 34.5% de chance gana Museo. [grito] Okay. [aplausos] Esa es la predicción del mercado. Y en base a esta predicción, que aún no es la versión final, el leaderboard actual de los traders se ve así. Eh, el primero con 5,176 bananas es Showcoder. ¿Quién es? 5,000 bananas.

**[3:53:45]** Okay, muy bien. [aplausos] Esto aún no significa nada, porque si es que si es que sus predicciones del mercado no están correctas y él aún no ha vendido bananas, significa que esas bananas se pierden. Okay. Okay. Ahora sí, vamos a ir con los premios por track. Recuerden, cada ganador de track eh gana para el equipo 400 dólares

**[3:54:19]** y uno de esos ganadores del de track eh será el ganador de la Platinum Hack 26 Caracas y ese equipo, en vez de 400, ganará 1200 y viajará a Chile en menos de un mes. [aplausos] Viajará a la Hackaton de Chile, no no viajará a pasear. Bueno, pueden pasear igual, pero Okay. Ganadores por track.

**[3:54:53]** Track AI Security. Segundo lugar, no tiene premio, pero estuvo cerca. [risas] El segundo lugar del track AI Security es para el equipo, redoble de tambores, para el equipo Gotchu. Un fuerte aplauso para Gotchu. [aplausos] Con un score de 35.

**[3:55:28]** Ese score significa que eh después de normalizar los puntajes, convertirlos en un valor de 0 a 100, de 0 a 1, multiplicarlo por 100, nos dio 35. Eh primer lugar del track AI Security, ellos ganan premio, Arcángel. [aplausos] Adelante equipo Arcángel a una foto, por favor. [aplausos] [ovación]

**[3:56:13]** [aplausos] Foto con foto con el equipo plátanos y después fotos de ellos solos. Felicidades team.

**[3:57:07]** Okay. Acá hice un pe, cometí un pequeño error y es que puse el puntaje, este puntaje podría revelar información, pero en los otros primeros lugares no puse el puntaje, así que todo está bien. Para que vean que no hago mis presentaciones con IA. Para bien o para mal. Okay, seguimos con el track de

**[3:57:43]** emergencias. El segundo lugar del track de emergencias, redoble de pies, el segundo lugar del equipo del track de emergencias es para el equipo Presente. Equipo 25. [aplausos] ¿Qué pasó? ¿Tiene puntaje? Eh, equipo 25.

**[3:58:19]** Son cosas que pasan. No durmió. Eh, primer lugar del equipo de emergencias, por favor, redoble, por favor, es para Aloha. [aplausos] [ovación] [aplausos] Adelante, por favor. Felicitaciones.

**[3:58:51]** Gracias. Gracias. Felicitaciones. Qué cracks. Felicitaciones. Qué cracks. Gracias. Gracias a todos. Gracias. ¿Sabemos o no? O no lo podemos Pero que vaya, ¿no? Gracias. A ver, ¿solo no quieren? Sí, sí, una solos. Vamos.

**[3:59:30]** Gracias. [aplausos] Okay, seguimos. Track Trust. Segundo lugar del Track Trust. Eh, re doble, por favor. El segundo lugar del Track Trust es para

**[4:00:04]** el equipo Quorum. Enhorabuena. [aplausos] Felicitaciones, equipo Quorum. El primer lugar del equipo Trust, o sea, del Track Trust. Ya no puedo pensar. Es para el equipo Smart Traffic.

**[4:00:38]** [aplausos] Adelante, por favor. [aplausos] Gracias.

**[4:01:37]** Gran de equipo Smart Traffic. Okay. Continuamos. Queremos dormir y comer. Segundo lugar del track de tres dimensiones, por favor. Tri redoble tridimensional. El segundo lugar del track de tres dimensiones es para el equipo Kubot.

**[4:02:12]** Kubot. [aplausos] Felicitaciones equipo Kubot. El primer lugar de el track de tres dimensiones redoble tambores. Para sacarse una foto con el equipo

**[4:02:44]** Platanus. Ese es el premio. Falta Nacho que está en la cámara. Nos encantaría que se suba a la última foto. Es para el equipo Museo. [aplausos][ovación] Equipo cinco. Adelante. [aplausos] Felicitaciones. Gracias. Gracias. Qué cracks. Felicitaciones.

**[4:03:19]** Cansancio lo valió. El el kinder fue la clave. Fue la calidad. Ya saben para el siguiente año 14. [risas] Un abrazo para el equipo museo. [aplausos] Ya no estoy seguro si viene en la

**[4:04:12]** siguiente slide. Así que Voy a pedir un redoble de tambores ahora, aunque no sea la siguiente slide, no lo sé, pero redoble de tambores por si se me escapa. El ganador de Platanus Hack 26, edición Caracas junto a Yumi es el equipo ganador. [risas] No es falso. 1 2 3

**[4:04:57]** con un score de 80.7 es lo escribí o no. No. Bueno, lo digo ahora. Es museo. Felicitaciones. [ovación] [aplausos] Digan tres dimensiones.

**[4:06:09]** Felicidades. [aplausos] Qué grandes. Muchas gracias. ¿Quieren foto? Nos vemos en Chile. [aplausos][ovación] Bien, ¿está bien una una? Les saco con el teléfono una. ¿Cómo? Les saco una con el teléfono aquí. Ah, con el Con el iPhone. Ahí. Increíble. Digan, no sé, que en el museo. Museo. Ya.

**[4:06:41]** Increíble. Gracias. Queda el último ganador. Nos vemos en Chile Team Museo. [aplausos] Okay, ahora el ganador del Market y nos vamos. Ah. No, está bien, está bien. Fue a propósito. El ganador del Market y ahora sí nos podemos ir. El ganador del Market. El mercado.

**[4:07:17]** El mercado. Okay. El ganador. Ya tenemos ganador del mercado. El ganador de el mercado. Si logro conectarme a la pantalla.

**[4:07:55]** Es para tarararata. Compartimos, comparto. Se. Okay. Okay. Dados los resultados, el nuevo ganador es Gede Castellano. [aplausos] Venga a sacarse. Venga a sacarse una foto. ¿Qué pasó? Insider Insider trading.

**[4:08:31]** [risas] Muy bien, se la jugó por sí mismo. O sea que te vas a gastar esa plata. ¿En qué? En Chile, en choripanes. Choripanes, muy bien, felicitaciones. Bueno. Un fuerte aplauso para los jueces. [aplausos] Que aguantaron muchas horas aquí. Lo pasamos increíble de parte del equipo

**[4:09:05]** de Platanus, mil gracias, mil gracias Yumi. Los queremos mucho, hasta la próxima. [ovación] Acá está. Gracias a todos.

**[4:09:44]** Ah, sí, pueden si está habilitada, sí, pueden jugar ping pong.
