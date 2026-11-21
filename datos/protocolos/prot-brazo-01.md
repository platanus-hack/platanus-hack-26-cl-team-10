# Ajuste de pinza en brazo robótico

> Redactado por el equipo de Factum para el demo del ADR-0010; no es el procedimiento de una operación real. La secuencia de aislar, bloquear y comprobar energía cero sale de REFERENCIAS 56. La norma de seguridad de celdas robotizadas que lo respalda no se buscó: `Brecha`.

## 1. Alcance

Ajuste de la pinza del brazo BR-01 cuando suelta la pieza, dentro de su celda. Aplica junto con el protocolo de aislamiento y bloqueo de energías.

## 2. Peligros y controles críticos

| Lo que no puede pasar | El control | Cómo se comprueba |
|---|---|---|
| Que el brazo se mueva con una persona dentro de la celda | Nadie entra con el brazo energizado: la energía se aísla, se bloquea y se comprueba antes de acercarse | Relé de los servos abierto, candado en el punto de bloqueo y orden de partida sin respuesta |
| Que alguien devuelva la energía con una persona adentro | El candado es personal y la energía vuelve solo con la celda despejada | Zona libre antes de retirar el bloqueo |

La celda tiene una última barrera que no depende del procedimiento: si alguien entra con el brazo energizado, corta los servos por su cuenta. No reemplaza al bloqueo: el corte automático se repone solo, y el candado no.

## 3. Antes de empezar

1. Avisa que el brazo sale de servicio y espera a que termine su ciclo.
2. Ten a mano la herramienta de ajuste y tu candado.

## 4. Detener y aislar

1. Corta la alimentación de los servos en el tablero de la celda.
2. Pon tu candado en el punto de bloqueo del tablero y guarda la llave contigo.
3. Da la orden de partida desde el mando y comprueba que el brazo no se mueve.

## 5. Ajustar la pinza

1. Entra a la celda.
2. Aprieta el tornillo de la pinza hasta que cierre sobre la pieza.
3. Retira la herramienta y sal de la zona del brazo.

## 6. Volver a servicio

1. Con la celda despejada, retira tu candado.
2. Conecta la alimentación de los servos.
3. Mira al brazo tomar y dejar una pieza, y confirma que no la suelta.

## 7. Registros

El ajuste hecho, quién aisló y bloqueó, el resultado de la comprobación de energía cero y el de la prueba.
