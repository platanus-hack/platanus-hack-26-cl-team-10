---
name: pedir-ot
description: Pide una orden de trabajo (OT) en Factum desde una pauta habilitada para la empresa y la deja asignada a un operador, con el login del supervisor. Úsala cuando pidan abrir, generar o programar una OT, asignar un trabajo a un operador, o cuando un calendario de mantención o una falla tenga que disparar una OT.
---

# Pedir una OT

Una OT siempre nace de una pauta aprobada que sale de un protocolo. Esta skill no crea protocolos ni pautas: esas las carga el equipo de Factum. Si la pauta que hace falta no está, se termina acá y se le dice a la persona.

## Antes de empezar

- **El servidor.** `FACTUM_URL`, el de la empresa. Si no está definido, pregúntalo: no lo supongas. El del demo es `https://34-176-44-192.sslip.io`. Cada ruta, con su cuerpo y un ejemplo, está en `$FACTUM_URL/referencia/clientes.json`.
- **Quién entra.** Un supervisor de la empresa: solo el supervisor pide y asigna. El usuario y la clave los da la persona, o vienen en `FACTUM_USUARIO` y `FACTUM_CLAVE`. Nunca escribas la clave ni el token en un archivo, en un commit ni en tu respuesta.

```bash
TOKEN=$(curl -s -X POST "$FACTUM_URL/auth/entrar" -H 'content-type: application/json' \
  -d "{\"usuario\":\"$FACTUM_USUARIO\",\"clave\":\"$FACTUM_CLAVE\"}" | jq -r .token)
H="Authorization: Bearer $TOKEN"
curl -s "$FACTUM_URL/yo" -H "$H"     # quién entró y de qué empresa; tiene que decir "rol": "supervisor"
```

## 1. Elegir la pauta

```bash
curl -s "$FACTUM_URL/cliente/pautas" -H "$H"
```

Son las que la empresa puede pedir: habilitadas, aprobadas y con su protocolo. Elige por lo que la persona describió: el `equipo` sobre el que se hace y la tarea del `nombre`, no el parecido del id. Si dos sirven, pregunta. Si ninguna sirve, no pidas una parecida: dile qué pautas hay y que la que falta la carga el equipo de Factum.

## 2. Pedir la OT

```bash
curl -s -X POST "$FACTUM_URL/cliente/ots" -H "$H" -H 'content-type: application/json' -d '{"pauta_id":"<pauta>"}'
```

Sale de la última versión aprobada. Sin `ot_id`, el servidor le pone uno; mándalo solo si el sistema del cliente ya numera sus órdenes. La respuesta trae la OT, la versión y los protocolos de donde sale.

## 3. Asignarla

```bash
curl -s "$FACTUM_URL/cliente/operadores" -H "$H"
curl -s -X POST "$FACTUM_URL/cliente/ots/<ot>/asignar" -H "$H" -H 'content-type: application/json' -d '{"operador":"<id>"}'
```

A quién asignar lo decide la persona. Si no lo dijo, pregunta: no elijas por carga ni por historial, porque Factum no compara personas.

## Cuando la dispara un calendario o una falla

Es la misma llamada. Lo que cambia es quién la hace: el planificador del cliente en su fecha, o quien ve la falla. Si el disparo es una falla, dilo en tu respuesta, con lo que la mostró; la OT no guarda el motivo del disparo.

## Errores

| Código | Qué significa | Qué hacer |
|---|---|---|
| 401 | El token falta o venció | Entrar de nuevo |
| 403 | Quien entró no es supervisor, la pauta no está habilitada o el operador es de otra empresa | Decírselo a la persona; no reintentes con otro usuario |
| 404 | La OT no existe para esta empresa | Revisar el id |
| 409 | La pauta no tiene versión aprobada, el `ot_id` ya existe, la OT está completa o ya tiene operador | El cuerpo (`regla`) dice cuál |

## Entregar

La OT, la pauta con su versión, los protocolos de donde sale y a quién quedó asignada. Si el operador va a ejecutarla con un agente, el siguiente paso es la skill `ejecutar-ot`.
