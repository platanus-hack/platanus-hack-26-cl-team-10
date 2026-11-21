# Ajuste de pinza en brazo robótico

> Redactado por el equipo de Factum para el demo del ADR-0010; no es el procedimiento de una operación real. La norma de seguridad de celdas robotizadas que lo respalda no se buscó: `Brecha`.

## 1. Alcance

Ajuste de la pinza del brazo BR-01 cuando suelta la pieza, dentro de su celda. Aplica junto con el protocolo de aislamiento y bloqueo de energías.

## 2. Trabajar seguro

- **El peligro.** Que el brazo se mueva con una persona dentro de la celda.
- **El control.** Nadie entra a la celda con el brazo energizado. La energía se corta y se bloquea antes de acercarse.
- **La celda.** Tiene un solo costado abierto, vigilado.

## 3. Antes de empezar

1. Avisa que el brazo sale de servicio.
2. Ten a mano la herramienta de ajuste.

## 4. Procedimiento

1. Abre el interruptor de los servos y comprueba que el brazo quedó sin energía.
2. Pon el candado y la tarjeta en el interruptor.
3. Con la energía cortada y el bloqueo puesto, entra a la celda.
4. Aprieta el tornillo de la pinza hasta que cierre sobre la pieza.

## 5. Volver a servicio

1. Retira la herramienta y sal de la zona del brazo.
2. Con la celda despejada, saca el candado y la tarjeta.
3. Cierra el interruptor de los servos.
4. Mira al brazo tomar y dejar una pieza, y confirma que no la suelta.

## 6. Registros

El ajuste hecho, quién lo hizo, y el resultado de la prueba.
