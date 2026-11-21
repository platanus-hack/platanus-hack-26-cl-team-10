# Plan técnico — Gestión de OT

Implementa el [PRD](./PRD.md). Stack y convenciones de `web/` (Vite, React, Mantine, MSW, Vitest, oxlint). Sin dependencias nuevas.

## Archivos

**Nuevos (dueño: Diego), en `web/src/gestion/`:**

| Archivo | Qué |
|---|---|
| `estados.ts` | `estadoDe(ot)` con el respaldo del PRD §6, y por estado: etiqueta, color del tema e ícono |
| `useOts.ts` | Carga `listarOts()` y el avance de cada OT (`leerOt` en paralelo), recarga cada 5 s, expone `recargar()` y `asignar()` |
| `Encabezado.tsx` | Marca, usuario y «Salir» |
| `EstadoBadge.tsx` | Badge con ícono y texto del estado general |
| `PaginaLogin.tsx` | `/login` |
| `PaginaSupervisor.tsx` | `/supervisor`: contadores, tabla y control de asignación |
| `PaginaOperador.tsx` | `/operador`: tarjetas de mis OT |
| `Inicio.tsx` | `/`: redirige según la sesión |
| `*.test.tsx` | Tests de cada página, con MSW y el mundo del mock |

**Compartidos, cambio mínimo:**

| Archivo | Cambio |
|---|---|
| `src/App.tsx` | Rutas `/`, `/login`, `/supervisor`, `/operador` |
| `src/api/cliente.ts` | `asignar(otId, operador): Promise<OtResumen>` |
| `src/api/cliente.test.ts` | Test del cuerpo y la ruta de `asignar` |
| `src/mocks/handlers.ts` | `POST /ot/:id/asignar` con `m.asignar()` (el hueco que dejó Dani) |
| `src/mocks/handlers.test.ts` | Asignar, reasignar una entregada y los 409 |

No se toca `ejecucion/`, `mundo.ts` ni `escenarios.ts`.

## Decisiones

- **Avance = pasos `verificado` o `sobrescrito` sobre el total**, contados de `GET /ot/{id}`. Con 3 OT son 3 llamadas cada 5 s: aceptable para el demo. Si una falla, esa OT se muestra sin avance; la lista no cae.
- **Polling y no WebSocket:** el stream es por OT y es de Dani. Un intervalo de 5 s alcanza.
- **Reglas de asignación en el mock:** solo `sin_asignar` o `entregada`; el operador debe ser un usuario del demo con rol `operador`. Si no, 409 con `regla`, que la UI muestra tal cual.
- **«Comenzar» espera `desbloquearAudio()`** antes de navegar: así `PaginaOt` encuentra el audio activo y abre la sesión sin pedir otro toque. `desbloquear` nunca rechaza.
- **Responsive:** el supervisor ve una tabla en pantallas medianas o más y tarjetas en el celular; el operador siempre ve tarjetas con botones grandes.

## Orden

1. Cliente y handler de `asignar`, con tests.
2. `estados.ts` y `useOts.ts`, con tests.
3. Login, inicio, encabezado y rutas.
4. Dashboard del operador.
5. Dashboard del supervisor.
6. Tests, lint y build; prueba en el navegador con el mock (flujo del PRD §7, celular y escritorio).
7. Revisión independiente, corrección y nueva validación.

## Cómo probar

```bash
cd web
npm ci
NODE_OPTIONS=--no-experimental-webstorage npm test   # Node 25: ver nota
npm run lint && npm run build
VITE_MOCK=1 npm run dev                               # http://localhost:5173/login
```

**Nota sobre Node 25:** trae un `localStorage` propio que tapa al de jsdom y hace fallar todos los tests con `localStorage.clear is not a function`. Con Node 22/24 o con el flag de arriba pasan. No es un problema del código.
