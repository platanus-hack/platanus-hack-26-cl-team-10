# PRD — Servicios en vivo

> **Dueño de la decisión:** Francisco · **Se consulta a:** frente 2 (qué consume la UI), frente 3 (qué manda el edge), frente 4 (qué redacta el modelo) · **Alcance:** lo que llega del edge se atribuye a la OT en curso, se califica y llega a la UI al instante, y el CRUD de lo que las reglas piden guardar.
>
> **Estado →** [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md). Este documento no lleva avance. La decisión estructural está en [ADR-0007](../../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md) y el recorrido animado en [servicios.html](../../architecture/servicios.html).

## 1. Resumen

**Hoy:** un paso se evalúa solo cuando el operario habla, y una alerta de seguridad se escribe en todas las OT de la base porque el sistema no sabe cuál se está ejecutando. La UI tiene que preguntar para enterarse de algo.

**Después:** el edge manda lecturas sin parar; cada una se atribuye a la OT que el operario eligió, cierra el paso si es su sensor, alerta una sola vez si la condición empieza, y la UI la ve en el mismo segundo con una calificación OK, WARNING o ERROR que dice cuánto creerle.

## 2. Historia

**Antes.** El operario, al cortar la energía y poner el candado, tiene que decirlo en voz alta para que el paso avance, aunque el sensor del candado ya lo sepa. Si abre la guarda con la energía viva, la alerta aparece en la bitácora de cualquier OT abierta.

**Después.** El operario pone el candado y el paso queda verificado solo, con la lectura como evidencia. Si abre la guarda con energía viva, la alerta entra una vez a su OT y a ninguna otra, y suena en su auricular.

## 3. Objetivos y no-objetivos

- **O1 —** Toda lectura del edge queda atribuida a una sola OT, o a ninguna si no hay sesión.
- **O2 —** La UI recibe cada lectura, evento y calificación sin preguntar, y al reconectar recupera la bitácora que se perdió.
- **O3 —** Cada evento lleva su calificación por capa, con certeza y motivos, y la OT tiene una calificación vigente.
- **O4 —** Pautas, aprobaciones, OT, sesiones, eventos y sensores tienen su CRUD, con las reglas de negocio adentro.
- **O5 —** Un aviso vive mientras su condición dure: cuando el sensor se corrige, el aviso sale de la pantalla y la bitácora registra que se resolvió.
- **O6 —** El video del edge entra a la API, la UI lo ve en vivo y un paso de cámara se juzga con el último cuadro, que queda como evidencia.
- **O7 —** Un agente que se conecta encuentra en `/agente` todo lo que necesita para usar la API sin leer el código.
- **O8 —** Cada criterio de aceptación se puede correr contra un servidor vivo, local o el del demo, y ver qué se llamó, qué respondió y qué llegó por el stream.
- **NO1 —** No es un broker ni varios servicios desplegados: una aplicación y una base ([ADR-0003](../../decisions/0003-patrones-de-arquitectura-para-el-mvp.md)).
- **NO2 —** No redacta la justificación en texto; entrega los motivos y la redacción es del frente 4.

## 4. Flujo: hoy → después

```text
HOY
edge → POST /sensores → alerta a TODAS las OT
operario habla → POST /ot/{id}/declarar → veredicto → la UI pregunta para verlo

DESPUÉS
operario elige la OT → POST /ot/{id}/sesion (une OT y edge)
edge → POST /edge/{id}/lecturas → servicio: dedupe → sesión → seguridad → paso por sensor → capa 2
     → bitácora (solo agrega) → calificación → bus → WS /ot/{id}/stream → UI
sensor se corrige → alerta_resuelta → el aviso sale de calificacion.avisos
cámara → WS /edge/{id}/video → último cuadro → juez de cámara al declarar · MJPEG → UI
```

## 5. Datos y reglas

| Entidad | Cambio | Regla o fuente |
| --- | --- | --- |
| `sesiones` | Nueva: une un edge con la OT que ejecuta | ADR-0007 |
| Clave del equipo | Con `CLAVE_EQUIPO` en el servidor, quitarle un edge a la OT que ejecuta, o soltarlo, pide la cabecera `X-Clave-Equipo`; un edge libre o repetir su sesión, no. Sin la variable, todo abierto | La API es pública: sin esto cualquiera cambia a qué OT entran las lecturas del demo |
| `aprobaciones` | Nueva: quién aprobó cada versión de pauta | Una persona aprueba antes de usar ([ADR-0003](../../decisions/0003-patrones-de-arquitectura-para-el-mvp.md)) |
| `pautas` | Cambiar = versión siguiente; nunca encima de otra ni saltando | Pauta versionada (ADR-0003) |
| `ots` | Solo desde una pauta aprobada; guarda la versión | [ADR-0006](../../decisions/0006-la-ot-nace-del-protocolo.md) |
| `eventos` | Solo agrega; sin editar ni borrar por ninguna vía | [LOGICA](../../architecture/LOGICA.md#evento) |
| Calificación | Se calcula al leer, no se guarda | ADR-0007 |
| `alerta_resuelta` | Nuevo tipo de evento: apunta a la alerta que cierra en `evidencia.resuelve` | [LOGICA](../../architecture/LOGICA.md#evento), ADR-0007 |
| Video | Los últimos 10 s por edge, en memoria; el cuadro que juzgó un paso queda en `datos/evidencias/` | ADR-0007 |

## 6. Contrato de comportamiento

```text
CUANDO llega una lectura del edge
  SI su seq ya se recibió
    NO se procesa (el edge reenvía tras un corte)
  SI el edge no tiene sesión
    NO toca ninguna bitácora; solo actualiza el sensor
  ENTONCES
    la regla de seguridad que EMPIEZA entra como alerta de capa 1 (una vez mientras dura)
    si es el sensor del paso actual y lo cierra, entra su veredicto
    si deshace un control crítico ya verificado, entra una alerta de capa 1 (control)
    si cierra un paso posterior mientras el actual, crítico, sigue abierto, entra una alerta de capa 1 (orden)
    si es numérica y se aleja de su historia normal, entra una alerta de capa 2 (una vez; la distancia del edge no se compara, `SIN_ANOMALIA`); diez iguales seguidas, sensor pegado
    todo sale por el stream de esa OT, con su calificación
CUANDO la condición de una alerta abierta desaparece
  ENTONCES entra alerta_resuelta que la apunta, y el aviso deja de venir en calificacion.avisos
CUANDO el sensor del paso en curso lleva más de 5 s sin lecturas
  ENTONCES la OT baja a warning: el sensor puede haberse caído
CUANDO una persona confirma el paso en curso contra la evidencia, con motivo
  ENTONCES el paso queda verificado por persona (capa nula), la OT en warning, y la seguridad se sigue evaluando con los sensores
CUANDO el operario declara
  SI nombra un paso que su sensor ya cerró → se registra y no se evalúa contra el siguiente
  SI el paso es de cámara y no hay un cuadro de los últimos 10 s → no se verifica y no se le pregunta al juez

Promesas: un modelo nunca contradice a un sensor; solo la capa 1 llega a ERROR; la bitácora solo agrega.
```

## 7. Alcance

**Entra:** sesión por edge, ingreso de lecturas en lote, atribución, revisión por capa, calificación, resolución de alertas, WebSocket por OT con reconexión, video del edge (entrada, MJPEG y cuadro para el juez), CRUD de pautas, aprobaciones, OT, sesiones, eventos (lectura) y sensores, la guía `/agente`, el banco de pruebas `/casos` y el servidor del demo.

**No entra:** la redacción de la justificación (frente 4), el juez real de cámara (frente 3), la voz del operario (frente 2), varias estaciones con el mismo `sensor_id`.

## 8. Criterios de aceptación

- **CA1 —** **Dado** un edge sin sesión, **cuando** manda guarda abierta con energía viva, **entonces** ninguna OT recibe la alerta.
- **CA2 —** **Dado** el edge en sesión con la OT 1 y otra OT abierta, **cuando** se da la condición de seguridad, **entonces** solo la OT 1 recibe la alerta.
- **CA3 —** **Dado** el paso de bloqueo en curso, **cuando** llega el candado cerrado, **entonces** el paso queda verificado sin que el operario hable.
- **CA4 —** **Dado** el paso de bloqueo en curso, **cuando** llega una lectura de la guarda, **entonces** la pauta no avanza.
- **CA5 —** **Dado** una condición de seguridad activa, **cuando** siguen llegando lecturas, **entonces** la alerta entra una sola vez, y otra vez solo si la condición vuelve.
- **CA6 —** **Dado** una UI conectada al stream, **cuando** el edge manda una lectura que cierra un paso, **entonces** recibe lectura, evento y calificación, en ese orden.
- **CA7 —** **Dado** una UI que se desconectó, **cuando** vuelve con el último id que vio, **entonces** recibe solo la bitácora que le faltó.
- **CA8 —** **Dado** una pauta sin aprobar, **cuando** alguien abre una OT con ella, **entonces** recibe 409.
- **CA9 —** **Dado** una versión de pauta que existe, **cuando** alguien la vuelve a crear, **entonces** recibe 409.
- **CA10 —** **Dado** cualquier evento, **cuando** alguien intenta editarlo o borrarlo, **entonces** recibe 405.
- **CA11 —** **Dado** una alerta de guarda abierta con energía viva, **cuando** la guarda se cierra o la energía se corta, **entonces** entra `alerta_resuelta` y la UI deja de mostrar el aviso.
- **CA12 —** **Dado** un pico de vibración con alerta abierta, **cuando** la señal vuelve a lo normal, **entonces** la alerta de capa 2 se resuelve.
- **CA13 —** **Dado** la cámara del edge transmitiendo, **cuando** el operario declara un paso de cámara, **entonces** el juez recibe el último cuadro y ese cuadro queda como evidencia del veredicto.
- **CA14 —** **Dado** un agente nuevo, **cuando** lee `/agente`, **entonces** encuentra todas las rutas de la API con la URL del servidor.
- **CA16 —** **Dado** un paso en curso cuyo sensor no muestra lo hecho, **cuando** una persona lo confirma con su motivo en `POST /ot/{id}/pasos/{paso}/confirmar`, **entonces** el paso queda verificado por persona, la bitácora guarda quién, por qué y qué marcaba el sensor, la OT queda en `warning`, y las reglas de seguridad siguen mandando. Sin motivo, como `sistema` o sobre un paso que no es el actual, recibe 409.
- **CA15 —** **Dado** el banco `/casos` apuntando a un servidor, **cuando** se corre un criterio, **entonces** usa una OT y un edge propios de la corrida, muestra cada llamada con su respuesta y cada mensaje del stream, compara lo esperado con lo obtenido, y al terminar deja los sensores como estaban y su sesión cerrada.
- **CA17 —** **Dado** un servidor con clave de equipo y un edge que ejecuta la OT 1, **cuando** alguien sin la clave lo une a otra OT o lo suelta, **entonces** recibe 401 y el edge sigue en la OT 1; repetir la sesión que ya tiene no pide clave.

Cada criterio tiene su test en `tests/test_servicios.py`, `tests/test_catalogo.py`, `tests/test_stream.py`, `tests/test_api_crud.py`, `tests/test_video.py`, `tests/test_casos.py` y `tests/test_confirmar.py`, y cada uno, salvo el CA15, su tarjeta en `/casos`; `tests/test_casos.py` falla si un criterio queda sin tarjeta.

## 9. Riesgos y decisiones abiertas

| Tema | Impacto | Qué falta decidir | Se consulta a | Decide |
| --- | --- | --- | --- | --- |
| Umbrales de la calificación | medio | ¿5 s de frescura, 75 % de confianza de cámara y 3,5 desvíos aguantan el ensayo sin falsas alarmas? `Candidata a validar` | Frente 3 | Francisco |
| Abrir una OT | medio | ADR-0003 pide que una persona la confirme; hoy el endpoint acepta `actor=sistema` | Equipo | Equipo |
| Sensores globales | medio | Con dos estaciones que usen el mismo `sensor_id` se pisan. ¿El demo tiene una sola? Desde el 2026-11-21 solo la OT en sesión se califica con esos sensores; una OT sin sesión se queda con lo que su bitácora dejó abierto (`Servicios._vigentes`, tarjeta CA2 de `/casos`). Antes, una estación con la guarda abierta y energía viva ponía en `error` a toda OT del servidor. Dos OT en sesión a la vez siguen calificándose con los mismos sensores, así que el peligro de una estación aparece en la otra: el banco lo advierte y restaura los sensores. ¿Los sensores pasan a ser por edge? | Frente 3 | Francisco |
| Juez de cámara | alto | El stub ya recibe el cuadro pero no lo mira. ¿Qué VLM y con qué latencia? `Brecha` | Frente 3 | Frente 3 |
| Autenticación | medio | El servidor del demo es abierto: cualquiera con la URL escribe. ¿Basta para el demo? | Equipo | Francisco |
| Justificación | medio | ¿El frente 4 redacta sobre los motivos de cada evento o solo al cambiar de nivel? `Brecha` | Frente 4 | Frente 4 |

## Fuentes

- [LOGICA](../../architecture/LOGICA.md), [ADR-0002](../../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md), [ADR-0003](../../decisions/0003-patrones-de-arquitectura-para-el-mvp.md), [ADR-0004](../../decisions/0004-verificacion-por-capas.md), [ADR-0006](../../decisions/0006-la-ot-nace-del-protocolo.md) y [ADR-0007](../../decisions/0007-servicios-en-vivo-sesion-stream-y-calificacion.md).
