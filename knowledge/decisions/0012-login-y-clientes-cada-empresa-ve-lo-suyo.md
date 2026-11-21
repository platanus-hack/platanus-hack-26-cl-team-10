# ADR-0012 — El servicio para clientes pide login, y cada empresa ve solo lo suyo

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

Con el [ADR-0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md), el servicio para clientes generaba OT, pero no sabía quién las pedía. `GET /cliente/ots` devolvía las OT de todos, el solicitante era un texto libre que cualquiera podía escribir, y los operadores eran dos nombres fijos en el código. Francisco pidió habilitar el servicio con login y dar acceso a una minera ficticia, Oculta.

## Decisión

El servicio para clientes (`/cliente/...`) pide login. Una persona entra con usuario y clave en `POST /auth/entrar` y recibe un token que dura 12 horas. Con ese token, el servidor sabe quién pide y de qué empresa es, sin creerle a lo que venga en el cuerpo.

- **Un cliente es una empresa**, con sus personas. Cada persona tiene uno de dos roles: el **supervisor** pide OT, las asigna a operadores de su empresa y ve todas las de su empresa; el **operador** ve las que tiene asignadas.
- **Cualquier persona de la empresa lee el nombre y el rol de las demás** (`GET /cliente/personas`), para que un relevo diga «Ana Rojas» y no `operario:1`. El usuario con que cada una entra no sale: es la mitad del login. La lista de operadores para asignar (`GET /cliente/operadores`) sigue siendo del supervisor.
- **El operador une su OT a una estación con su token, sin la clave del equipo** (`POST /cliente/ots/{ot_id}/sesion`). La interfaz no puede guardar la clave del equipo, porque todo lo que va en el navegador se ve. La autoriza quién es: solo el operador que tiene la OT asignada, y el `operario` de la sesión es quien entró. Una estación libre, o que ejecuta una OT ya completa, se une sin más. Si ejecuta otra OT abierta, el servidor responde 409 y hay que repetir con `tomar` en true, porque esa OT deja de recibir sus sensores: tiene que ser un acto de la persona y no un reintento. La estación que ejecuta la OT de otra empresa no se toma. Decidido por Francisco el 2026-11-21.
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

- Quitarle la estación a una OT no queda en la bitácora de ninguna de las dos: la sesión nueva dice quién la tiene y desde cuándo (`GET /edge/{id}/sesion`), pero no a quién se la quitó. Registrarlo pide un tipo de evento nuevo en `app/contratos.py`. `Brecha`.
- Una estación no es de ninguna empresa: cualquier operador con una OT abierta puede unirla a cualquier estación libre. `Brecha`.
- La pantalla del operador no usa todavía la ruta nueva ni ofrece tomar la estación. `Brecha`, de `web/`.
- Las rutas anteriores (`/ots`, `/ot/{id}`, `/ot/{id}/declarar`, `/ot/{id}/asignar`) siguen abiertas y muestran las OT de todos. Desde el 2026-11-21 la ejecución tiene sus versiones con login en `/cliente/ots/{id}/...` ([PRD de skills](../projects/skills/PRD.md)); falta que la pantalla del demo y el banco las usen, y entonces cerrar las abiertas. `Brecha`.
- No hay límite de intentos de login ni bloqueo por intentos fallidos. `Brecha`.
- El tiempo de respuesta del login delata si un usuario existe: con uno que existe el servidor deriva la clave (20 ms en local, medido el 2026-11-21) y con uno que no existe responde en 0,01 ms. Se cierra derivando siempre. `Brecha`.
- La revisión de la API contra los estándares está en [API](../architecture/API.md): ordena estas brechas y suma el formato de los errores y la validación que corre antes que el login.
- El token vive en la base del servidor: si la base se borra, todos vuelven a entrar. Aceptable para el demo.
- No hay pantalla de login: hoy se entra por la API. La interfaz es de Daniel (`web/`). `Brecha`.
- El servidor del demo solo tiene HTTPS si va detrás del dominio de la VM; sin HTTPS, la clave viaja a la vista. `Candidata a validar` en la VM.

## Referencias

- Código: `app/acceso.py`, las rutas `/auth`, `/yo`, `/cliente` e `/interno/clientes` de `app/api.py`, y `tests/test_acceso.py`.
- [ADR-0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md).
