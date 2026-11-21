# Factum

**El copiloto de tus operarios.** Factum acompaña al operario mientras ejecuta una orden de trabajo: comprueba cada paso con cámara y sensores, y le avisa en el momento si se salta uno. Como está en cada trabajo, todo queda registrado con su evidencia, y la operación sabe que cada trabajo se hizo bien sin poner un supervisor encima de cada uno. El caso de uso es el mantenimiento de maquinaria, donde una mala ejecución cuesta vidas y horas de detención.

## El problema

Las operaciones críticas, como una faena minera, tienen procedimientos, pero no pueden comprobar que se cumplen. En 2025, entre los miembros de ICMM, la ejecución inefectiva de un control fue la falla más común en los incidentes fatales: 19 de 26. Y una correa transportadora detenida puede costar cientos de miles de dólares por hora.

## Cómo funciona

1. **Pauta.** El protocolo del cliente se convierte en pautas, y de ellas salen las órdenes de trabajo. Cada paso define qué evidencia lo cierra.
2. **Verificación.** La cámara, los sensores y las reglas deterministas comprueban cada paso. No depende solo de un modelo de lenguaje.
3. **Aviso.** Si el operario se salta un paso, recibe el aviso por audio y lo corrige en ese momento.
4. **Reporte.** Cada paso verificado queda como un hecho con su evidencia: el reporte no se escribe ni omite nada, y el turno siguiente retoma desde ahí.
5. **Mejora continua.** El operario deja lo que observa mientras trabaja. Cuando el mismo paso se desvía en varias ejecuciones, Factum propone mejorar la pauta; el supervisor la valida, y con la versión nueva se comprueba si el paso dejó de desviarse.
6. **Métricas por API.** Cumplimiento, desviaciones y tiempos por pauta, equipo, paso y día, hacia los sistemas del cliente. Se agrupan por pauta y por equipo, nunca por persona: Factum mira el paso, no a quien lo ejecuta.

## El demo

Un brazo robótico dentro de una celda. Falla, y Factum abre la orden de trabajo desde el protocolo. El operario se salta cortar la energía y se acerca con el brazo en movimiento: Factum lo detiene, le avisa y lo guía paso a paso hasta que el brazo vuelve a trabajar bien. Factum no reemplaza la seguridad de la máquina: hace que se cumpla.

## Equipo

Track 🌎 Physical World · team-10

- Francisco Zúñiga ([@dreamxist](https://github.com/dreamxist))
- Diego Villanueva ([@dvillanuevaaraya](https://github.com/dvillanuevaaraya))
- Jonathan Riquelme ([@sh1njr](https://github.com/sh1njr))
- Daniel Godoy ([@godoy97](https://github.com/godoy97))
