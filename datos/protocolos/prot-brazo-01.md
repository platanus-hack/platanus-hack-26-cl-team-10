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

1. Avisa que el brazo sale de servicio y espera a que termine lo que está haciendo.
2. Ten a mano la herramienta de ajuste y tu candado.

## 4. Bloque A · Dejar el brazo sin poder moverse

Las mismas tres cosas que en cualquier equipo, en este orden (56).

1. **Cortar la corriente del brazo.** Baja el interruptor de los motores del brazo en el tablero de la celda.
2. **Poner tu candado** en el tablero, y la llave contigo. Mientras esté puesto, nadie puede volver a dar corriente.
3. **Probar que no arranca.** Da la orden de partida y mira que el brazo no se mueve.

## 5. Bloque B · Ajustar la pinza

4. **Entrar a la celda.**
5. **Ajustar la pinza.** Aprieta el tornillo hasta que cierre sobre la pieza.
6. **Salir de la celda** con la herramienta.

## 6. Bloque C · Devolver el brazo a trabajar

7. **Sacar tu candado**, con la celda vacía.
8. **Devolver la corriente.**
9. **Probar un ciclo.** Mira al brazo tomar y dejar una pieza, y confirma que no la suelta.

## 7. Registros

El ajuste hecho, quién cortó la corriente y puso candado, si la prueba de partida salió sin movimiento, y cómo salió el ciclo.
