# PRD — Gestión de OT (módulo de Diego)

**Rama:** `feat/gestion-ot` → PR hacia `feat/front-y-servicios`
**Fuente de verdad:** [`knowledge/architecture/FRONTEND.md`](../../knowledge/architecture/FRONTEND.md). Este PRD baja a tareas solo la parte de gestión; si algo choca, manda FRONTEND.md.
**Estado:** MVP P0, 2026-11-21.

## 1. Problema

El demo empieza y termina en gestión: el supervisor asigna una OT, el operario la abre, entrega el turno a mitad del trabajo y el supervisor la reasigna a otro operario. Sin estas pantallas, la ejecución de Dani (`/ot/:id`) solo se alcanza escribiendo la URL a mano.

## 2. Usuarios

| Usuario | Dispositivo | Qué necesita |
|---|---|---|
| Supervisor (`supervisor:1`) | Computador | Ver todas las OT, saber cuáles piden acción y asignarlas o reasignarlas |
| Operador (OP1 `operario:1`, OP2 `operario:2`) | Celular, con guantes | Ver solo sus OT y entrar a la que toca con un toque |

## 3. Alcance P0

1. **Login falso** (`/login`): se elige un usuario del demo, sin contraseña. Entra al dashboard de su rol. Con sesión activa, redirige directo.
2. **Inicio** (`/`): redirige al dashboard del rol o a `/login`.
3. **Encabezado** con el usuario actual y «Salir», que borra la sesión y vuelve a `/login`.
4. **Dashboard del supervisor** (`/supervisor`):
   - Todas las OT con id, pauta, equipo, estado general, operador, avance (pasos cerrados / total) y acción.
   - Contadores por estado arriba: lo que pide acción se ve primero.
   - **Asignar** las OT `sin_asignar` y **reasignar** las `entregada` a un operador. Es P0: sin reasignar no hay relevo.
   - La lista se actualiza sola cada 5 s y con un botón «Actualizar»: el operador cambia la OT desde otro dispositivo.
5. **Dashboard del operador** (`/operador`):
   - Solo sus OT (`operador === usuario.id`).
   - «Comenzar» (`asignada`) o «Continuar» (`en_ejecucion`): desbloquea el audio con `desbloquearAudio()` de Dani dentro del toque y navega a `/ot/:id`.
   - Las `completa` muestran «Ver resumen», que abre la misma ruta (Dani muestra el cierre).
6. **Estados vacío, de carga y de error** mínimos en ambos dashboards: texto claro y «Reintentar».
7. **Servicio de asignación en el mock**: `POST /ot/:id/asignar` y `asignar()` en el cliente.

## 4. Fuera de alcance

- Todo lo que pasa dentro de `/ot/:id` (ejecución, voz, relevo, briefing, OT completa): Dani.
- Login real, filtros, búsqueda, warns por operario, video del edge, reasignar una OT `asignada` o `en_ejecucion`: P1.
- Backend real: no se toca `app/`. Los contratos que faltan están en la sección 6.

## 5. Estados generales

Los trae la API (`estado_general`). El front no los calcula, salvo un respaldo mientras el back real no los entregue (ver 6).

| Estado | Color (FRONTEND §4) | Supervisor | Operador |
|---|---|---|---|
| `sin_asignar` | roca | «Asignar» | no aparece |
| `asignada` | acción | operador | «Comenzar» |
| `en_ejecucion` | acción | operador y avance | «Continuar» |
| `entregada` | precaución | «Reasignar» | ya no le aparece |
| `completa` | verificado | avance final | «Ver resumen» |

El color nunca va solo: siempre con ícono y texto.

## 6. Contratos con el backend

**Ya existen y se usan:** `GET /ots`, `GET /ot/{id}` (para el avance).

**Faltan en el back real** (el mock los imita; los implementa la capa de servicios de Diego y Dani, coordinando con el equipo de Francisco):

| Qué | Contrato |
|---|---|
| Asignar y reasignar | `POST /ot/{id}/asignar` con `{ "operador": "operario:2" }` → `200` con el `OtResumen` de esa OT. `404 {no_existe}` si la OT no existe. `409 {regla}` si la OT no está `sin_asignar` ni `entregada`, o si `operador` no es un operador conocido |
| Operador y estado en la lista | `GET /ots`: cada OT con `operador: string \| null` y `estado_general` (los 5 de la sección 5) |
| Avance (opcional) | Hoy sale de un `GET /ot/{id}` por OT. Si el back agrega `cerrados` y `total` en `GET /ots`, se ahorra esa llamada |

**Respaldo mientras falten:** si `GET /ots` no trae `estado_general`, el front muestra `completa` o, sin ella, `asignada`/`sin_asignar` según `operador`. Con el back real de hoy (sin `operador`), todas las OT abiertas se ven `sin_asignar` y el operador no ve ninguna: es el bloqueo del demo en vivo.

## 7. Criterio de éxito (sobre el mock)

1. El supervisor entra, ve las tres OT y asigna `ot-14` a OP1.
2. OP1 entra, ve `ot-12` y `ot-14`, toca «Comenzar» y llega a la ejecución sin otro toque.
3. OP1 entrega el turno y vuelve a `/operador`: la OT ya no le aparece.
4. El supervisor la ve `entregada`, la reasigna a OP2.
5. OP2 entra, toca «Continuar» y ve el briefing de Dani.

## 8. Riesgos

- **Back real sin `asignar` ni `operador`:** bloquea el demo en vivo. Ver sección 6.
- **El mock se reinicia al recargar:** el flujo entre usuarios se prueba navegando dentro de la app («Salir» y volver a entrar), no recargando.
- **«Solo sus OT» es un filtro del front**, no un control de acceso.
- **Contra el back real, asignar responde 404** (la ruta no existe) y la UI muestra «No existe» hasta que se implemente el contrato de la sección 6.

## 9. Pendientes conocidos (fuera del P0 entregado)

| Qué | Por qué queda | Cómo se cierra |
|---|---|---|
| Mostrar **quién entregó** una OT `entregada` (FRONTEND §5) | `GET /ots` no trae ese dato y la bitácora solo llega por el stream de cada OT (de Dani) | Agregar `entregada_por` a `GET /ots` en el contrato del back y del mock |
| **Escenarios de gestión** del mock (`vacia`, `mixta`, `ya-asignada`, `ot-ajena`, FRONTEND §9) | Tocan `escenarios.ts` de Dani y los tests ya cubren vacía, 409 y la reasignación | Acordar con Dani si se agregan para ensayar; `ya-asignada` y `ot-ajena` no aplican al demo (un supervisor; `GET /ot/{id}` no recibe actor) |
| **Avance** = `verificado` + `sobrescrito` sobre el total | FRONTEND §8 dice `verificados.length`, que deja fuera lo sobrescrito y hace ver atrasada una OT que avanzó | Confirmar con Dani; es una línea en `gestion/estados.ts` |
