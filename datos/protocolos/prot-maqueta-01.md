# Ejemplos en la maqueta del demo

> Redactado por el equipo de Factum para la maqueta del demo. No es el procedimiento de una operación real ni sale de una norma: describe tareas de ejemplo que la estación a escala puede seguir y comprobar con lo que mide. Una pauta que sale solo de este protocolo no sirve para intervenir un equipo de verdad.

## 1. Alcance

La estación a escala del demo: una correa de juguete movida por un motor que se enciende y se apaga con un botón, un ESP32 que mide la distancia de la mano y la temperatura del equipo, y una cámara sobre la mesa (`edge/edge.py`, `edge/loto.py`). Sirve para mostrar cómo Factum sigue una OT paso a paso, avisa cuando algo se hace fuera de orden y le pregunta a la cámara lo que los sensores no ven.

## 2. Lo que la maqueta no tiene

La maqueta no tiene un punto de aislación ni un punto de bloqueo real. El botón que apaga el motor es el mismo mando con que se opera, y el protocolo de aislamiento (`prot-aislamiento-01`) dice que el candado no va ahí. Tampoco hay cómo comprobar energía cero intentando una partida. Por eso las pautas de este protocolo no salen del de aislamiento: lo imitan, pero no lo cumplen.

| En un equipo real | En la maqueta |
|---|---|
| Cortar la energía en el punto de aislación | Apagar el motor con su botón (`energia`) |
| Poner tu candado | Trabar el botón de parada (`bloqueo`), o dejar un mouse sobre la mesa como dispositivo de bloqueo |
| Comprobar energía cero | Esperar a que el equipo esté frío (`equipo`); no es una prueba de partida |
| Acercarse al equipo | La mano a menos de la distancia que mide el sensor (`operario`) |
| El polín o la herramienta | Latas, plumones o un lápiz que la cámara reconoce |

## 3. Los controles que imita

Son tres, en este orden, y cada pauta de este protocolo los tiene que traer (ADR-0016). Imitan los de `prot-aislamiento-01` con lo que la maqueta tiene; no los cumplen.

| Control | Imita | Cómo se comprueba en la maqueta |
|---|---|---|
| M1 · Apagar el motor | Aislar | `energia = cortada` |
| M2 · Trabar la parada | Bloquear | `bloqueo = puesto`, o la cámara ve el dispositivo de bloqueo |
| M3 · Esperar a que se enfríe | Comprobar energía cero | `equipo = frio`; no es una prueba de partida |

## 4. Lo que sí se puede mostrar

- **El orden:** acercarse con el motor encendido es peligro, y Factum avisa al instante.
- **Los controles que no se deshacen:** soltar la traba con alguien cerca abre una alerta hasta que se repone.
- **La cámara como evidencia:** un paso que se comprueba mirando se cierra cuando el VLM responde que sí, y un reemplazo se juzga comparando la foto de antes con la de ahora.

## 5. Pautas de ejemplo

- `pauta-polin-demo`: el cambio de polín en 2 minutos, con plumones como polines y el botón trabado como candado.
- `pauta-polin-estacion`: el cambio del polín rojo con lo que el ESP32 mide de verdad (motor, distancia y temperatura) y latas como polines. No tiene candado.
- `pauta-loto-escritorio`: un bloqueo de escritorio, con un mouse como dispositivo de bloqueo y un lápiz como herramienta.

## 6. Registros

Los de cualquier OT: quién la ejecutó, cuándo se cerró cada paso, las alertas con su inicio y su fin, y la foto con que la cámara cerró cada paso que se comprueba mirando.
