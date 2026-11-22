---
name: medir-y-mejorar
description: Responde las preguntas del supervisor sobre cómo se están ejecutando los trabajos en Factum (cumplimiento, desviaciones, pautas y pasos que más fallan, tiempos, tendencia) con las métricas de su empresa, y lo guía para validar las propuestas de mejora de sus pautas. Úsala cuando un supervisor pregunte qué pauta o qué paso falla más, si mejoró algo, cuánto se demora un trabajo, o qué propuestas de mejora hay.
---

# Medir y mejorar

Las métricas se leen de la bitácora al pedirlas: no hay un número guardado que se desfase. Agrupan por pauta, equipo, paso y día, **nunca por persona**. La mejora la propone el sistema y la decide el supervisor; tú la explicas, no la decides.

## Antes de empezar

- **El servidor.** `FACTUM_URL`, el de la empresa. Si no está definido, pregúntalo: no lo supongas. El del demo es `https://34-176-44-192.sslip.io`.
- **Quién entra.** El supervisor de la empresa: las métricas y las propuestas son solo suyas. Nunca escribas la clave ni el token en un archivo ni en tu respuesta.

```bash
TOKEN=$(curl -s -X POST "$FACTUM_URL/auth/entrar" -H 'content-type: application/json' \
  -d "{\"usuario\":\"$FACTUM_USUARIO\",\"clave\":\"$FACTUM_CLAVE\"}" | jq -r .token)
H="Authorization: Bearer $TOKEN"
```

## Qué ruta responde cada pregunta

Todas aceptan `desde` y `hasta` (AAAA-MM-DD, según cuándo se abrió la OT).

| Pregunta | Ruta |
|---|---|
| ¿Cómo vamos? | `GET /cliente/metricas` |
| ¿Qué pauta se desvía más? ¿Cuál cumple peor? | `GET /cliente/metricas/pautas?orden=desviaciones` o `orden=cumplimiento` |
| ¿En qué paso falla esta pauta? ¿Qué capa lo cierra y con cuánta confianza? | `GET /cliente/metricas/pautas/<pauta>/pasos?orden=desviaciones` |
| ¿Qué equipo da más problemas? ¿Qué se ha observado de la máquina? | `GET /cliente/metricas/equipos` |
| ¿Mejoró este mes? | `GET /cliente/metricas/serie?intervalo=semana` |
| ¿Qué habría que cambiar en las pautas? | `GET /cliente/mejoras` |

`orden` en pautas y equipos: `desviaciones` (el total de desviaciones, de más a menos), `cumplimiento` (el peor primero), `ots` (las más ejecutadas) o `minutos` (las más lentas). `limite` corta la lista.

## Cómo leer los números

- **Cumplimiento**: la fracción de las OT **completas** que terminaron sin ninguna desviación. Una OT abierta no cuenta, ni a favor ni en contra.
- **Desviación**: una alerta de seguridad, de orden invertido o de control perdido; un paso en conflicto entre la palabra y la evidencia; o un paso que una persona confirmó porque la evidencia no lo vio. Las alertas de señal y de sensor pegado hablan del sensor, no de cómo se trabajó, y van aparte (`sensores`).
- **Evidencia objetiva**: la parte de los pasos que cerró un sensor o la cámara, no la palabra.
- **Por paso**: `cerrado_en_capa` (1 sensor, 2 detector, 3 VLM, `persona`, `palabra`), `confianza` con cuántas veces quedó `bajo_el_umbral`, `intentos_medios` y `segundos_medios` desde el paso anterior. El primer paso no tiene tiempo: la bitácora no sabe cuándo empezó el operario.

Dilo con el número y su base: «2 de 9 OT completas tuvieron desviaciones», no «22 %» solo. Con menos de cinco OT por pauta, dilo: es poca historia para sacar conclusiones.

## Las propuestas de mejora

Hay dos tipos, en `tipo`:

- **`desviacion`**: el mismo paso de la misma versión tuvo señales en dos o más OT: alertas de seguridad, de orden o de control, conflictos, confirmaciones por persona y observaciones de los operarios. Trae su motivo, sus señales, lo que observaron, las OT (`ots`), una sugerencia y cuántos operarios distintos dieron señales (nunca quiénes). `recurrencia` dice si el paso se desvía más que el resto de su pauta: con pocas OT, dos señales pueden ser azar, y entonces dilo. Cuando `recurrencia.en_vivo` es verdadero, Factum ya le avisó al supervisor en la OT de `detectada`.
- **`conformidad`**: la pauta no cumple un control crítico de su protocolo (le falta, va junto con otro en un paso, va en otro orden). No depende de ninguna OT: está desde que se aprobó la versión.

`aplicable` dice si la propuesta trae un cambio de pauta; si no, `por_que_no` dice por qué (un sensor que no ve el paso, un orden que decide el equipo, una escalada).

```bash
curl -s "$FACTUM_URL/cliente/mejoras?estado=abierta" -H "$H"
```

Explícale cada una al supervisor: qué paso, qué se repite y qué sugiere. Si es aplicable, muéstrale el cambio concreto, con el antes y el después de cada paso y las OT que lo respaldan:

```bash
curl -s "$FACTUM_URL/cliente/mejoras/<id>/borrador" -H "$H"   # el id lleva «:» y «@»: va codificado en la URL
```

`comprobacion.valida` dice si el cambio sigue cumpliendo los controles del protocolo, y `redactado_por` si el texto lo escribió el código o el modelo. Entrega el cambio tal cual: no lo reescribas por tu cuenta. **Él decide.** «Aplicar» es aceptar. Cuando lo diga:

```bash
curl -s -X POST "$FACTUM_URL/cliente/mejoras/<id>/revision" -H "$H" -H 'content-type: application/json' \
  -d '{"decision":"aceptar","nota":"<su razón>"}'
```

Descartar pide una nota que diga por qué. Lo aceptado lo lleva el equipo de Factum a la versión siguiente de la pauta, y la aprueba aparte: eso no lo hace el supervisor ni esta skill. Después, la misma propuesta queda `aplicada` y trae `validacion`: si el paso dejó de desviarse en la versión nueva (`mejoro`), si la baja todavía puede ser azar (`sin_evidencia`, con su `p_valor`), si se sigue desviando (`se_repite`) o si todavía nadie la ejecutó (`sin_datos`). Si un cambio no bajó el paso y se sigue desviando, la propuesta de la versión nueva viene con `escalar`: la causa no es el texto de la pauta, y se conversa con la supervisión antes de otra versión.

## Lo que no se hace nunca

- **Métricas por persona.** Si las piden, recuerda que el dato usado para vigilar aumenta la presión de la jefatura, que causa parte de las desviaciones ([Peres, Smith y Sasangohar, 2020](https://acelab.tamu.edu/wp-content/uploads/sites/23/2020/09/1-s2.0-S0950423020305519-main.pdf)), y ofrece el detalle por pauta y por paso.
- **Aceptar o descartar una propuesta por tu cuenta.**
- **Proponer que un control crítico sobra porque se salta seguido.** Que se repita dice que la pauta está mal escrita o es impracticable, no que el paso sobre.

## Errores

401: entrar de nuevo. 403: las métricas y las propuestas son del supervisor. 404: la pauta no está habilitada o la propuesta no es de la empresa. 409: descartar sin nota, o la pauta ya tiene una versión más nueva. 422: un parámetro mal escrito.
