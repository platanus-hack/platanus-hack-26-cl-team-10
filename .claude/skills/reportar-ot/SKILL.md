---
name: reportar-ot
description: Arma el reporte de cierre de una orden de trabajo (OT) de Factum desde su bitácora, o el informe de un periodo desde las métricas, sin omitir ninguna desviación y citando el evento de cada afirmación. Úsala cuando pidan el reporte, el informe, el resumen o la notificación de cierre de una OT, el resumen para un relevo de turno, o el informe semanal o mensual de una empresa.
---

# Reportar

El reporte no se escribe: se lee de la bitácora. El servidor ya lo arma, paso por paso y con la evidencia de cada uno. Tu trabajo es entregarlo, y redactar encima solo si te lo piden, sin cambiar lo que dice.

## Antes de empezar

- **El servidor.** `FACTUM_URL`, el de la empresa. Si no está definido, pregúntalo: no lo supongas. El del demo es `https://34-176-44-192.sslip.io`.
- **Quién entra.** El supervisor de la empresa, o el operador que tiene la OT. El informe de un periodo es solo del supervisor. Nunca escribas la clave ni el token en un archivo ni en tu respuesta.

```bash
TOKEN=$(curl -s -X POST "$FACTUM_URL/auth/entrar" -H 'content-type: application/json' \
  -d "{\"usuario\":\"$FACTUM_USUARIO\",\"clave\":\"$FACTUM_CLAVE\"}" | jq -r .token)
H="Authorization: Bearer $TOKEN"
```

## El reporte de una OT

```bash
curl -s "$FACTUM_URL/cliente/ots/<ot>/reporte" -H "$H"                       # JSON
curl -s "$FACTUM_URL/cliente/ots/<ot>/reporte?formato=markdown" -H "$H"      # listo para leer o adjuntar
```

Lo arma el código, no un modelo. Trae:

- `pasos`: cada uno con su estado, con qué se cerró (`cerrado_con`), su capa, su hora, sus intentos y el `evento` que lo sostiene;
- `desviaciones`, `confirmados_por_persona`, `observaciones` y `relevos`, cada uno con su `evento`;
- `pendientes`, `tiempos` y `resultado`.
- `mejoras`, solo si lo pide un supervisor (para el operario va vacía): las propuestas de mejora de esa pauta y versión en que esta OT aportó, y las de conformidad, cada una con `cambios_resumen`, el cambio a la pauta en una línea por paso («Agrega…», «Separa…», «Reescribe…»). En el Markdown es la sección «Mejoras sugeridas». Son sugerencias: aplicarlas es aceptarlas en la skill `medir-y-mejorar`, y la versión nueva la arma Factum.

Si piden el reporte, **entrega el Markdown tal cual**. No lo resumas por tu cuenta: resumir es elegir qué callar.

## Si te piden redactarlo

Por ejemplo, un párrafo para el jefe de mantención o el resumen para el turno que llega. Va encima del reporte, nunca en su lugar ([LOGICA](../../../knowledge/architecture/LOGICA.md#relevo-de-turno)):

1. Parte del JSON completo, no de lo que recuerdes de la OT.
2. Cada afirmación cita su evento entre paréntesis: «el candado se puso a las 09:41 (evento 812)».
3. **Ninguna desviación queda fuera.** Antes de entregar, compara: cada `evento` de `desviaciones` y de `confirmados_por_persona` tiene que aparecer en tu texto. Si falta uno, agrégalo.
4. Nada que el reporte no diga. Si algo no está (por qué se demoró, qué pensaba el operador), no lo supongas: dilo como pregunta.
5. Un paso confirmado por una persona no es un paso verificado: dilo así, con su motivo.

## El informe de un periodo

Solo el supervisor. Sale de las métricas, que agrupan por pauta, equipo, paso y día:

```bash
curl -s "$FACTUM_URL/cliente/metricas?desde=AAAA-MM-DD&hasta=AAAA-MM-DD" -H "$H"
curl -s "$FACTUM_URL/cliente/metricas/pautas?desde=…&hasta=…&orden=desviaciones&limite=5" -H "$H"
curl -s "$FACTUM_URL/cliente/metricas/serie?intervalo=semana&desde=…&hasta=…" -H "$H"
curl -s "$FACTUM_URL/cliente/mejoras?estado=abierta" -H "$H"
```

Lleva el cumplimiento (OT completas sin desviaciones), las desviaciones por clase, las pautas y los pasos que más se desvían, la tendencia y las propuestas de mejora abiertas. **Un informe de periodo no nombra personas**: Factum mira el paso y la pauta, no a quien lo ejecuta ([ADR-0013](../../../knowledge/decisions/0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md)). Si piden el detalle por operario, recuerda que usar el dato para vigilar aumenta la presión que causa parte de las desviaciones, y ofrece el detalle por pauta.

Cómo leer cada número está en la skill `medir-y-mejorar`, que el servidor publica junto a esta.

## Errores

401: entrar de nuevo. 403: el informe de periodo es solo del supervisor. 404: la OT no es de quien pregunta. 422: una fecha mal escrita o `desde` después de `hasta`.
