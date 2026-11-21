# La API frente a los estándares

> Qué servicios tiene la API, cómo entra cada quien y en qué cumple o no cumple lo que piden los estándares de una API de este tipo. Revisado el 2026-11-21 contra el código de `main` y contra la VM del demo. El detalle de cada ruta no está acá: está en la referencia que sirve el servidor, en `/referencia`.

## Dónde está la documentación

- **`/referencia`**: la referencia para leer y probar, hecha con Scalar (REFERENCIAS 73). Trae dos documentos: «Para clientes», con el recorrido y solo lo que usa una empresa, y «Completa». Se arma en [`app/referencia.py`](../../app/referencia.py) desde las rutas reales.
- **`/openapi.json`** y **`/referencia/clientes.json`**: los mismos dos documentos en OpenAPI 3.1 (REFERENCIAS 67), para generar clientes o importarlos en otra herramienta.
- **`/agente`**: la guía en Markdown para un agente, con los WebSocket y el video, que OpenAPI no describe.

`tests/test_referencia.py` compara la referencia con el servidor: lo que declara token responde 401 sin token, cada error declarado se provoca y cada ejemplo tiene la forma de la respuesta real. `Confirmada`.

## Quién usa qué

| Servicio | Quién | Cómo entra | Qué hace |
|---|---|---|---|
| Entrar y Cliente (`/auth`, `/yo`, `/cliente`) | Las personas de una empresa cliente | Token Bearer de `POST /auth/entrar`, 12 horas | El supervisor pide OT de una pauta habilitada y las asigna. El operador ve las suyas y las une a una estación |
| Mejora continua y métricas (`/cliente/...`) | El operario observa; el supervisor valida y mide | Token Bearer; las métricas y las propuestas, solo supervisor | Observaciones, propuestas de mejora de la pauta con su validación, y métricas por pauta, equipo, paso y día ([ADR-0014](../decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)) |
| Ejecución de la OT (`/ot/{id}/...`) | El operario, desde la interfaz | Nada | Estado por paso, declarar, confirmar, relevo y bitácora |
| Estación (`/edge`, `/sensores`, `/sesiones`) | El edge y la interfaz | Nada, salvo la clave del equipo para quitarle una estación a otra OT | Lecturas, video y la sesión que une estación y OT |
| Interno (`/interno`) | El equipo de Factum | Clave del equipo en `X-Clave-Equipo` | Protocolos, pautas, aprobaciones, empresas, personas y qué pautas tiene cada empresa |
| Abiertas del demo (`/pautas`, `/ots`, `/ot/{id}/abrir`) | La pantalla del demo y el banco `/casos` | Nada | Crear pautas y abrir OT sin protocolo ni empresa |

La cadena protocolo → pauta → OT se cumple en el servicio para clientes: `POST /cliente/ots` exige una pauta habilitada para la empresa, aprobada y atribuida a un protocolo ([ADR-0011](../decisions/0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md)). Un cliente no puede crear protocolos ni pautas. Las rutas abiertas del demo se la saltan.

## Lo que hay que decidir

Ordenado por lo que más pesa. Cada punto dice cómo se comprobó.

1. **Ejecutar una OT no pide login.** El login cubre pedir, asignar, listar y unir la OT a una estación. Declarar un paso, confirmarlo, entregar el turno y leer la bitácora van por `/ot/{id}/...`, sin token: quien llama escribe quién es en `actor`, y sirve para la OT de cualquier empresa. Así lo usa hoy la interfaz (`web/src/api/cliente.ts`, en la rama `feat/front-y-servicios`). Además, `GET /ots` lista las OT de todas las empresas: en la VM devolvió 38 sin token, entre ellas las 15 del cliente del demo. Es la falla que OWASP pone primera, la autorización por objeto (REFERENCIAS 71, API1). `Brecha`, ya anotada en el [ADR-0012](../decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md). Cerrarla pide rutas de ejecución dentro de `/cliente`, que tomen al `actor` del token, y que la interfaz las use.
2. **Las rutas abiertas del demo rompen la cadena.** `POST /pautas`, su aprobación y `POST /ot/{id}/abrir` crean una pauta sin protocolo y abren una OT sin empresa, sin pedir nada. Es la autorización por función (REFERENCIAS 71, API5). `Brecha`, anotada en el ADR-0011. Cerrarlas obliga a que la pantalla del demo y el banco `/casos` manden la clave del equipo.
3. **El login no frena a quien prueba claves.** No hay límite de intentos, y el tiempo de respuesta delata si un usuario existe: con uno que existe el servidor deriva la clave (20 ms en local); con uno que no existe responde en 0,01 ms. Corresponde a la autenticación rota (REFERENCIAS 71, API2). `Brecha`. El segundo punto se cierra derivando siempre.
4. **Los errores tienen tres formas.** Los propios traen una llave que dice la clase (`login`, `permiso`, `no_existe`, `regla`, `clave`, `cuadro`); los que lanza FastAPI traen `detail` con un texto, y los de validación, `detail` con una lista en inglés. El estándar es un solo formato, `application/problem+json` con `type`, `title`, `status` y `detail` (REFERENCIAS 68). `Brecha`. Cambiarlo rompe a la interfaz, que hoy lee esas llaves.

## Contra cada estándar

| Tema | Qué pide | Cómo está | Estado |
|---|---|---|---|
| Documento de la API | OpenAPI con esquemas de seguridad y grupos (67) | `/openapi.json` 3.1 con `Token` (http bearer), `ClaveEquipo` (apiKey en cabecera), nueve grupos y un nombre único por operación | `Confirmada` |
| Mandar el token | `Authorization: Bearer <token>` (69, 2.1) | Así entra, y la cabecera ya no figura como parámetro suelto, que OpenAPI manda ignorar (67) | `Confirmada` |
| 401 con desafío | Un 401 lleva `WWW-Authenticate` (70, 15.5.2; 69, 3) | El del login lo lleva (`Bearer`). El de la clave del equipo no | `Brecha` menor |
| Ocultar lo ajeno | Se puede responder 404 en vez de 403 para no confirmar que algo existe (70, 15.5.4) | Una OT de otra empresa responde 404 | `Confirmada` |
| Conflicto con el estado | 409 con información para reconocer el conflicto (70, 15.5.10) | Cada regla de negocio responde 409 y dice cuál es | `Confirmada` |
| Transporte | Con token Bearer, siempre TLS (69, 5.3) | La VM redirige HTTP a HTTPS con 308. No manda `Strict-Transport-Security`. En local va sin TLS | `Confirmada` en la VM |
| Vida del token | Limitada; se recomienda una hora o menos (69, 5.3) | 12 horas, un turno. No se renueva, se cierra con `POST /auth/salir` y se guarda como SHA-256 | `Candidata a validar` |
| Autorización por objeto | Comprobar en cada ruta que el objeto es de quien pide (71, API1) | `/cliente` lo hace y está probado. La ejecución y las listas abiertas, no | `Brecha` (punto 1) |
| Autorización por función | Separar lo administrativo de lo común (71, API5) | `/interno` pide la clave del equipo en cada llamada. Las abiertas del demo, no | `Brecha` (punto 2) |
| Autenticación | Que no se pueda adivinar ni suplantar (71, API2) | Clave con PBKDF2-SHA256 y sal propia, y el mismo mensaje para usuario o clave incorrectos. Sin límite de intentos y con diferencia de tiempo | `Brecha` (punto 3) |
| Consumo | Limitar lo que un pedido puede gastar (71, API4) | El video tiene tope: 2 MB por cuadro, 20 por segundo y 8 edges. Las listas no paginan, y `GET /cliente/ots` calcula la calificación de cada OT. No hay límite de pedidos | `Brecha` |
| Inventario | Documentación al día de todo lo expuesto (71, API9) | La referencia sale de las rutas, y la prueba falla si una ruta queda sin grupo. `/docs` y `/redoc` siguen publicados | `Confirmada` |
| Formato de error | `application/problem+json` (68) | Tres formas | `Brecha` (punto 4) |
| Versión | Una API comparable del rubro la lleva en la ruta, `/v1` (72) | Sin versión en la ruta. `info.version` dice 0.1.0 | `Candidata a validar` |
| Clave visible una vez | La misma API comparable muestra la llave solo al generarla (72) | La clave de una persona se ve una sola vez, al crearla o cambiarla | `Confirmada` |

Tres observaciones que no salen de una referencia, sino de correr el servidor:

- **La validación corre antes que el login.** `POST /cliente/ots` sin token y con el cuerpo mal formado responde 422, no 401. Quien no entró recibe igual la descripción del cuerpo esperado. `Brecha` menor: se corrige leyendo el token en una dependencia y no dentro de la ruta.
- **Las respuestas no tienen esquema.** Las rutas devuelven `dict`, así que OpenAPI las declara como un objeto cualquiera. La referencia lo suple con un ejemplo real en las 13 rutas que usa un cliente. Para generar un SDK hacen falta modelos de respuesta. `Brecha`.
- **Los nombres no son parejos.** Conviven `/ot/{id}` y `/ots`, y `actor` va en el cuerpo al declarar y en la URL al entregar el turno. No rompe nada; conviene emparejarlo cuando se cierre el punto 1.

## Referencias

- Código: [`app/referencia.py`](../../app/referencia.py), `app/referencia_ejemplos.json`, `tests/test_referencia.py` y las rutas de [`app/api.py`](../../app/api.py).
- Estándares: [REFERENCIAS](../projects/research/REFERENCIAS.md#construcción-de-la-api), 67 a 73.
- Decisiones: [ADR-0011](../decisions/0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md) y [ADR-0012](../decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md).
