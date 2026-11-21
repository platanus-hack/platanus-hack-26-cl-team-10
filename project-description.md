# Mantenimiento Verificado

**Un operario aumentado con IA:** un copiloto que comprueba cada paso de la pauta de mantenimiento mientras se ejecuta y avisa en el momento si falta uno.

## El problema

En una operación donde un error de mantenimiento sale caro, como una faena minera, los procedimientos existen pero nadie puede comprobar que se cumplieron. Entre los miembros de ICMM, la ejecución inefectiva de un control fue la falla más común en los incidentes fatales de 2025: 19 de 26. El control existía y se ejecutó mal. Además, una detención no planificada de una correa transportadora puede costar cientos de miles de dólares por hora, y las órdenes de trabajo escritas en texto libre no sirven como dato.

## Qué hacemos

1. **De protocolo a pauta comprobable.** El cliente entrega el procedimiento que ya tiene y el sistema lo vuelve una pauta donde cada paso declara qué evidencia lo cierra.
2. **La OT nace de la pauta.** Por calendario, por pedido o por una falla del equipo, el sistema genera la orden de trabajo con los pasos en orden.
3. **Verificación en el momento.** Cámara y sensores (vibración, temperatura) comprueban el paso actual. Si el operario se salta uno, recibe el aviso por audio y lo corrige ahí.
4. **La bitácora es la ejecución verificada.** El turno siguiente retoma desde el último paso verificado, la pauta mejora con cada ejecución y el supervisor ve dónde se saltan pasos.

## Cómo verificamos

La verificación no depende solo de un modelo de lenguaje. Va por capas: reglas deterministas sobre el orden de la pauta, sensores leídos por un ESP32 y un modelo de visión que juzga la evidencia de la cámara. La entrada es no invasiva: sensores pegados al equipo y la cámara del operario, sin tocar el PLC ni pedirle integración a TI.

## El demo

Una correa transportadora a escala. Se carga la pauta, se genera la OT y el operario la ejecuta mientras el sistema verifica cada paso, con foco en el aislamiento de energía. Cuando se salta un paso, el sistema lo detecta y lo avisa en vivo.

## Equipo

Track 🌎 Physical World · team-10

- Francisco Zúñiga ([@dreamxist](https://github.com/dreamxist))
- Diego Villanueva ([@dvillanuevaaraya](https://github.com/dvillanuevaaraya))
- Jonathan Riquelme ([@sh1njr](https://github.com/sh1njr))
- Daniel Godoy ([@godoy97](https://github.com/godoy97))
