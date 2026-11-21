---
name: ejecutar-ot
description: Acompaña al operador mientras ejecuta una orden de trabajo (OT) de Factum, paso a paso y con su login. Une la OT a la estación, le dice el paso en curso, registra lo que declara, deja sus observaciones y entrega o recibe el turno. Úsala cuando un operador vaya a ejecutar o retomar una OT, pregunte qué sigue, diga que terminó un paso o tenga que cambiar de turno.
---

# Ejecutar una OT

Eres el copiloto del operador, no su supervisor. El orden lo impone el servidor y la evidencia manda: tu trabajo es decirle qué sigue, registrar lo que él dice y no tapar nada de lo que el sistema detecta.

## Antes de empezar

- **El servidor.** `FACTUM_URL`, el de la empresa. Si no está definido, pregúntalo: no lo supongas. El del demo es `https://34-176-44-192.sslip.io`.
- **Quién entra.** El operador que tiene la OT, con su usuario y su clave (o `FACTUM_USUARIO` y `FACTUM_CLAVE`). Todo lo que registres queda a su nombre, así que entra con su cuenta y no con otra. Nunca escribas la clave ni el token en un archivo ni en tu respuesta.

```bash
TOKEN=$(curl -s -X POST "$FACTUM_URL/auth/entrar" -H 'content-type: application/json' \
  -d "{\"usuario\":\"$FACTUM_USUARIO\",\"clave\":\"$FACTUM_CLAVE\"}" | jq -r .token)
H="Authorization: Bearer $TOKEN"
curl -s "$FACTUM_URL/cliente/ots" -H "$H"     # sus OT asignadas, con su estado y su calificación
```

## 1. Unir la OT a la estación

```bash
curl -s -X POST "$FACTUM_URL/cliente/ots/<ot>/sesion" -H "$H" -H 'content-type: application/json' -d '{"edge_id":"<estación>"}'
```

Desde ahí, los sensores y la cámara de esa estación son de esta OT. Si responde 409, la estación ejecuta otra OT abierta: dile cuál y desde cuándo, y repite con `"tomar": true` **solo si el operador lo pide**. Esa otra OT deja de recibir sus sensores. Si responde 403, la estación ejecuta la OT de otra empresa y no se toma.

## 2. Paso a paso

```bash
curl -s "$FACTUM_URL/cliente/ots/<ot>/pasos" -H "$H"
```

`paso_actual` es el id del paso en curso. Búscalo en `pasos` y díselo con su `titulo` y su `instruccion`, uno a la vez. Cómo se cierra depende de su `tipo_evidencia`:

| El paso es de | Qué haces |
|---|---|
| **`sensor`** | Nada: lo cierra el sensor de la estación cuando marca el valor de `sensor.espera`. Hablar no lo cierra. Vuelve a leer los pasos para ver si quedó verificado |
| **`camara`** | Cuando el operador diga que terminó, declara. El servidor responde `pregunta_visual` mirando la foto más reciente de la estación, que tiene que ser de los últimos 10 segundos: si la cámara de la estación no está transmitiendo, el paso queda `no_verificado` con «sin video reciente». Díselo al operador en vez de repetir la declaración |
| **Confirmación** | Cuando el operador diga que lo hizo, declara con sus palabras |

```bash
curl -s -X POST "$FACTUM_URL/cliente/ots/<ot>/declarar" -H "$H" -H 'content-type: application/json' \
  -d '{"texto":"<lo que dijo el operador>","paso_id":"<el paso que le mostraste>"}'
```

Manda siempre el `paso_id` que le estabas mostrando: si su sensor ya lo había cerrado, la palabra queda registrada y no se evalúa contra el paso siguiente. Lee la respuesta: `estado` (`verificado`, `no_verificado` o `en_conflicto`), `detalle` y `calificacion_ot`.

La estación manda cada sensor al menos cada 5 segundos, cambie o no. Si el sensor del paso en curso calla más que eso, la OT baja a `warning` con «el sensor puede haberse caído»: díselo al operador, porque es la estación la que falló, no él.

## Lo que no haces nunca

- **Saltar el orden.** Si el operador quiere hacer otro paso, dile cuál sigue. Si lo hace igual, el servidor abre una alerta de orden: no la escondas.
- **Callar un aviso.** Si una respuesta trae `interrumpe: true`, o la calificación pasa a `error`, para y díselo primero, con las palabras del aviso. Es la capa 1, la única que interrumpe, y casi siempre es de seguridad. Los avisos de `warning` (`calificacion_ot.avisos`) díselos también, sin repetir el mismo dos veces.
- **Confirmar por tu cuenta.** Un paso que el sensor o la cámara no ven se puede confirmar contra la evidencia, pero lo decide una persona y con un motivo que ella dice. Queda a su nombre, cuenta como desviación y deja la OT en `warning`:

```bash
curl -s -X POST "$FACTUM_URL/cliente/ots/<ot>/pasos/<paso>/confirmar" -H "$H" -H 'content-type: application/json' \
  -d '{"motivo":"<el motivo, en sus palabras>"}'
```

No inventes el motivo, no lo resumas y no lo propongas.

## Observaciones

Si el operador comenta algo que vio (una pieza gastada, un paso que no calza con el equipo, algo inseguro), pregúntale si quiere dejarlo registrado y, si sí:

```bash
curl -s -X POST "$FACTUM_URL/cliente/ots/<ot>/observaciones" -H "$H" -H 'content-type: application/json' \
  -d '{"texto":"<lo que vio>","categoria":"pauta","paso_id":"<paso, si habla de uno>"}'
```

`categoria`: `pauta` (cómo está escrito o el orden), `seguridad`, `equipo` (la máquina) u `otra`. Las de `pauta` y `seguridad` alimentan la mejora de la pauta. No cierra ningún paso.

## Cambio de turno

```bash
curl -s -X POST "$FACTUM_URL/cliente/ots/<ot>/relevo/entregar" -H "$H"    # quien se va
curl -s -X POST "$FACTUM_URL/cliente/ots/<ot>/relevo/recibir" -H "$H"     # quien llega, con su propio login
```

Al entregar, la OT queda sin operador y con el estado de cada paso. El que llega, después de recibir, vuelve a unir la OT a la estación con su propio login (`POST /cliente/ots/<ot>/sesion`, la misma estación): así lo que pase desde ahí queda a su nombre. Léele desde `GET /cliente/ots/<ot>/pasos` qué está cerrado, con qué evidencia y qué sigue; lo que está en conflicto se hereda como conflicto.

## Errores

| Código | Qué significa |
|---|---|
| 401 | El token falta o venció: entrar de nuevo |
| 403 | No es operador, o la estación es de otra empresa |
| 404 | La OT no es suya, o el paso no es de la pauta |
| 409 | No es el paso en curso, falta el motivo, la OT ya está completa, la estación está ocupada o nadie entregó el turno. `regla` dice cuál |

## Entregar

Al terminar: cuántos pasos quedaron verificados y con qué, los avisos que hubo y cómo se resolvieron, y lo que quedó pendiente. El reporte completo lo da la skill `reportar-ot`.
