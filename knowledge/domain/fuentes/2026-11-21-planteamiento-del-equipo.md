# Planteamiento del equipo — 2026-11-21

> Fuente original, no se edita. Es el planteamiento del equipo dictado por voz, que Francisco pasó al knowledge el 2026-11-21. El texto va tal como salió de la transcripción. Lo que se desprende de él está en [CONTEXTO](../CONTEXTO.md), [FLUJO](../../architecture/FLUJO.md) y el [ADR-0004](../../decisions/0004-verificacion-por-capas.md).

## Cómo leer la transcripción

Tres palabras parecen errores del dictado. Así se interpretaron, `Candidata a validar`:

- «ISP» se leyó como ICP, el perfil de cliente ideal.
- «Horario de trabajo» se leyó como orden de trabajo.
- «Una muela» se leyó como el auricular: el propio texto lo explica como «este comunicador en el oído».

## Transcripción

Ok, el problema ataca principalmente al dolor que se enfrentan en esta situación las mineras, por ejemplo, cuando ocurre una parada de cinta transportadora, por ejemplo, no planificada. Esto tiene un valor monetario de retraso por cada hora de hasta 300 mil dólares. Además, el no tener el trabajo efectuado de manera correcta podría generar, por ejemplo, en el peor de los casos, la muerte de un operario.

Por ello, creemos que una solución atingente a este problema serían protocolos de procedimientos estandarizados, que actualmente no son verificables. Ese problema queremos verificarlo a través de AI como un copilot del operario. Entonces, al final tendríamos un AI augmented operator. Ese sería como nuestra premisa máxima.

¿Cómo haríamos esto? Lo haríamos a través de que, siendo como foco el ISP de un cliente que ya tiene protocolos de procedimientos estandarizados, pero que no tiene las capacidades para verificarlo y depende netamente del operario que este trabajo se lleve a cabo correctamente, creemos que eso lo estuvimos… nosotros buscamos poder verificarlo a través de AI.

Entonces, como sería el flujo que nosotros nos imaginamos en gran medida es: entre un protocolo que ya existe, a través de AI esto genera una OT, un horario de trabajo. Luego esta OT de trabajo se empieza a ejecutar. ¿Qué empezamos a recopilar cuando se empieza a ejecutar? Tenemos computer vision y además tenemos todos los sensores que nos permitan, a través de IoT, recopilar información. Estos pueden ser vibraciones, temperatura, entre otros.

A medida que el operario va avanzando en la OT, la gracia está en que, por ejemplo, si se llega a saltar algún paso, en este caso la IA le entrega feedback. Actualmente creemos que la manera más eficiente es a través de una muela, lo que igual es como este comunicador en el oído, que le recuerde que ha generado un error en el orden correcto de las tareas en la OT.

¿Qué logramos con esto? Que el problema sea solucionado en el momento y no después, porque si no, igual estaríamos incumpliendo en el objetivo de poder alcanzar a hacer la reparación en el tiempo pronosticado y ahorrarnos el dinero de extendernos más allá o, en un peor escenario, ahorrarnos el problema de que alguien se vea accidentado o pierda la vida.

Una vez que va avanzando y se va finalizando, y por consecuencia cada uno de los pasos de la OT se va verificando, encontramos que pueden haber casos, por ejemplo, donde un procedimiento tome más de un turno. Esto igual encontramos valor, que permitamos que el siguiente turno tome la continuación del trabajo de manera eficiente y que no tenga que preguntarle o depender del operador anterior: qué tan detallado es el trabajo. Como qué tan detallado es el trabajo, esto va a depender también de un resumen de AI o puede hacer consultas o puede hacer un briefing. Ahí estamos por definirlo.

Una vez que está listo, queda listo y, tras N iteraciones de este mismo procedimiento, nosotros podemos entregar mejoras del mismo. Si bien hablamos de un ISP que tiene esta regla ya de protocolos de procedimiento estandarizados ya existentes, creemos que esta misma habilidad o esta misma funcionalidad de permitir proponer mejoras puede existir solo con el hecho de observar cómo un operario ejecuta una acción en particular. Y para aquellas empresas que no tengan el protocolo establecido, después de una iteración, nosotros podríamos entregar un protocolo y desde ahí empezar nuevamente el flujo, como si fuese el primer caso de un ISP.

La ventaja también está en que no estamos basándonos netamente en un LLM para poder determinar si la operación fue correctamente aplicada, sino que tenemos también inputs determinísticos. Todo, además de esto, nos permite sacar externalidades positivas, como por ejemplo que un supervisor pueda irse a áreas donde estamos observando que más operarios están saltándose pasos o no están siguiendo el protocolo como corresponde, o tienen incidencias o tienen comportamientos peligrosos. Además, también nos permite entender cuáles protocolos quizás tienen muchos puntos de mejora debido a que varias personas están saltando pasos, siendo que ellos son operarios que normalmente no les ocurre.

Esto también genera una eficiencia en cuanto a los supervisores, ya que ahora los supervisores de verdad podrían estar supervisando solo aquellos trabajos que realmente son un riesgo más alto. Es importante que con el computer vision y los sensores nosotros podamos extraer esta información y llevarla a un sistema determinístico, a un sistema, mejor dicho, que tenga distintas capas, donde una capa sea determinista, otra capa puede utilizar algoritmos o algoritmos de soft computing, machine learning, redes neuronales, no sé, tenemos que determinarlo, y otro segmento podría utilizar un modelo de lenguaje directo por API para clasificar cada uno de estos segmentos.

Con diferentes capas estamos pensando también en una demo de cómo podríamos ejecutar esto en vivo. Tenemos Arduino, tenemos Raspberry, tenemos sensores, receptores, motores, tenemos un montón de cosas que podríamos utilizar, tenemos ESP, y algo que se nos ocurre es poder mostrar en una interfaz visual cómo el procedimiento, o sea, cómo el protocolo los envía, se genera la orden de trabajo y cómo el operario es asistido cuando se equivoca, evitando la muerte de esa persona y así generando el impacto que buscamos generar.
