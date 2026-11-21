# Mantención de polines en correa transportadora

> Redactado por el equipo de Factum como ejemplo de lo que entrega un cliente; no es el procedimiento de una operación real. Sale del DS 132 art. 52 y 116 (REFERENCIAS 44), de 30 CFR 56.14105 y 56.14112 (45), de la alerta de MSHA sobre correas (46), de la estrategia de controles de Antofagasta Minerals (56) y de los manuales de polines de PPI (57) y Martin (58, 59).

## 1. Alcance

Revisar y cambiar los polines de la correa CT-01. Aplica junto con el protocolo de aislamiento y bloqueo de energías.

## 2. Palabras de este protocolo

| Palabra | Qué es |
|---|---|
| **Polín** | El juego de rodillos sobre el que corre la correa. Hay uno cada pocos metros; cada uno es una *estación*. |
| **Tapa protectora** | La reja que cubre los rodillos para que nadie meta la mano mientras la correa anda. En las normas se llama *guarda*. |
| **Palanca de corriente** | El interruptor del tablero que da corriente al motor de la correa. La baja y la sube un eléctrico autorizado. En las normas, *desconectador*. |
| **Candado personal** | Cada trabajador tiene el suyo, con una tarjeta con su nombre. Se pone en la caja de bloqueo y la llave la guarda él. Mientras esté puesto, nadie puede volver a dar corriente, y solo lo saca quien lo puso. |
| **Caja de bloqueo** | La caja junto al tablero donde se ponen los candados. |
| **Botonera** | Los botones de partir y parar que están junto a la correa. |

## 3. Lo que no puede pasar

| Lo que no puede pasar | Cómo se evita | Cómo se comprueba |
|---|---|---|
| Que la correa se mueva con alguien metiendo las manos | Correa parada, sin corriente, con candado puesto, y probado que no arranca (44, art. 116; 56) | Correa quieta, palanca abajo, candado puesto y la correa no responde al botón de partida |
| Que alguien trabaje sin tapa con la correa con corriente | La tapa se saca solo sin corriente y con candado, y vuelve antes de sacar el candado (45, 56) | La tapa no aparece sacada mientras haya corriente |
| Que un rodillo trabado se caliente y dañe la correa | Los polines se revisan y su temperatura se vigila (56) | Ruido, giro libre y temperatura del rodillo |

MSHA cuenta ocho muertes con correas desde 2017, seis con la correa andando (46).

## 4. Cuándo se cambia un polín

- Un rodillo no gira: se traba y desgasta la correa y el propio rodillo (57).
- Hace un ruido raro, que suele ser el rodamiento (57).
- Se calienta más de lo que la operación aceptó (56).
- Tiene material pegado que no sale al limpiarlo (57).

## 5. Antes de empezar

1. Revisa el número de la correa y la estación del polín que vas a cambiar (56).
2. Coordina la parada con la sala de control.
3. Ten a mano el polín nuevo, del tipo que pide el fabricante, y revisa que sus rodillos giren sueltos (57).

## 6. Bloque A · Dejar la correa sin poder moverse

Es el control crítico 1 de la estrategia de Antofagasta Minerals (56): cortar la energía, bloquear y probar que no hay energía. Son tres cosas distintas y van en este orden.

1. **Parar la correa.** Pide la parada y espera a que quede quieta y vacía. Trabajar con la correa vacía es lo recomendado (58).
2. **Cortar la corriente.** El eléctrico baja la palanca de corriente del motor.
3. **Poner tu candado.** Tu candado y tu tarjeta en la caja de bloqueo, y la llave contigo.
4. **Probar que no arranca.** Aprieta partir en la botonera y mira que la correa no se mueve.

## 7. Bloque B · Cambiar el polín

5. **Sacar la tapa protectora** de la estación. Recién ahora, con los cuatro pasos anteriores hechos (56).
6. **Cambiar el polín.** Levanta la correa, suelta los pernos, saca el polín trabado, pon el nuevo alineado con la correa y aprieta sus pernos; normalmente son cuatro (57). Gira los rodillos con la mano: tienen que girar sueltos.
7. **Volver a poner la tapa** y apretarla. Va antes de sacar el candado (56).

## 8. Bloque C · Devolver la correa a trabajar

8. **Sacar tu candado**, con todos fuera de la correa.
9. **Devolver la corriente.** El eléctrico sube la palanca y avisa a la sala de control.
10. **Probar sin carga.** La correa parte vacía; mira que el rodillo nuevo gira y que la correa va derecha. Después se carga de a poco (59).

## 9. Registros

El polín cambiado y su estación, por qué se cambió, quién cortó la corriente y quién puso candado, y cómo salió la prueba sin carga.

## 10. Pautas que salen de este protocolo

- `pauta-polin-ct-01`: el cambio de polín, con los tres bloques completos. Sus pasos se llaman igual que aquí.
- `pauta-polin-demo`: la versión de 2 minutos para el demo, con la correa a escala. Deja fuera la tapa protectora y la prueba sin carga, y agrega «acercarte a la correa» y «alejarte», que mide el sensor de distancia.
- `pauta-polin-estacion`: la que corre en la estación física, con lo que el ESP32 mide de verdad: el motor que se apaga y enciende con el botón, la distancia y la temperatura. Seis pasos: apagar el motor, acercarse, esperar a que enfríe, ubicar el polín rojo (la cámara lo tiene que ver), cambiarlo (la cámara deja de verlo) y dejar la cinta andando. Que no se vea un polín rojo no prueba que se sacó: por eso primero hay que verlo. No tiene candado, porque la estación no lo mide.
- `pauta-correa-ct-01`: el cambio de rodillo del demo anterior. Junta cortar la corriente y poner candado en un paso y no prueba que no arranca.
