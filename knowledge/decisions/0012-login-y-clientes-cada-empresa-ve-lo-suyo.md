# ADR-0012 — El servicio para clientes pide login, y cada empresa ve solo lo suyo

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

Con el [ADR-0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md), el servicio para clientes generaba OT, pero no sabía quién las pedía. `GET /cliente/ots` devolvía las OT de todos, el solicitante era un texto libre que cualquiera podía escribir, y los operadores eran dos nombres fijos en el código. Francisco pidió habilitar el servicio con login y dar acceso a una minera ficticia, Oculta.

## Decisión

El servicio para clientes (`/cliente/...`) pide login. Una persona entra con usuario y clave en `POST /auth/entrar` y recibe un token que dura 12 horas. Con ese token, el servidor sabe quién pide y de qué empresa es, sin creerle a lo que venga en el cuerpo.

- **Un cliente es una empresa**, con sus personas. Cada persona tiene uno de dos roles: el **supervisor** pide OT, las asigna a operadores de su empresa y ve todas las de su empresa; el **operador** ve las que tiene asignadas.
- **Cada OT queda de la empresa que la pidió.** Una OT de otra empresa no existe para quien pregunta: 404, no 403, para no confirmar que existe.
- **El equipo habilita qué pautas puede pedir cada cliente.** Un cliente ve y pide solo esas.
- **El equipo crea las empresas y sus personas** en `/interno/clientes`, con la clave del equipo. La clave de cada persona la genera el sistema y se ve una sola vez; si se pierde, se genera otra, y eso cierra sus sesiones.
- **Ni la clave ni el token se guardan tal cual.** La clave se guarda derivada con PBKDF2-SHA256 y sal propia; el token, como SHA-256. Todo con la biblioteca estándar de Python.

Oculta queda en la semilla (`datos/ots-semilla.json`) con una supervisora y dos operadores, las ocho pautas habilitadas y sus 15 OT de ejemplo.

## Alternativas consideradas

- **A — Una clave de API por empresa, sin personas:** separa los datos de cada empresa, pero no distingue al supervisor del operador ni deja saber quién pidió cada OT.
- **B — Un proveedor de identidad externo (OAuth, Cognito, Auth0):** es lo que corresponde en producción, pero suma una dependencia y una cuenta que el demo no necesita. El token Bearer de esta decisión se puede reemplazar por uno de ese proveedor sin cambiar las rutas.
- **C — Cerrar también las rutas anteriores (`/ots`, `/ot/{id}/...`):** las usan la pantalla del demo, el monitor y el banco de casos. Cerrarlas ahora los rompe.

## Consecuencias

- Una empresa no puede ver ni pedir lo de otra, y cada OT dice qué persona la pidió.
- Un operador nuevo de un cliente se puede asignar: la regla de asignación acepta los dos del demo y cualquier persona con rol operador.
- La puesta en marcha de un cliente suma un paso del equipo: crear la empresa, sus personas y habilitar sus pautas.

## Pendientes y no verificado

- Las rutas anteriores (`/ots`, `/ot/{id}`, `/ot/{id}/declarar`, `/ot/{id}/asignar`) siguen abiertas y muestran las OT de todos. Hay que llevarlas detrás del login cuando la pantalla del demo lo use. `Brecha`.
- No hay límite de intentos de login ni bloqueo por intentos fallidos. `Brecha`.
- El token vive en la base del servidor: si la base se borra, todos vuelven a entrar. Aceptable para el demo.
- No hay pantalla de login: hoy se entra por la API. La interfaz es de Daniel (`web/`). `Brecha`.
- El servidor del demo solo tiene HTTPS si va detrás del dominio de la VM; sin HTTPS, la clave viaja a la vista. `Candidata a validar` en la VM.

## Referencias

- Código: `app/acceso.py`, las rutas `/auth`, `/yo`, `/cliente` e `/interno/clientes` de `app/api.py`, y `tests/test_acceso.py`.
- [ADR-0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md).
