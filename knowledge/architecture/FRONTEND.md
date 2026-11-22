# Frontend — alcance y reparto

**Proyecto:** Factum — Platanus Hack 26
**Rama:** `feat/front-y-servicios`
**Módulo de Diego:** gestión y visualización de órdenes de trabajo (OT)
**Módulo de Dani:** ejecución de la OT, avisos y voz
**Estado:** acordado el 2026-11-21 para el MVP. Sale de la pizarra del equipo y de las respuestas de Dani. Lo marcado *(propuesta)* no se discutió: es una decisión razonable que cualquiera de los dos puede cambiar avisando.

## 1. Para qué

El demo tiene que mostrar esto: el supervisor asigna una OT, el operario la ejecuta paso a paso y, cuando la API detecta que un paso no se hizo, **el operario lo oye en el momento**. A mitad del trabajo cambia el turno y otro operario la termina desde donde quedó.

El front no verifica nada. Muestra lo que decide la API, deja al operario responder y hace sonar el aviso. La lógica de verificación es del equipo de Francisco.

## 2. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Stack | Vite + React + TypeScript, en `web/`. Una sola app con pantallas separadas por ruta, no una sola pantalla. React Router para las rutas, Mantine para los componentes, MSW para el mock y Vitest para los tests |
| Login | Real, con correo y clave contra `POST /auth/entrar` ([ADR-0012](../decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md)). Con mock, además, un toque por persona de prueba |
| Datos mientras no hay back | Un mock que imita la forma que la API ya devuelve (`GET /ot/{id}`), más las extensiones de la [sección 8](#8-contrato-con-la-api). El mock es solo para construir |
| Demo en vivo | Corre sobre el back real, con el supervisor en un computador y el operador en un celular. Los warns y la alerta de seguridad los disparan los sensores reales del ESP32 |
| Captura | El front no captura nada. La cámara y los sensores van por el dispositivo de borde, directo a la API |
| Relevo de turno | Entra al MVP. El reporte final y el conteo de warns por operario quedan en P1 |
| Cuándo actúa el operario | Los pasos se cierran solos con su evidencia: el sensor o la cámara del edge. No hay un «Hecho» permanente. El operario solo actúa cuando la API lo necesita: «Hecho» en un paso que se cierra declarando (confirmación, o cámara sin detección), y «Ya lo hice» cuando la API avisa que el paso se saltó, cuando hay un conflicto o cuando la evidencia no llega (decidido por Dani, 2026-11-21) |
| Botón «Ya lo hice» (el *skip* de la pizarra) | No sirve para saltarse trabajo: el operario lo usa para decir que sí lo hizo, aunque la evidencia no lo muestre. Llama a `POST /ot/{id}/pasos/{paso}/confirmar` con un motivo obligatorio. El paso queda verificado por una persona, a su nombre, y la OT queda en `warning`. No sirve en un paso de confirmación, que se cierra declarando, ni apaga una alerta de seguridad, que se resuelve con el sensor |
| Aviso por voz | Cuando la API avisa que un paso no se hizo, el aviso se convierte en voz con ElevenLabs y suena en la app del operario casi al instante. Ver [sección 7](#7-aviso-por-voz-elevenlabs) |
| Endpoints que faltan | Los hacen Diego y Dani después de las pantallas, como capa de servicios, con lo mínimo. No se invierte tiempo en el back: el equipo de Francisco lo va a cambiar |
| Dispositivo | La app del operario se diseña para celular con audífonos, y el celular queda con la pantalla encendida y la app abierta durante todo el trabajo. La del supervisor se diseña para computador |

**Resuelto con el equipo de Francisco.** Hablar sigue sin cerrar un paso de sensor (regla 2 de `/agente`), pero ahora una persona puede confirmarlo explícitamente, con quién y por qué: `POST /ot/{id}/pasos/{paso}/confirmar` (rama `dreamxist/services`, [LOGICA](./LOGICA.md)). «Ya lo hice» usa ese endpoint.

## 3. Reparto

| Diego — Gestión | Dani — Ejecución |
|---|---|
| Login falso y sesión con rol | Vista de ejecución de la OT |
| Dashboard del supervisor | Máquina de estados del paso |
| Dashboard del operador | Alertas, «Hecho» donde hace falta y «Ya lo hice» |
| Listado y display de OT | Aviso por voz con ElevenLabs |
| Asignar y reasignar operador | Entregar turno y briefing del que llega |
| Estado general de la OT (lo trae la API) | Pantalla de OT completa |
| Escenarios del mock de gestión | Base del mock y escenarios de ejecución |

Dani arma la base compartida de la sección 4 en el primer commit, y Diego parte sobre ella *(propuesta)*.

## 4. Base compartida

```
web/
  src/
    api/         tipos.ts y cliente.ts: el único lugar que sabe de la API
    mocks/       handlers de MSW y escenarios
    sesion/      usuario actual y rol
    gestion/     Diego: login, dashboards, listado
    ejecucion/   Dani: vista de la OT, máquina de estados, voz, briefing
```

| Ruta | Quién entra | Dueño |
|---|---|---|
| `/login` | todos | Diego |
| `/supervisor/hoy` | supervisor | Diego |
| `/supervisor` | supervisor | Diego |
| `/operador` | operador | Diego |
| `/supervisor/protocolos` | supervisor | Diego |
| `/supervisor/mejoras` | supervisor | Diego |
| `/supervisor/ot/:id` | supervisor | Dani |
| `/ot/:id` | el operador asignado | Dani |

- `api/` y `sesion/` son compartidos: se avisa antes de cambiarlos. Fuera de eso, cada uno trabaja en su carpeta y no hay choques en la rama.
- El id de la OT viaja en la URL y la sesión (`usuario` con `id`, `nombre`, `rol` y empresa, más el `token` y cuándo `expira`) en `localStorage`, aparte con y sin mock. Con eso el módulo de ejecución sabe quién es el actor. Un token vencido o rechazado (401) cierra la sesión y el login dice «Tu sesión venció».
- Los actores usan el formato de la bitácora: `operario:1`, `supervisor:oculta`. El nombre de cada uno sale de la sesión y, para el supervisor, de `GET /cliente/operadores`; si el front no lo conoce, se lee del id («Operario 2»).
- Personas de prueba: las de la minera ficticia Oculta en la semilla del servidor (`datos/ots-semilla.json`): la supervisora Carla Muñoz y los operadores Ana Rojas (`operario:1`) y Bruno Díaz (`operario:2`). El mock usa las mismas, con la clave `demo`; las claves del servidor no van en el repo.
- Con mock, `?como=operario:1` en la URL entra como esa persona sin pasar por el login. Sin mock no hace nada.
- El mock corre en el navegador con MSW, que también imita el WebSocket: `npm run dev:mock` (o `VITE_MOCK=1`). Sin mock (`npm run dev`), el cliente apunta a `VITE_API_URL`, que por defecto es el servidor del equipo, `https://34-176-44-192.sslip.io`, y lo que se toque ahí lo ven todos.
- Dentro de un navegador, el mock es un solo mundo: lo que el supervisor asigna en `/supervisor` aparece en `/operador` y en `/ot/:id`. El escenario solo fija cómo parte ese mundo, y se elige en la URL: `/ot/ot-12?escenario=warn-sobrescrito`. No cruza dispositivos, y no hace falta: el demo corre sobre el back real.
- Los datos del mock usan la pauta real, [`datos/pauta-correa.json`](../../datos/pauta-correa.json): 6 pasos sobre la correa CT-01.

### Colores

Los colores son los de seguridad industrial (ISO 3864, ANSI Z535): los mismos de los letreros y las tarjetas de bloqueo de una planta, así un operario los lee como ya los lee en terreno. Reglas:

- **Cada color significa una sola cosa.** Rojo es peligro, amarillo es precaución, verde es verificado y azul es acción obligatoria, que en la app es el paso actual y el botón «Hecho».
- **Lo demás es neutro.** Una OT tranquila se ve gris y blanca, con el paso actual en azul. Cuando algo sale mal, la pantalla cambia de color, y eso es lo que se tiene que notar.
- **Sin naranjo.** Queda entre el rojo y el amarillo y confunde los dos avisos.
- **La marca casi no dice estados.** En claro, el lima y la tinta del logo viven solo en la banda de arriba (ver «Marca»). En oscuro, el lima dice además «verificado», como en el monitor: es el único estado que comparte color con la marca.
- **El color nunca va solo.** Siempre va con un ícono y un texto: con sol, con guantes o con daltonismo rojo-verde, el color no alcanza.
- **Claro para el operario, oscuro para el supervisor y el login.** Lo del operario va en claro, que se lee mejor bajo el sol. Lo del supervisor (`/supervisor…`) y el login van en oscuro, con el lenguaje del monitor. Lo decide la ruta, en `App.tsx`; ninguna pantalla sabe en qué esquema está.
- **En oscuro, la paleta del monitor más dos colores.** Lima para lo verificado, ámbar para el aviso y rojo para el peligro. El lima dejó de usarse para todo: **hielo** es lo que se puede tocar y el paso en curso, y **lila** son las propuestas de mejora. Los dos tienen la misma claridad que el lima, así que conviven con él.
- **La saturación es un solo número.** `SATURACION`, en `tema.ts`, dice cuánto color llevan las vistas oscuras y el lima de la marca: 1 es la paleta tal cual y 0 la deja en grises. Hoy va en 0,5, porque la pantalla de la presentación exagera los colores. Baja el croma y deja igual la claridad, así que el contraste no cambia; el rojo del peligro conserva algo más de color (0,65) para seguir siendo lo que más salta. Lo del operario, en claro, no la usa.
- **Cada color tiene cinco usos:** el color, bajo el cursor, el texto que va encima, un fondo teñido y el texto de color. Sus valores cambian con el esquema y están en `tema.ts` (`CLARO` y `OSCURO`). Botones, insignias e íconos los toman de ahí, y en oscuro los tonos de Mantine que las pantallas ya usan (`peligro.6`, `precaucion.0`) siguen esos usos.
- **La alerta de capa 1 se ve como una tarjeta de bloqueo:** una franja roja arriba con «Peligro» en blanco, y el cuerpo blanco con el texto en grafito.

| Token | Hex | Uso |
|---|---|---|
| Grafito | `#1F262E` | Texto principal |
| Roca | `#5B6570` | Texto secundario, bordes y pasos pendientes |
| Polvo | `#EDF0F2` | Fondo de la app |
| Blanco | `#FFFFFF` | Superficies: tarjetas, banner, barra inferior |
| Acción | `#004C97` | Paso actual, «Hecho» y botones principales |
| Verificado | `#00843D` | Paso verificado |
| Precaución | `#FFD100` de relleno, `#7A5C00` para texto | Avisos de nivel `warning` (cámara y anomalías de señal), sin señal, sin conexión y la marca de un paso confirmado por una persona |
| Peligro | `#C8102E` | Lo de nivel `error`: el warn de capa 1 que suena y la alerta de seguridad |

En oscuro, la paleta tal cual, y entre paréntesis como se ve en pantalla con la saturación de hoy:

| Token | Hex | Uso |
|---|---|---|
| Tinta | `#0a0c0a` | Fondo, liso |
| Panel | `#101310` | Celdas y tarjetas |
| Línea | `#252a23` y `#3d4439` | Separadores de celdas y bordes |
| Lima | `#d4ff9e` (`#e1f7c8`) | Verificado, y la marca |
| Hielo | `#9fe3ff` (`#bddeeb`) | Botones principales, enlaces y el paso en curso |
| Lila | `#c8b6ff` (`#c5bde2`) | Propuestas de mejora |
| Ámbar | `#ffc24d` (`#e7c997`) | Avisos de nivel `warning` |
| Rojo | `#ff4433` (`#de6b5c`) | Lo de nivel `error` |

El amarillo de seguridad no se lee como texto sobre blanco (1,5:1): va siempre de relleno con texto grafito (10,5:1), y el texto amarillo usa `#7A5C00` (6,3:1). Los demás pasan AA con texto blanco: rojo 5,9:1, verde 4,8:1, azul 8,5:1.

**Ejecución:** `pendiente` roca · `en_curso` y `comprobando` acción · `verificado` verificado · `warn` peligro si es capa 1 y precaución si no · `sin_senal` precaución · `confirmado` verificado con un borde izquierdo de precaución, porque está cerrado pero cuenta como warn.

**Gestión:** `sin_asignar` roca · `asignada` y `en_ejecucion` acción · `entregada` precaución, porque espera al supervisor · `completa` verificado.

### Marca

El logo es `project-logo.png`: una cruz lima y «Factum» en matriz de puntos, sobre tinta. Es el mismo del monitor de Jona.

- **`<Marca>`** (`web/src/Marca.tsx`) lo dibuja en SVG, calcado del PNG punto por punto: no depende de que cargue una letra. La cruz y el nombre van siempre juntos; la cruz sola en una barra se lee como un botón de «agregar».
- **El menú del supervisor** lo abre el logo: un panel a la izquierda que empuja la página (no la tapa; en el celular, sí), con Hoy, Órdenes de trabajo, Protocolos, Mejoras y, al pie, el nombre y «Salir». La cruz gira hasta ser una ×, y Escape lo cierra. El operario no tiene menú: su nombre y «Salir» siguen en la banda.
- **Vive sobre tinta, y solo arriba.** La banda de arriba (`Encabezado` y `BarraOt`) y el panel del login son tinta. Lo de trabajo va debajo: en claro para el operario y en oscuro para el supervisor, donde una línea separa la banda. `SOBRE_TINTA` en `tema.ts` trae el fondo, el texto y el foco del teclado en lima, porque el azul no se ve sobre tinta.
- **La letra** es Bitcount Prop Single, servida por el front (`@fontsource-variable/bitcount-prop-single`). Desde el 2026-11-22 va solo en el logo y en el login, en la frase «Cada paso verificado queda como un hecho.»: en las pantallas de trabajo, los títulos y los valores van en la letra del texto, que se lee más limpio.
- **El favicon** (`web/public/favicon.svg`) es la cruz lima sobre tinta, con el trazo más grueso que en el logo para que se lea a 16 px.

| Token | Hex | Uso |
|---|---|---|
| Tinta | `#0a0c0a` | Fondo de la banda de arriba y del panel del login |
| Lima | `#d4ff9e` | La cruz del logo y el foco del teclado sobre tinta |
| Hueso | `#eef2e9` | «Factum» y el texto sobre tinta |
| Tenue | `#9ca696` | Texto secundario sobre tinta |

El tema vive en `web/src/tema.ts`, con los colores, sus usos por esquema, las letras y los radios. Nadie escribe un hex fuera de ahí; las dos excepciones son archivos que no pueden importarlo, `favicon.svg` y el `theme-color` de `index.html`.

### El lenguaje del monitor

Las vistas del supervisor y el login se ven como el monitor de Jona (`app/estatico/monitor.html`). Sus clases están en `web/src/gestion/industrial.module.css`:

- **Rótulos chicos** en mayúsculas monoespaciadas (la ficha de la OT, el estado de cada paso). El título de una sección va en la letra del texto, sin corchetes, con su número a la derecha.
- **Celdas, no tarjetas:** grupos de datos separados por una línea de 1 px (la ficha de la OT, los sensores).
- **Títulos, valores y botones** en la letra del texto, con mayúscula inicial. Desde el 2026-11-22 ya no van en la letra de puntos ni los botones en mayúsculas monoespaciadas, y el fondo no lleva trama: Pancho pidió bajar el ruido.
- **Una sola etiqueta por OT:** la verificación, con el motivo al pasar el cursor. Una OT sin asignar dice solo su estado.
- **Esquinas casi rectas:** ningún radio pasa de unos pocos píxeles, en toda la app.
- **El video** lleva esquineros de visor que toman el color de la verificación, y el paso en curso encima.
- **Los pasos van numerados** (`01`, `02`), con su estado a la derecha.

El operario conserva su fondo claro y sus colores ISO. De este lenguaje toma solo las formas y las insignias, que salen del tema.

## 5. Diego — gestión

**Login.** Correo y clave; al entrar va a su dashboard según el rol, y el encabezado dice su nombre y su empresa. Si la clave no calza lo dice ahí mismo; si el servidor no responde, también. Con mock, abajo hay un toque por persona de prueba.

**Pedir OT.** El supervisor elige una de las pautas de su empresa y la OT aparece por asignar, con un aviso de cuál pidió.

**Hoy (`/supervisor/hoy`).** La portada del supervisor, adonde lleva el login. Arriba, los incidentes en curso (una línea por OT en «detente», con su campana). Después cuatro números: en curso, con alerta, por asignar y completas hoy (de `GET /cliente/metricas?desde=` el día del supervisor). Debajo, «En curso ahora», hasta 8 OT que corren, lo que avisa primero, con el operario, el paso y el avance, y «Ver todas las OT»; y «El día» en frases: cuántas completas salieron sin desviaciones, cuántas desviaciones y de qué tipo, cuánto se tarda en corregir una y cuánto dura una OT. Al final, el aviso de mejoras de Factum.

**La lista (`/supervisor`, «Órdenes de trabajo»).** Pensada para cientos de operarios y OT: arriba «Pedir OT» y una sola tabla (`TablaOts`), una fila por OT: cómo va, la OT, el operario, la pauta, el avance con el paso en curso, y para las que se pueden asignar un selector con búsqueda («Asignar a…», o «Reasignar a…» si se entregó el turno), que sirve igual con dos operarios que con cientos. Lo que avisa va primero («Detente», después «Atención»), después lo que corre, lo que falta asignar y lo que está por empezar. Filtros: «Activas», «Con alerta», «Por asignar» y «Completas», cada uno con cuántas tiene; las completas no ensucian la vista del día. Un buscador por OT, operario o pauta, y páginas de 25. Un clic en cualquier parte de la fila abre su vista en vivo. La lista se recarga sola cada 2 s y apenas la pestaña vuelve a estar a la vista; no hay botón para recargar. Para mostrar el paso en curso, la lista lee el estado de las OT que corren ahora; las demás no se piden una por una. El supervisor ve todas las de su empresa: la API no distingue a qué supervisor pertenece cada una.

**Fila encendida.** Si la estación avisa algo en una OT abierta, su fila se enciende y su etiqueta da el motivo más grave al pasar el cursor: amarillo para «Atención» (la cámara o una señal dudan) y rojo para «Detente». Lleva una franja a la izquierda y el fondo teñido, además del ícono y el texto, porque el color nunca va solo. Una OT completa no se enciende.

**Verificación.** Cada OT de la lista dice cómo va lo que Factum verifica: «Todo bien», «Atención» o «Detente», con ícono y texto. La trae `GET /cliente/ots` en cada OT (`calificacion`), sin una llamada por OT. Las sin asignar no la muestran.

**Incidentes.** Una OT abierta en «Detente» es un incidente. Arriba de la lista aparece una barra roja con una línea por cada uno (OT, operador y el motivo más grave, en pocas palabras) y «Ver», que abre su vista en vivo. Cuando aparece uno nuevo suena una campana corta (Web Audio, sin archivos); los que ya estaban al entrar no suenan. El supervisor solo mira: no confirma ni detiene nada.

**Vista en vivo (`/supervisor/ot/:id`).** Se llega desde la barra de incidentes, desde la fila de la OT o desde su id. Trabaja como el monitor de Jona y, como todo lo del supervisor, va en oscuro.

- **Arriba,** una flecha para volver a la lista, el número de la OT y el nombre de la pauta. Las alertas abiertas van en una etiqueta roja chica a la derecha (el título de la alerta, o «N alertas»); al tocarla se abre el detalle de cada una: qué pasa, desde cuándo, qué hacer y «Ver en la bitácora». Una alerta resuelta sigue 3 s, en gris, para que la pantalla no parpadee. Una anomalía de un sensor se dice en palabras («Distancia 148.9 cm fuera de lo normal: lo habitual es 102 cm», `app/scoring.py`).
- **A la derecha, siempre a la vista, los pasos;** debajo, plegados, «Detalles» (la ficha: quién la ejecuta, en qué estación y desde cuándo, el equipo y el estado) y «Sensores». La verificación, junto al video, tampoco se pliega.
- **Cámara.** El video de la estación (`GET /edge/{edge}/video.mjpg`, el que el edge manda al servidor). Encima va lo que la cámara reconoce, en cajas: blancas si está segura (80 % o más) y amarillas si duda; se borran si pasa 1 s sin detecciones. También el paso en curso, y el marco toma el color de la verificación. Si la OT no corre en una estación, lo dice.
- **Verificación.** «Todo bien», «Atención» o «Detente», en grande y con su color, y por qué lo dice: cada aviso activo de `calificacion.avisos`, quién lo dice (el sensor o la cámara) y con cuánta certeza. Es lo que explica una fila encendida de la lista.
- **Sensores** (plegados; el título trae cuántos), una ficha por sensor: los de la pauta de esta OT y los que están leyendo ahora (el servidor recuerda sensores de todas las estaciones, y esos no se muestran). El que espera el paso en curso va primero y marcado, y solo una lectura de ahora cuenta como «ya está». Lo que solo trajo el snapshot dice «Última lectura guardada» y va en gris hasta que llega una nueva. Un sensor numérico muestra su unidad y una línea con sus últimas 90 lecturas, para ver hacia dónde va (la temperatura que baja mientras se espera).
- **Pasos,** numerados y con su estado a la derecha: verificado en lima, en curso en hielo. Un paso en conflicto va en rojo solo si lo dice el sensor; la duda de la cámara va en ámbar.
- **Bitácora** completa, abajo y a todo el ancho, lo último arriba.

Todo llega por el mismo WebSocket de la OT que usa la ejecución, pero esta vista no abre sesión ni declara: mirar no cambia la bitácora.

**La propuesta, al terminar la OT.** El servidor calcula las propuestas de mejora al leer la bitácora ([ADR-0014](../decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md)): una nace cuando el mismo paso de la misma versión tiene señales en dos OT, y las de conformidad nacen de la pauta misma, sin OT ([LOGICA](./LOGICA.md#cuándo-el-sistema-propone-cambiar-la-pauta)). La vista vuelve a pedir `GET /cliente/mejoras` con cada evento del stream, pero no muestra nada mientras la OT corre: ahí lo que importa es la alerta. Cuando la OT se completa aparecen, bajo el aviso de OT completa, las propuestas abiertas de esa pauta y versión en las que esta OT dio señales, con «Revisar la propuesta». Dice «Con esta OT nació una propuesta» si no existía al abrir la pantalla. Qué cuenta como señal está en `api/mejoras.ts`, igual que en `app/mejora.py`: una alerta de seguridad cuenta en el paso que estaba en curso cuando se dio el peligro (`evidencia.paso`), así que acercarse con el motor encendido cuenta en «Apagar el motor».

Esa espera la pone la pantalla, no el servidor: `app/mejora.py` cuenta también las OT en ejecución, así que la página de mejoras puede mostrar la propuesta antes de que la OT termine. `Brecha`.

**Reporte de la OT.** El selector «Ejecución / Reporte» cambia la vista en vivo por el reporte que arma el servidor desde la bitácora (`GET /cliente/ots/{id}/reporte`): cuántos pasos se verificaron y, justo debajo, para el supervisor, «Qué cambiaría Factum en la pauta»: las mejoras en que esta OT aportó y las de conformidad de su pauta, cada una con su cambio en una línea («Agrega «Comprobar energía cero» después de «Poner tu candado»»), «Por qué» y «Cómo se sabrá si funcionó», escritos para quien conoce el trabajo y no la estadística (`porque` y `como_se_mide`, de `sugerencias.para_una_persona`), y un enlace a `/supervisor/mejoras`. Después, qué cerró cada paso (el sensor con su lectura, la cámara con su certeza, una persona contra la evidencia, o la palabra del operario), a qué hora y cuánto tardó; las desviaciones, juntas cuando se repiten en el mismo paso y plegadas («Señal fuera de lo normal, en el paso 4 · 9 veces»), con lo que tardó en corregirse cada una; y lo que observó el operario. Los avisos de anomalía viejos de la bitácora («dist_cm = 148.9, lejos de su mediana…») se muestran en palabras (`enPalabras`, en `sensores.ts`). Al operario el reporte le llega sin mejoras. Una OT que ya estaba completa se abre en su reporte. Si se completa mientras se mira, aparece «Ver el reporte». Sirve también para una OT en curso: se vuelve a pedir con cada evento.

**Protocolos (`/supervisor/protocolos`).** Cada protocolo de la empresa con sus pautas (de `GET /cliente/pautas`, agrupadas por `protocolos`; una pauta de dos protocolos va en los dos), y de cada pauta su versión, sus pasos, el equipo y cómo van sus OT («2 en curso · 1 con alerta · 5 completas»). «Ver sus OT» abre la lista filtrada por esa pauta (`/supervisor?pauta=…`), con una etiqueta «Pauta: …» que se quita con su ×. Un buscador por protocolo, pauta o equipo.

**Mejoras (`/supervisor/mejoras`).** Una sección del menú del supervisor. Arriba, cuatro números de `GET /cliente/metricas`: OT completas, cuántas sin desviaciones, qué parte de los pasos se cerró con sensor o cámara y cuántas propuestas esperan revisión. Debajo, las propuestas: el paso, en cuántas OT dio señales, qué señales, qué revisar y lo que observaron los operarios. Nunca nombra a una persona. «Ver el cambio» pide el borrador (`GET /cliente/mejoras/{id}/borrador`) y muestra, por paso, el antes y el después, por qué con las OT que lo respaldan, y si el validador lo aprueba. Si la propuesta trae un cambio que aplicar, el botón dice «Aplicar»; si no (lo que pesa es el sensor, o se escaló), dice «Aceptar» y la tarjeta explica por qué no hay cambio de pauta. Los dos aceptan la propuesta: la versión no la crea el supervisor, la arma y la aprueba Factum. «Descartar» pide antes el motivo (`POST /cliente/mejoras/{id}/revision`); después se puede cambiar la decisión. Se recarga cada 3 s, y una propuesta que nace con la página abierta entra sola, marcada «Nueva».

**El aviso de mejoras.** En «Hoy», al final, un solo panel: «Factum propone mejorar una pauta» (o «… N pautas»), con una fila plegada por pauta (`Recomendaciones.tsx`). La fila dice el nombre de la pauta y «versión N · M cambios», o «sin cambios a la pauta». Desplegada, trae una línea por cambio, en palabras del supervisor y sin ids de protocolo, y una línea «No cambia: …» por lo que no cambia (lo que es del sensor, de las observaciones o de la supervisión); el porqué de cada línea está en un ícono de información, al pasar el cursor. Lo arma el servidor con todas las propuestas abiertas que ya avisó (`GET /cliente/mejoras/resumen`, que `useRecomendaciones` lee cada 5 s y al volver a la pestaña), y suena la campana una vez por propuesta nueva. Un solo botón, «Aplicar el cambio» o «Aplicar los N cambios» (o «Entendido» si nada cambia la pauta), llama a `POST /cliente/pautas/{id}/mejoras/aplicar`: acepta todo y Factum arma la versión siguiente, que el equipo aprueba antes de que llegue a las OT. «Ahora no» la esconde hasta la próxima visita y «Ver el detalle» lleva a `/supervisor/mejoras`, donde cada propuesta se revisa o se descarta por separado.

**Supervisor.** Ve todas las OT con su estado general, su operador y su avance. Asigna las que no tienen operador y reasigna las entregadas. Reasignar es P0: sin eso no hay relevo.

**Operador.** Ve solo sus OT y entra a una con «Comenzar» o «Continuar», que lleva a `/ot/:id`.

**Cada OT muestra:** id, nombre de la pauta, equipo, operador, estado general, avance (por ejemplo 3/6) y la acción según el rol. El avance y el estado los trae la API: el front no los calcula.

Estados generales *(propuesta)*:

| Estado | El supervisor ve | El operador ve |
|---|---|---|
| `sin_asignar` | «Asignar» | no aparece |
| `asignada` | el operador | «Comenzar» |
| `en_ejecucion` | el operador y el avance | «Continuar» |
| `entregada` | «Reasignar», con el avance y quién la entregó | ya no le aparece al que la entregó |
| `completa` | el avance final | «Ver resumen» |

## 6. Dani — ejecución

### La pantalla

```
┌──────────────────────────────┐
│ ← Mis OT          Factum OP1 │
├──────────────────────────────┤
│ OT-12 [Peligro]          0/6 │
│ Cambio de rodillo      00:04 │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │
├──────────────────────────────┤
│ ┃ Paso saltado               │
│ ┃ Hiciste «Retirar la guarda»│
│ ┃ antes de «Cortar la…».     │
│ ⚠ 1 Cortar energía y bloquear│
│   Te saltaste este paso…     │
│   [ Ya lo hice ]             │
│ · 2 Retirar la guarda        │
│ · 3 Cambiar el rodillo       │
│ ──────────────────────────── │
│ [       Entregar turno     ] │
└──────────────────────────────┘
```

No hay un «Hecho» fijo abajo. El paso actual dice cómo se cierra: «Se cierra solo cuando el sensor lo marque», «…cuando la cámara lo vea», o un botón «Hecho» si es de los que se cierran declarando. Si la cámara del edge manda detecciones, el paso de cámara en curso muestra qué ve ahora.

### Estados de un paso

```mermaid
stateDiagram-v2
  [*] --> pendiente
  pendiente --> en_curso: la API lo marca como paso actual
  en_curso --> verificado: su sensor o la cámara lo cierran solos
  en_curso --> comprobando: Hecho (confirmación, o cámara sin detección)
  en_curso --> warn: la API avisa que se saltó
  en_curso --> sin_senal: pasan 20 s sin evidencia
  comprobando --> verificado: la evidencia lo confirma
  comprobando --> warn: la evidencia lo contradice
  comprobando --> sin_senal: la API responde no_verificado o pasan 10 s
  sin_senal --> verificado: llega la evidencia
  sin_senal --> confirmado: Ya lo hice, con motivo
  warn --> verificado: lo hace y la evidencia lo confirma
  warn --> confirmado: Ya lo hice, con motivo
```

| Estado en pantalla | De dónde sale | Qué puede hacer el operario |
|---|---|---|
| `pendiente`, `en_curso` | `no_verificado` en la API; es `en_curso` si es el `paso_actual` | Nada si se cierra solo; «Hecho» si se cierra declarando |
| `comprobando` | Solo del front: tocó «Hecho» y espera la respuesta | Nada |
| `warn` | `en_conflicto` en la API, o una alerta de orden activa cuyo `evidencia.pendiente` es este paso | Hacerlo, o «Ya lo hice»; en un paso de cámara sin detección, también «Hecho» de nuevo |
| `sin_senal` | Solo del front: la evidencia no llega (20 s esperando, o `declarar` respondió `no_verificado`) | «Ya lo hice» |
| `verificado` | `verificado` en la API, con evidencia de sensor o cámara | Nada; dice «por sensor» o «por la cámara» |
| `confirmado` | `verificado` en la API con `evidencia.tipo = persona` | Nada; dice «Confirmado por OP1: «motivo»» |

- **La API manda.** El front nunca cierra un paso ni decide el orden: muestra el `paso_actual` que le llega. Cuando el stream trae un `evento` con `paso_id`, el front vuelve a pedir `GET /ot/{id}`.
- **Cuándo un paso se cierra solo** (`web/src/api/pauta.ts`): si es de sensor, o de cámara con `deteccion`. La pauta LOTO del demo se cierra entera sola; en la de la correa, «Hecho» aparece en el paso de cámara sin detección y en el de confirmación.
- «Hecho» llama a `POST /ot/{id}/declarar` con el `paso_id` que la pantalla mostraba.
- «Ya lo hice» pide un motivo (con atajos de un toque: «El sensor no lo marca», «La cámara no lo ve», «Lo revisé en persona») y llama a `POST /ot/{id}/pasos/{paso}/confirmar`. No aparece en un paso de confirmación.
- En `sin_senal` el front no inventa un warn ni lo hace sonar: solo ofrece confirmarlo.
- Sin conexión, los botones que escriben se deshabilitan.

### Alertas

Llegan en cualquier momento, vaya el operario en el paso que vaya. Se ven arriba de los pasos y dicen qué clase de alerta son (por su `evidencia.clave` en la API: `seguridad:`, `orden:`, `control:`, `senal:`):

| Alerta | Se ve | Se apaga |
|---|---|---|
| Seguridad («Guarda abierta con energía viva») | Tarjeta de bloqueo roja: «Peligro» | Sola, con un `alerta_resuelta` cuando el sensor se corrige. Confirmar a mano no la apaga |
| Orden («ORDEN INVERTIDO…») | Tarjeta roja: «Paso saltado», con qué se hizo antes de qué | Haciendo el paso saltado, o confirmándolo con «Ya lo hice» en el paso |
| Control perdido | Tarjeta roja: «Control perdido», con el paso que se deshizo | Sola, cuando el sensor vuelve |
| Señal (capa 2) | Franja amarilla: «Precaución» | Sola |

El banner no tiene botones: informa. Lo que el operario puede hacer está en el paso. Muestra las `alertas_activas` del snapshot, más cada evento `alerta` nuevo, menos las que cierra un `alerta_resuelta` (por su `evidencia.resuelve`). `calificacion.nivel` pinta el indicador general de la OT.

### Qué suena y qué no

Suena, y aparece en grande sobre la pantalla, lo que llega con nivel `error`, y solo la capa 1 (sensores y reglas) llega a `error`: un salto, un control perdido, una alerta de seguridad. Un salto y un control perdido suenan siempre, aunque la API los calificara más bajo: es el aviso que pidió el equipo. Lo que dice la cámara (capa 3) y las anomalías de señal (capa 2) llegan a lo más a `warning`: se muestran en su paso pero no suenan, como fija [LOGICA](./LOGICA.md#qué-puede-interrumpir-al-operario). Con tantas falsas alarmas, un aviso que suena de más le enseña al operario a ignorarlo.

### Relevo de turno

1. OP1 toca «Entregar turno» (al final de la lista) y confirma. El front llama a `POST /ot/{id}/relevo/entregar` y vuelve a `/operador`.
2. El supervisor reasigna la OT a OP2 (Diego).
3. OP2 entra y ve el **briefing** antes de la ejecución: el resumen, qué pasos están cerrados y cómo (por sensor, por la cámara, o confirmado por quién), los avisos heredados y desde qué paso sigue. Hay un relevo pendiente si el último `relevo_entregado` de la bitácora no tiene un `relevo_recibido` después, y el resumen viene en su `detalle`.
4. OP2 toca «Recibido». El front llama a `POST /ot/{id}/relevo/recibir` y abre la ejecución en el paso actual.

### Navegación

Todas las pantallas de una OT tienen arriba «← Mis OT», para volver a la lista sin entregar el turno. Una OT completa muestra el cierre con «Volver a mis OT»; una que no existe lo dice y ofrece lo mismo. Una ruta desconocida lleva al inicio del rol, o al login.

### OT completa

Pantalla de cierre con los pasos verificados, los confirmados por una persona y los avisos. El reporte con KPIs de desempeño es P1.

### Si la API falla

Banner «Sin conexión, reintentando». Se mantiene el último estado conocido, los botones que escriben se deshabilitan y el WebSocket reintenta con espera creciente, volviendo con `?desde=`. Si vuelve la red, o la pantalla vuelve después de 10 s oculta, reconecta al tiro.

Un 409 trae en `regla` la regla de negocio que se violó: se le muestra al operario tal cual y no se reintenta igual. La excepción es la estación ocupada (abajo): esa regla está escrita para quien llama a la API, y el operario ve otra cosa.

### Estación ocupada

Al empezar, el front une la OT con la estación (`POST /cliente/ots/{id}/sesion`, con el token del operador). Si la estación ejecuta otra OT abierta de la empresa, la API responde 409; el front pregunta cuál (`GET /edge/{edge}/sesion`) y, en vez de la regla, muestra «La estación edge-1 está con la OT-13 de Bruno Díaz desde las 10:42», que si la toma esa OT deja de recibir sus sensores, y un botón grande «Tomar la estación». Ese toque repite la llamada con `tomar: true`, y es el único camino que la manda. Mientras tanto la sesión se reintenta sola cada 3 s, siempre sin `tomar`: si la estación queda libre, la OT parte sola y el aviso se va.

Si la estación ejecuta una OT de otra empresa (403) no hay botón: «La estación está ocupada con una OT de otra empresa. Pide que la liberen; esta OT parte sola apenas quede libre.», y sigue reintentando. Otro 409 (la OT ya está completa) se muestra tal cual y no se reintenta.

## 7. Aviso por voz (ElevenLabs)

Cuando la API avisa que un paso no se hizo, el aviso se convierte en voz con ElevenLabs y suena en la app del operario casi al instante.

**Solo para el demo, suena en la vista del supervisor.** `config.VOZ_EN` (`web/src/config.ts`) está en `'supervisor'`: los avisos los dice el detalle de la OT del supervisor y no la pantalla del operario, así no hace falta tener abierta una ventana del operario solo para que suene. Esa vista muestra «Audio activo» o «Audio bloqueado» y un botón «Probar audio», que es el toque que el navegador pide antes de dejar sonar; la del operario los esconde. Lo normal es `'operario'`, porque el aviso es para quien está junto a la máquina: **hay que volver a eso después del demo.** Las dos pantallas usan el mismo gancho, `useAvisosEnVoz`.

**Cómo llega:**

1. Al tocar «Comenzar» o «Continuar», el front abre la sesión (`POST /cliente/ots/{id}/sesion`) y se conecta a `wss://…/ot/{id}/stream`. Solo escucha. Si se corta, vuelve con `?desde=<último evento.id>`.
2. Suena un `evento` nuevo cuya `calificacion.nivel` es `error` (seguridad, un conflicto de sensor) y **siempre** una alerta de paso saltado (`orden`) o de paso que se deshizo (`control`), aunque la API la calificara más bajo. La duda de la cámara no suena: se ve en su paso. El front arma la frase y pide su audio a `GET /api/voz?texto=…`. Antes de la voz suena un tono hecho con Web Audio, sin archivos: «ding-ding» para un aviso y tres pitidos agudos para un «Alto». Si el tono falla, la voz suena igual. Si el audio no empieza en 1,5 s desde que llegó el aviso (tono incluido), lo dice la voz del navegador.
3. Lo que suena **también aparece en grande** sobre la pantalla: la misma frase, el título de la alerta («Paso saltado», «Peligro», «Control perdido»), qué hacer, «Entendido» y «Escuchar de nuevo». Con guantes y ruido de planta el operario puede no oírlo, y en el celular el banner queda fuera de la vista si bajó por la lista. Al tocar «Entendido» la pantalla va al paso afectado. Se cierra solo si la alerta se resuelve o el paso queda verificado; el banner y el paso siguen mostrando la alerta mientras esté activa.
4. El `evento.id` es la llave: un evento suena y aparece una sola vez, también al reconectar. La bitácora que trae el snapshot al conectar **no** suena ni aparece: es lo que ya pasó.
5. `/api/voz` es nuestro, no de la API de Francisco: lo sirve el mismo servidor del front (`web/servidor/voz.ts`, montado en `vite.config.ts`; al desplegar, una función de Vercel con el mismo código). Hace la misma llamada que `~/code/Godoy97/elevenlabs-tts/tts.py`, con `eleven_flash_v2_5` y la voz chilena «Catalina - Chilean Spanish» (`6Gr4AVmTax1pMJO0lHRK`; `ELEVENLABS_VOICE_ID` para otra). Cada frase se genera una vez y se guarda en `web/.cache/voz/`.

**Cómo correrlo:** la llave va en `web/.env.local` (git la ignora) como `ELEVENLABS_API_KEY=…`, y `npm run dev:mock` (o `npm run dev`) ya sirve la voz. Sin llave, `/api/voz` responde 503 y el aviso lo dice el navegador.

**Cómo desplegarlo:** el front está en Vercel, en <https://factum-tau.vercel.app> (proyecto `factum`), y habla con la API de la VM. **Producción es `main`:** desde `web/`, con `vercel login` y `vercel link` hechos, `npm run desplegar` sube lo que está en `origin/main`, no lo que haya en tu carpeta ni en tu rama (`deploy/vercel/desplegar.sh` lo saca a una copia aparte). El trabajo en curso se queda en su rama; para verlo en una URL sin tocar producción, `npm run desplegar:previa` sube tu carpeta como vista previa (sin la voz de ElevenLabs, que solo tiene llave en producción). Los dos compilan en tu máquina y suben el resultado, por dos razones: el mock importa las pautas de `datos/`, que queda fuera de `web/` y Vercel no la vería; y el builder de Vercel no compila con TypeScript 7, así que `npm run build:funcion` deja `servidor/voz.ts` compilado en `web/api/_servicio/` y la función (`web/api/voz.js`) lo importa. La llave va como variable de entorno del proyecto en Vercel (`vercel env add ELEVENLABS_API_KEY production`); cambiarla pide desplegar de nuevo. En Vercel los audios guardados los sirve la CDN, y el tope de 200 frases es por instancia, no global.

Por qué la voz sale del evento y no de `calificacion.avisos`: un aviso no trae `id` ni dice de qué paso es, así que no hay cómo saber si ya sonó. Y por qué el front pide la voz en vez de esperar que el back la adjunte: así la voz solo necesita un texto, y no depende de cómo el equipo de Francisco rehaga los eventos. Si después el back manda un `audio_url`, el front reproduce ese.

**Reglas:**

- La llave de ElevenLabs vive solo en el servidor, en `ELEVENLABS_API_KEY`, sin prefijo `VITE_`: así Vite nunca la manda al navegador. Nunca en el repo: el repo es público. `/api/voz` no tiene autenticación, así que genera a lo más 200 frases nuevas por arranque; las guardadas se sirven siempre.
- Meta: menos de 2 s desde que el evento entra a la bitácora hasta que suena. El stream lo entrega al instante y el tono parte al tiro. Una frase precalentada empieza apenas termina el tono; una que ElevenLabs tarda en generar la dice el navegador a los 1,5 s.
- Los textos de los avisos del demo se generan una vez y se guardan, para que en el escenario suenen sin esperar a ElevenLabs.
- Si `/voz` falla, el front dice el mismo texto con la voz del navegador (`speechSynthesis`). El aviso nunca queda mudo.
- Si llegan dos eventos, suenan en orden, sin pisarse.
- La excepción es un **«Alto»**, la alerta de seguridad de capa 1 (`tipo: 'alerta'`, `capa: 1`, `evidencia.clave` `seguridad:…`; ver `esAlto` en `estado.ts`). Corta el tono o la voz que esté sonando, suena primero y lo cortado vuelve a sonar entero después. Un «Alto» no corta a otro: entre ellos van en orden de llegada.
- Al abrir la OT, el front pide de a una las frases que ya conoce (paso saltado de cada paso y control perdido de cada control crítico, `frasesDeLaOt`), para que el servidor las tenga generadas cuando hagan falta. Las alertas de seguridad no entran: su texto lo escribe el back. Al primer fallo se detiene. Cuidado: consume el tope de 200 frases nuevas por arranque.
- Cada vez que un aviso cae a la voz del navegador queda un `console.warn('[voz] …')` con el motivo (`sin-url`, `error-audio`, `sin-inicio`, `play-rechazado`). No se registra la llave ni nada del operario.
- Lo que se dice es una frase armada en el front (`textoParaVoz`), con el tono de la pizarra: un salto suena «Oye, te saltaste el paso 1: Cortar la energía y bloquear con candado. Hazlo antes de seguir.»; un control perdido, «Oye, se deshizo el paso 1: …»; lo demás, el `detalle` de la API sin las mayúsculas gritadas.
- El navegador del celular no reproduce sonido hasta que el usuario toca algo. El toque en «Comenzar» o «Continuar» desbloquea el audio, la voz del navegador y el `AudioContext` del tono: Diego llama a `desbloquearAudio()` de `web/src/ejecucion/voz.ts` en ese botón. Si se entra a `/ot/:id` sin ese toque (una recarga o un enlace directo), la pantalla pide un toque antes de empezar. Muestra si el audio está activo, con un botón «Probar audio». Probarlo en el celular del demo, sobre todo si es iPhone.
- Con la pantalla bloqueada, el celular corta el WebSocket y deja de sonar. La vista de ejecución le pide al navegador que mantenga la pantalla encendida (Wake Lock API) mientras la OT está abierta.
- Con el mock la voz es la misma: `/api/voz` la sirve el servidor del front, no la API.

## 8. Contrato con la API

> El back va a cambiar con el equipo de Francisco. Esto es solo lo que el front consume, y todo cambio se absorbe en `web/src/api/` sin tocar las pantallas.

La API está desplegada en `https://34-176-44-192.sslip.io`. La guía completa está en [`/agente`](https://34-176-44-192.sslip.io/agente), los esquemas en `/openapi.json`, y el diseño en el [PRD de servicios en vivo](../projects/servicios-en-vivo/PRD.md), el [ADR-0007](../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md) y el [ADR-0012](../decisions/0012-login-y-clientes-cada-empresa-ve-lo-suyo.md). Las listas y la asignación van por el servicio para clientes, con login; la ejecución de una OT (`/ot/{id}/...`) sigue abierta. El front manda el token en todas las llamadas.

**Lo que el front usa y ya existe:**

| Qué | Para | Nota |
|---|---|---|
| `POST /auth/entrar` `{usuario, clave}` → `{token, expira, persona}` | los dos | `persona`: `{id, nombre, usuario, rol, cliente}`. El token dura 12 horas y va como `Authorization: Bearer`. 401 si no calzan. `POST /auth/salir` lo invalida |
| `GET /cliente/ots` → `[{ot, pauta, version, equipo, abierta_en, paso_actual, completa, operador, estado_general, entregada_por, cerrados, total, calificacion}]` | Diego | El supervisor ve todas las de su empresa; el operador, las suyas. El id viene en `ot`, no en `id`. El avance es `cerrados` sobre `total` y la verificación es `calificacion`, sin pedir cada OT. 401 sin token |
| `GET /ot/{id}` → `{pauta, equipo, paso_actual, completa, pasos, verificados, en_conflicto, pendientes}` | los dos | Cada paso: `id, orden, titulo, estado, control_critico, capa, evidencia, detalle`. El dashboard del operador lo pide solo para sus OT abiertas, para mostrar en qué paso siguen |
| `GET /cliente/pautas` → `[{id, nombre, version, equipo, pasos, protocolos}]` | Diego | Las pautas que la empresa puede pedir: su nombre legible para la lista de OT y las opciones de «Pedir OT» |
| `GET /cliente/operadores` → `[persona]` | Diego | Los operadores de la empresa, para asignar. Solo supervisor (403) |
| `GET /cliente/personas` → `[{id, nombre, rol}]` | los dos | Los nombres de toda la empresa; lo lee cualquier persona, también un operador. Se pide una vez por sesión (al entrar o al abrir con una sesión guardada), para que el relevo y la bitácora digan «Ana Rojas» y no `operario:1` |
| `POST /cliente/ots` `{pauta_id}` → `{ot, pauta, version, nombre, cliente}` | Diego | «Pedir OT»: la OT nace sin operador. Solo supervisor; 403 si la pauta no está habilitada para su empresa |
| `GET /pautas/{pauta_id}?version=` | Dani | La pauta completa, con `instruccion`, `tipo_evidencia` y `deteccion` de cada paso: con eso se sabe si un paso se cierra solo. Se pide una vez |
| `POST /cliente/ots/{id}/asignar` `{operador}` | Diego | Asigna una OT sin operador o reasigna una entregada. Quién asigna sale del token y queda en la bitácora como `ot_asignada`. 403 si el operador no es de la empresa; 409 si está completa o ya tiene operador |
| `POST /cliente/ots/{id}/sesion` `{edge_id, tomar}` → `{edge_id, ot_id, operario, desde}` | Dani | Une la OT con el edge, con el token del operador y sin `X-Clave-Equipo`: el operario de la sesión es quien entró. Sin sesión, las lecturas no llegan a ninguna OT. 409 si la estación ejecuta otra OT abierta (se repite con `tomar: true`, solo con el toque del operador), 403 si esa OT es de otra empresa, 404 si la OT no es suya, 409 si ya está completa. El demo tiene un solo edge, `edge-1`, que va en `VITE_EDGE_ID` ([PR #39](https://github.com/platanus-hack/platanus-hack-26-cl-team-10/pull/39)) |
| `GET /edge/{edge_id}/sesion` → `{edge_id, ot_id, operario, desde}` | Dani | Qué OT ejecuta la estación, para decir de quién es cuando está ocupada. Público; 404 si está libre |
| `WS /ot/{id}/stream?desde=` | Dani | Primero un `snapshot` (estado, calificación, alertas activas, sesión, sensores y bitácora) y después `lectura`, `evento`, `calificacion_ot`, `sesion` y `detecciones` (lo que ve la cámara del edge) |
| `POST /ot/{id}/declarar` `{actor, texto, paso_id}` | Dani | «Hecho». `paso_id` es el paso que la pantalla mostraba: si su evidencia ya lo cerró, no se evalúa el siguiente. Un paso de cámara se juzga con el último cuadro del edge |
| `POST /ot/{id}/pasos/{paso_id}/confirmar` `{actor, motivo}` | Dani | «Ya lo hice». Solo el paso en curso, nunca uno de confirmación, nunca sin motivo (409). Deja un `veredicto` `verificado`, capa nula, con `evidencia: {tipo: persona, motivo, contra}` |
| `POST /ot/{id}/relevo/entregar?actor=` y `/relevo/recibir?actor=` | Dani | El relevo pendiente se lee de la bitácora (sección 6) |
| `GET /cliente/ots/{id}/reporte`, `GET /cliente/mejoras`, `GET /cliente/mejoras/resumen`, `GET /cliente/mejoras/{id}/borrador`, `POST /cliente/mejoras/{id}/revision`, `POST /cliente/pautas/{id}/mejoras/aplicar` y `GET /cliente/metricas` | Diego | El reporte de la OT, las propuestas de mejora, el aviso por pauta y las métricas (sección 5). Las de mejoras y métricas, solo supervisor (403) |
| `GET /edge/{edge_id}/video.mjpg` | Diego, P1 | Video en vivo en un `<img>`, por si el supervisor quiere ver la estación. Ya existe una página `/monitor` con video, avisos y bitácora |

Un aviso de `calificacion.avisos` es `{nivel, certeza, capa, motivos}`: sin `id` y sin `paso_id`. Un `evento` del stream trae `id, tipo, paso_id, estado, capa, detalle, evidencia, calificacion`.

**La voz no es de esta API:** `GET /api/voz` la sirve el servidor del front (sección 7). El servidor de Francisco no necesita la llave de ElevenLabs.

Respaldo si el ESP32 falla en el escenario: la lectura se puede escribir a mano en `POST /edge/edge-1/lecturas` o en `POST /sensores`.

`GET /cliente/ots/{id}` trae la OT con su `calificacion` (todo bien, atención o detente). El front la usa para la verificación de la lista, para los incidentes y para saber si una persona puede abrir una OT: responde 404 si no es de su empresa o, para un operador, si no está asignada a él. Con 404 la ejecución dice «Esta OT no está en tu lista» y no abre sesión.

`GET /edge/{edge_id}/video.mjpg` es el video en vivo de la estación, para un `<img>`. El front nunca manda `X-Clave-Equipo` (iría en el navegador, a la vista): por eso usa `POST /cliente/ots/{id}/sesion` y no `POST /ot/{id}/sesion`.

## 9. Escenarios del mock

Ejecución (Dani). Todos sirven para las dos pautas del repo: la correa (por defecto) y LOTO, la del demo con ESP32 y cámara (`?pauta=loto`).

| Escenario | `?escenario=` | Qué hace la API |
|---|---|---|
| Camino feliz | `feliz` | Los pasos de sensor (4 s) y de cámara con detección (5 s) se cierran solos; «Hecho» cierra los demás; la OT termina |
| Salto corregido | `warn-corregido` | Al llegar al primer control crítico, la API avisa que se saltó (un paso posterior se hizo antes); 5 s después el operario lo hace y el aviso se resuelve solo |
| Salto confirmado | `warn-sobrescrito` | El mismo salto, pero nada lo cierra hasta que el operario toca «Ya lo hice» con un motivo |
| Alerta de seguridad | `alerta-seguridad` | La guarda se abre con energía viva a mitad del trabajo; se resuelve sola 10 s después |
| Control perdido | `control-perdido` | El primer control crítico ya verificado se deshace y vuelve 8 s después |
| La cámara dice que no | `camara-no` | El primer «Hecho» en un paso de cámara da un conflicto que se muestra pero no suena |
| Sin evidencia | `sin-senal` | Nada se cierra solo: a los 20 s el paso ofrece «Ya lo hice» |
| Relevo | `relevo` | OT en 3/6 con un paso confirmado por Ana; Bruno entra y la termina |
| Incidente | `incidente` | Para el supervisor: la OT de Bruno va en la estación y a los 8 s se abre la guarda con la energía viva. Barra roja, campana y vista en vivo. `/supervisor?escenario=incidente&como=supervisor:oculta` |
| Atención | `atencion` | Para el supervisor: Ana y Bruno ejecutan a la vez, cada uno en su estación, y en la de Bruno la cámara duda del rodillo, reconoce cosas y la estación lee temperatura y distancia. Su fila va primero y encendida en amarillo; su vista en vivo muestra las cajas sobre el video y las fichas de los sensores. `/supervisor?escenario=atencion&como=supervisor:oculta` |
| Mejora | `mejora` | El demo sin la estación: la OT de Ana ya se ejecutó, con un desvío de orden que corrigió. La de Bruno corre ahora y a los 6 s se desvía en el mismo paso: es la segunda. Después se corrige y termina sola: al completarse aparecen la propuesta y «Ver el reporte». `/supervisor/ot/ot-13?escenario=mejora&como=supervisor:oculta` |
| Estación ocupada | `estacion-ocupada` | `edge-1` ejecuta la OT de Bruno cuando Ana abre la suya: el aviso dice de quién es y «Tomar la estación» se la quita. `/ot/ot-12?escenario=estacion-ocupada&como=operario:1` |
| API caída | `api-caida` | Errores y timeouts con el operario a mitad de un paso |
| Ya completa | `completa` | La OT está terminada cuando el operario la abre |

Gestión (Diego):

| Escenario | `?escenario=` | Qué hace la API |
|---|---|---|
| Lista vacía | `vacia` | No hay OT |
| Lista mixta | `mixta` | OT en todos los estados generales |
| OT ya tomada | `ya-asignada` | Al asignar, responde que otro supervisor ya la asignó (409) |
| OT ajena | `?como=operario:1` en `/ot/ot-13` | Un operador abre por URL una OT que no es suya: «Esta OT no está en tu lista» (404) |

## 10. Prioridades

### P0

**Diego**
- [ ] Login falso con roles.
- [ ] Dashboard del supervisor.
- [ ] Dashboard del operador.
- [ ] Listado y display de OT.
- [ ] Asignar y reasignar operador.
- [ ] Navegación a `/ot/:id`.
- [ ] Escenarios de gestión.

**Dani**
- [ ] Base compartida y mock.
- [ ] Vista de ejecución con la máquina de estados.
- [ ] Alertas, «Hecho» donde hace falta y «Ya lo hice» con motivo.
- [ ] Voz: `/voz` con ElevenLabs y reproducción en el celular.
- [ ] Entregar turno y briefing.
- [ ] Pantalla de OT completa.
- [ ] Escenarios de ejecución.

**Los dos, después de las pantallas:** lo que falta de la sección 8 (asignar y voz), lo mínimo para que el demo corra contra el back real. Es camino crítico, porque el demo no corre sobre el mock: tiene que estar listo con tiempo para ensayar, a más tardar a las 05:00 del domingo 2026-11-22 *(propuesta)*.

### P1

- [ ] Reporte final con KPIs de desempeño (Dani).
- [ ] Warns por operario en el dashboard del supervisor, el «OP1 +1 warn» de la pizarra (Diego).
- [ ] Durante la ejecución: notas, reportar una anomalía y pedir apoyo al supervisor (Dani).
- [ ] Filtros y búsqueda de OT (Diego).
- [ ] Panel para disparar a mano los eventos del mock en el ensayo (Dani).
- [x] Login real, contra `POST /auth/entrar`.
- [ ] Estados vacíos y mensajes de error más cuidados.

## 11. Criterio de éxito

En el escenario corre sobre el back real, con el supervisor en un computador, el operador en un celular y los sensores reales del ESP32. Antes de eso, cada paso se prueba sobre el mock.

1. El supervisor entra y asigna la OT a OP1.
2. OP1 entra, ve solo sus OT y comienza.
3. Un sensor muestra que un paso no se hizo, la API avisa y OP1 lo oye en menos de 2 s.
4. OP1 toca «Ya lo hice» con un motivo y el paso queda confirmado a su nombre.
5. Alguien abre la guarda con la energía viva y suena la alerta de seguridad.
6. OP1 entrega el turno y el supervisor reasigna a OP2.
7. OP2 lee el briefing, confirma y termina la OT.

## 12. Enfoques considerados

| Tema | Elegido | Descartado y por qué |
|---|---|---|
| Stack | Vite + React + TS, una app con rutas | Next.js: más pesado de montar, y el render en servidor no le aporta nada al demo. HTML plano en `app/estatico`: sin build, pero difícil de trabajar entre dos y de probar una máquina de estados |
| Forma del mock | La del esqueleto más extensiones | `{bool, string}` de la pizarra: no distingue un warn de una alerta crítica ni muestra la evidencia. Modelo propio con adaptador: más aislado del back, pero más código, y `api/` ya hace de adaptador |
| Componentes | Mantine, sin Tailwind | MUI: más pesado, y cuesta que no se vea como Material. shadcn/ui con Tailwind: se ve muy bien, pero cada componente se copia y se arma a mano, y dos personas agregando a la misma carpeta chocan |
| Origen de la voz | El front pide el audio a `/voz` | Que el back adjunte el audio al warn: ata la voz a cómo el equipo de Francisco rehaga los warns. ElevenLabs desde el navegador: expone la llave en un repo público |

## 13. Queda a criterio de quien construye

- La tipografía y el resto del tema de Mantine. Los colores están fijos en la [sección 4](#colores).
- Cómo se implementa la máquina de estados. Sugerencia: un reducer puro y tipado, probado con Vitest, sin librerías.
- Cómo guarda el mock su estado entre llamadas.
- Cómo se desbloquea el audio en cada navegador.
- Dónde se publica el front.
