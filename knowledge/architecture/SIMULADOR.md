# Simulador

> Referencia · 2026-11-21 · Fuente: [`app/estatico/simulador.html`](../../app/estatico/simulador.html), servida en `/simulador`.

El simulador muestra cómo se ejecuta una OT con Factum, paso a paso y en 3D, con las pautas y los operarios que tiene la base del servidor. Lo que es real y lo que se simula está separado: las pautas, sus protocolos y las personas salen de la base; las OT que se ejecutan en la pantalla son simuladas y no se escriben en ninguna parte.

Reemplaza a la página `knowledge/architecture/flujo-protocolo-a-ot.html`, que fue su primera versión. Hay un solo archivo: el que sirve el servidor.

## Dónde se abre

- **En el servidor del demo:** `https://34-176-44-192.sslip.io/simulador`. El monitor (`/`) lleva un botón «Simulador» en su barra.
- **En local:** `uv run uvicorn app.api:app` y `http://localhost:8000/simulador`. Servido así, la base es la del mismo servidor.
- **Como archivo suelto:** abierto desde el disco se conecta a la VM. `?base=<url>` elige otra base y `?sinbase` lo deja con los datos de ejemplo que trae escritos.

El enlace del simulador al monitor solo aparece para un supervisor con sesión. El monitor mismo sigue abierto a quien tenga la URL: restringirlo pide cambiar el servidor. `Brecha`.

## Qué es real y qué es simulado

| Qué | De dónde sale |
|---|---|
| Pautas, versiones y pasos | La base: `GET /pautas` y `GET /pautas/{id}`. Con sesión, solo las habilitadas para la empresa (`GET /cliente/pautas`) |
| Protocolos de cada pauta y su texto | `GET /cliente/pautas` con sesión; el texto, de `/interno/protocolos/{id}` con la clave del equipo |
| Operarios | Con sesión, `GET /cliente/personas` (con nombre). Sin sesión, los `operador` de `GET /ots` (solo el id) |
| OT reales de la pauta y su bitácora | `GET /cliente/ots` (o `GET /ots` sin sesión) y `GET /ot/{id}/eventos`. Se muestran, no se tocan |
| Las ejecuciones en pantalla | **Simuladas.** Un motor en la página aplica las mismas reglas que `app/servicios.py` sobre las lecturas del guion. No llaman a la API ni dejan rastro |
| El reporte y las propuestas | Calculados en la página sobre las ejecuciones simuladas, con el criterio mínimo de [`app/mejora.py`](../../app/mejora.py): por paso, en al menos dos OT distintas, nunca por persona. Sin la prueba de recurrencia, el aviso en vivo ni el cambio propuesto, que solo calcula el servidor |

Sin sesión, la base no entrega nombres: los operarios se ven por su id. Con un usuario del cliente se ven sus nombres, sus OT y sus protocolos; un supervisor ve toda la empresa y un operador solo sus OT.

## Las pautas

Cada pauta aprobada de la base es un caso. Hay dos clases:

- **Las cinco con guion escrito** (`pauta-polin-demo`, `pauta-brazo-01`, `pauta-polin-ct-01`, `pauta-celda-mt-01` y `pauta-excavadora-01`) usan su guion, su escena 3D y sus textos en palabras de terreno, si la base tiene la misma versión y los mismos pasos.
- **Cualquier otra** se simula desde sus propios pasos. Cada sensor parte en reposo: si la pauta lo lleva a varios valores, el reposo es el último; si lo lleva a uno, su contrario (`presente` → `ausente`, `cortada` → `viva`, `frio` → `caliente`). Un paso de sensor se cierra llevando el sensor al valor que pide; uno de cámara o de confirmación, declarando. La escena se elige por el nombre y el equipo de la pauta: la correa a escala, la correa de faena, el brazo, la celda, la excavadora, el camión de extracción o la botella del demo, y una escena genérica (un equipo sobre su base y un poste por sensor) para lo demás. En la botella, que no tiene sensores, la botella llega a la mesa con el paso 1 verificado y pierde la tapa con el paso 2; lo que dibuja la vista «Cámara de Factum» es el cuadro que juzga el VLM al correr en la base.

Todas las escenas comparten la persona (piernas, brazos que se estiran para tomar algo, casco) y las sombras en el piso.

## Cómo ejecuta cada operario

Cada ejecución tiene un operario de la base y una forma de ejecutar la pauta:

| Forma | Qué hace |
|---|---|
| El guion del caso | Solo en las cinco con guion: el recorrido escrito, con sus desvíos |
| Sigue la pauta | Cierra cada paso en orden, sin alertas |
| Se salta un paso que no se puede saltar | Hace un paso posterior con un control crítico pendiente y lo deshace: orden invertido |
| Deshace un control antes de tiempo | Pierde un control ya verificado y lo repone: control perdido |
| Declara el paso de cámara antes de tiempo | El juez responde que no y el paso queda en conflicto hasta que se vuelve a declarar |

Los desvíos de una pauta de la base se generan desde sus pasos, y el motor los comprueba antes de ofrecerlos: tienen que abrir una alerta, quedar resueltos y dejar que la OT termine. Una pauta cuyo único control crítico es el último paso no tiene desvío que ofrecer (pasaba con `pauta-polin-estacion` hasta la v6). La v7 agrega «Alejarte de la cinta», un control crítico antes del último; si el simulador ya le ofrece un desvío no se comprobó.

**Agregar y sacar operarios.** «+ Operario» agrega una ejecución eligiendo quién y cómo; la «×» de cada ficha la saca de la simulación y del reporte. **El relevo** («⇄ Relevo») entrega la misma OT a otro operario desde el paso en curso: lo verificado sigue verificado, como en `POST /ot/{id}/relevo/entregar` y `/recibir`. Otra ejecución, en cambio, es otra OT: una OT completa no se reasigna.

## La pantalla

- **Arriba,** las pautas; **a la izquierda,** la escena 3D, el relato del tramo y la línea de tiempo, con un cuadro por tramo teñido según cómo queda la OT; **a la derecha,** el pipeline Protocolo → Pautas → OT → Ejecución → Reporte, con lo que la base tiene de cada uno.
- **La escena** tiene vistas (general, frente, costado, desde arriba y la de la cámara de Factum) y capas que se encienden y apagan. Cada tramo se ve como una acción: la persona llega a donde actúa y recién después cambian los sensores y salta la alerta.
- **«Ver lo técnico»** muestra, para cada etapa, las rutas y el código que hacen lo mismo en el servidor, y qué está construido.
- **El estilo** es el del monitor: tinta con rejilla, la letra de matriz para los títulos, rótulos en mono, lima para lo verificado, ámbar para atención y rojo para peligro.

## Cómo se actualiza y se despliega

- Se edita `app/estatico/simulador.html` y va en el despliegue normal (`deploy/vm/desplegar.sh`). `tests/test_stream.py` comprueba que `/simulador` se sirva y que el monitor lleve a él.
- Los datos de los cinco casos con guion están escritos en el archivo (el objeto `F`): sus guiones, los textos y lo que respondió cada llamada al generarlos. Si cambian esas pautas en `datos/`, el caso escrito se deja de usar y la pauta se simula desde la base.

## Lo que no cubre

- **El motor de la página es una copia de las reglas del servidor.** Si `app/servicios.py` cambia una regla, el simulador no se entera. `Brecha`.
- **Las OT simuladas no llegan a `GET /cliente/mejoras` ni a las métricas.** El reporte que muestra es el de la simulación.
- **El texto de los protocolos** pide la clave del equipo en un servidor que la tiene configurada; el simulador no la guarda.
