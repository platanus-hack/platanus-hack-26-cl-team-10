# Factum

**AI Augmented Operator.** Vuelve verificable cualquier flujo operacional: comprueba cada paso mientras se ejecuta y avisa al operario en el momento si se salta uno. El caso de uso es el mantenimiento de maquinaria, donde una mala ejecución cuesta vidas y horas de detención.

## El problema

Las operaciones críticas, como una faena minera, tienen procedimientos, pero no pueden comprobar que se cumplen. En 2025, entre los miembros de ICMM, la ejecución inefectiva de un control fue la falla más común en los incidentes fatales: 19 de 26. Y una correa transportadora detenida puede costar cientos de miles de dólares por hora.

## Cómo funciona

1. **Pauta.** El protocolo del cliente se convierte en una orden de trabajo, y cada paso define qué evidencia lo cierra.
2. **Verificación.** La cámara, los sensores y las reglas deterministas comprueban cada paso. No depende solo de un modelo de lenguaje.
3. **Aviso.** Si el operario se salta un paso, recibe el aviso por audio y lo corrige en ese momento.
4. **Bitácora.** Cada paso verificado queda como un hecho: el turno siguiente retoma desde ahí y el supervisor ve dónde se saltan pasos.

## El demo

Una correa transportadora a escala con el aislamiento de energía como paso crítico. Se carga la pauta, el operario ejecuta y Factum detecta en vivo el paso que falta.

## Equipo

Track 🌎 Physical World · team-10

- Francisco Zúñiga ([@dreamxist](https://github.com/dreamxist))
- Diego Villanueva ([@dvillanuevaaraya](https://github.com/dvillanuevaaraya))
- Jonathan Riquelme ([@sh1njr](https://github.com/sh1njr))
- Daniel Godoy ([@godoy97](https://github.com/godoy97))
