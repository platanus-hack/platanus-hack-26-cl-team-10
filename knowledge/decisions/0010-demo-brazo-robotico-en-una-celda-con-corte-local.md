# ADR-0010 — El demo es un brazo robótico en una celda, y el corte de energía es local en el edge

> Estado: `accepted` · Fecha: 2026-11-21 · Aceptado por el equipo el 2026-11-21 · Reemplaza la correa a escala del [Demo propuesto](../architecture/FLUJO.md#demo-propuesto)

## Contexto

El demo propuesto era una correa transportadora a escala. Lo construido hasta ahora es otra cosa: una pauta de bloqueo sobre un escritorio, con un mouse y un lápiz como objetos que ve la cámara. Esa pauta tiene un hueco: el bloqueo es un paso de cámara, y saltárselo no dispara ningún aviso, porque la regla de orden invertido solo mira lecturas de sensores y la cámara no interrumpe ([ADR-0004](./0004-verificacion-por-capas.md)).

El equipo tiene un brazo robótico impreso con servomotores y pinza, un ESP32, un sensor ultrasónico, un sensor de temperatura y humedad, un pulsador y un motor DC. Un brazo en movimiento se ve peligroso sin explicarlo, y eso es lo que el demo tiene que mostrar: una máquina peligrosa que el sistema ayuda a operar con seguridad.

## Decisión

1. **El demo es el brazo dentro de una caja que simula la celda de trabajo.** Cuatro momentos: el brazo falla y Factum abre la OT desde el protocolo; el operario se salta el corte de energía y se acerca con el brazo energizado; Factum corta los servos y le habla; lo guía por la OT hasta que el brazo vuelve a trabajar bien. El guion está en el [FLUJO](../architecture/FLUJO.md#demo-propuesto).
2. **El paso que se salta es cortar la energía**, y lo cierran sensores, no la cámara: el estado del relé de los servos y un interruptor en el bloqueo. Así el salto lo detecta la capa 1, que es la que interrumpe.
3. **El corte lo hace el ESP32, no el servidor.** Cuando el ultrasonido marca la zona ocupada y la energía está viva, el ESP32 abre el relé por su cuenta y después lo informa. Una función de seguridad no puede depender de la red ni de la VM: si se cae internet en pleno demo, el brazo igual se detiene.
4. **En el pitch, el corte es una integración opcional.** Factum, instalado sin integrarse al control, avisa y guía. Conectado al relé de seguridad de la máquina, además la detiene. Así no se contradice el «no tocamos el control» del [CONTEXTO](../domain/CONTEXTO.md).

## Alternativas consideradas

- **A — Seguir con la pauta de escritorio:** ya corre, pero no se ve peligrosa y su salto central no se detecta.
- **B — Volver a la correa a escala:** tiene el costo por hora detenida a favor, pero hay que construirla y el brazo ya existe.
- **C — Que la cámara detecte a la persona y detenga el brazo:** la cámara es capa 2 y su tasa de falsas alarmas no está medida; una parada de seguridad no puede descansar en ella.
- **D — Que el servidor ordene el corte:** el corte quedaría a merced de la red y de la latencia de la VM.

## Consecuencias

- Hace falta hardware nuevo: un relé en la alimentación de los servos, un interruptor en el bloqueo, la caja y una cámara cenital. El ultrasonido y el ESP32 ya están.
- El firmware del ESP32 pasa de solo leer a también actuar, con una regla propia que no espera al servidor. Esa regla tiene que ser la misma que la de capa 1 en `reglas.py`, o el servidor y el brazo van a contar historias distintas.
- La pauta del brazo se escribe a mano, como las de hoy, porque convertir un protocolo en pauta sigue siendo un stub.
- La pauta de escritorio queda para ensayar sin el brazo.

## Pendientes y no verificado

- Cómo se detecta que el brazo falló: la cámara viendo la pieza fuera de la bandeja, o un sensor en la bandeja. `Brecha`.
- Si el detector distingue la pinza, la pieza y la herramienta con la cámara cenital. Hoy reconoce mouse y lápiz. `Brecha`.
- La norma de seguridad que respalda la regla de persona en la zona con energía viva en celdas robotizadas. No se buscó. `Brecha`.
- Cuánto tarda el ESP32 en abrir el relé desde que alguien entra a la zona. Sin medir. `Brecha`.

## Referencias

- [ADR-0004](./0004-verificacion-por-capas.md), sobre qué capa interrumpe.
- [LOGICA](../architecture/LOGICA.md#qué-puede-interrumpir-al-operario) y [FLUJO](../architecture/FLUJO.md#demo-propuesto).
- REFERENCIAS 9, para la cámara cenital, y 40, para el aislamiento de energía como peligro de alta consecuencia.
