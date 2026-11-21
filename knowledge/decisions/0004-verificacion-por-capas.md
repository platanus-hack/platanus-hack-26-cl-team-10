# ADR-0004 — Verificación por capas, con lo determinista primero

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

El [planteamiento del equipo](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md) pide que la verificación no dependa solo de un modelo de lenguaje: el sistema recibe la cámara y además sensores (vibración, temperatura y otros), y se organiza en capas, una de ellas determinista.

La evidencia empuja en la misma dirección. Un VLM general detectó 3 de 12 cambios de orden y rechazó 5 de 12 ejecuciones correctas (REFERENCIAS 9). El [ADR-0002](./0002-la-aplicacion-impone-el-orden-de-la-pauta.md) dejó abierta justo esa brecha: cómo comprobar el orden del bloqueo. Y el trabajo más cercano al ciclo completo pone un verificador determinista entre el modelo y la respuesta (REFERENCIAS 25).

## Decisión

Verificamos cada paso con tres capas, y la primera que puede decidir, decide:

1. **Determinista.** Señales de sensores y reglas con marca de tiempo: energía cortada, guarda abierta, temperatura bajo el límite. Decide el orden y todo lo que un sensor puede medir. Un modelo nunca contradice a un sensor.
2. **Aprendizaje automático sobre señales.** Detecta anomalías en vibración o temperatura. El algoritmo está por definir; para el primer disparo basta un umbral.
3. **Modelo de visión y lenguaje, por API.** Responde lo que solo se ve o se redacta: si el candado y la tarjeta están puestos, y el resumen para el relevo de turno.

Cada paso de la pauta declara cómo se comprueba: sensor, cámara o confirmación del operario.

El aviso por audio que interrumpe al operario sale solo de la capa determinista mientras no midamos la tasa de falsas alarmas de la cámara. Lo que detecta la cámara se muestra, pero no interrumpe.

## Alternativas consideradas

- **A — Solo el VLM:** es lo más rápido de armar, pero falla en el orden y da falsas alarmas (REFERENCIAS 9). Un aviso falso en el oído, repetido, enseña al operario a ignorarlo.
- **B — Solo sensores:** es confiable, pero un sensor no ve el candado, la tarjeta ni el estado de una pieza, y obliga a instrumentar cada paso.

## Consecuencias

- El orden del bloqueo deja de depender del modelo: lo dan las marcas de tiempo de los sensores.
- Convertir un procedimiento del cliente en pauta comprobable exige decidir, paso por paso, qué evidencia lo cierra. Es trabajo de entrada por cada tarea.
- En el demo se ve una parte física real: un sensor que corta la discusión sobre si el modelo se equivocó.

## Pendientes y no verificado

- Qué pasos de una tarea minera real tienen una señal de sensor disponible sin tocar el PLC. `Brecha`.
- Qué algoritmo usa la capa 2. `Brecha`.
- La latencia del aviso de punta a punta. Sabetta et al. evaluaron videos completos, no en vivo (REFERENCIAS 9). `Brecha`.
- Si un auricular funciona con la protección auditiva y el ruido de una planta. `Brecha`.

## Referencias

- [Planteamiento del equipo, 2026-11-21](../domain/fuentes/2026-11-21-planteamiento-del-equipo.md).
- REFERENCIAS 9 y 25. REFERENCIAS 11 y 12 detectan el error mientras ocurre; solo se leyó el resumen.
- [ADR-0002](./0002-la-aplicacion-impone-el-orden-de-la-pauta.md) y [ADR-0003](./0003-patrones-de-arquitectura-para-el-mvp.md).
