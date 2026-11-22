# Cambio de polín en la cinta · protocolo corto

> Redactado por el equipo de Factum para el demo. No es el procedimiento de una operación real ni sale de una norma. Es el mismo cambio de polín de `prot-maqueta-01`, escrito como lo traería un cliente: solo lo que hay que hacer, sin decir dónde tiene que estar la persona.

## 1. Alcance

La cinta a escala del demo: un motor que se enciende y se apaga con un botón, un ESP32 que mide a qué distancia está la mano, y una cámara sobre la mesa. Los polines son latas.

## 2. Procedimiento

1. Apagar el sistema.
2. Retirar el polín rojo.
3. Poner el polín verde.
4. Encender el sistema.

## 3. Lo que el protocolo no dice

No dice que la persona se aleja de la cinta antes de encender. La estación lo mide igual: con alguien junto a la cinta y el motor encendido, Factum avisa (`app/reglas.py`) y «Encender el sistema» no se cierra hasta que la persona se aleja. Cuando eso se repite en varias OT, Factum propone agregar el paso que falta (`app/sugerencias.py`).

## 4. Registros

Los de cualquier OT: quién la ejecutó, cuándo se cerró cada paso, las alertas con su inicio y su fin, los relevos de turno y la foto con que la cámara cerró cada paso que se comprueba mirando.
