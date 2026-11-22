# Registro de decisiones

> Una línea por decisión, la más nueva arriba. Las estructurales tienen su ADR; las menores pueden vivir solo acá.

| ADR | Fecha | Decisión | Estado |
|---|---|---|---|
| [0017](./0017-la-capa-3-queda-con-el-vlm-sin-medir-por-ahora.md) | 2026-11-21 | La capa 3 queda con el VLM y sin medir por ahora; el orden para bajarle el peso queda escrito | `accepted` |
| [0016](./0016-una-pauta-sale-del-protocolo-que-aplica-a-su-tarea.md) | 2026-11-22 | Una pauta se atribuye al protocolo cuyo alcance cubre su tarea; si no cumple un control crítico, se registra como hallazgo y se corrige con una versión nueva, nunca quitando la atribución | `proposed` |
| [0015](./0015-reconocer-procesos-con-skills-de-agente-y-un-criterio.md) | 2026-11-21 | Los procesos los reconoce un agente con skills (reconocer, optimizar, regla, visión); lo comprobable lo comprueba `app/analisis.py`, y un criterio en el código decide qué se analiza | `proposed` |
| [0014](./0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md) | 2026-11-21 | El operario deja observaciones; la pauta mejora desde señales repetidas en el mismo paso, que valida el supervisor y se comprueban con la versión nueva; las métricas se leen de la bitácora por pauta, equipo, paso y día, nunca por persona | `proposed` |
| [0013](./0013-el-pitch-copiloto-del-operario-sin-supervisor-encima.md) | 2026-11-21 | Factum se presenta como el copiloto del operario: cada trabajo queda verificado sin un supervisor encima. No se vende como un supervisor que mira todo el tiempo; el conocimiento del operario y las métricas son visión hasta construirlos | `proposed` |
| [0012](./0012-login-y-clientes-cada-empresa-ve-lo-suyo.md) | 2026-11-21 | El servicio para clientes pide login; cada empresa ve solo sus OT y las pautas que el equipo le habilitó, con roles supervisor y operador | `proposed` |
| [0011](./0011-protocolos-y-pautas-por-servicio-interno-ot-por-servicio-al-cliente.md) | 2026-11-21 | Los protocolos y las pautas se cargan por un servicio interno del equipo, atribuidos entre sí de muchos a muchos; el cliente solo pide OT de las pautas aprobadas | `proposed` |
| [0010](./0010-demo-brazo-robotico-en-una-celda-con-corte-local.md) | 2026-11-21 | El demo es un brazo robótico en una celda; el corte de energía lo hace el ESP32 por su cuenta y se presenta como integración opcional | `accepted` |
| [0009](./0009-flujo-operacional-verificable-mantenimiento-como-caso-de-uso.md) | 2026-11-21 | El producto vuelve verificable cualquier flujo operacional; el mantenimiento de maquinaria es el caso de uso. Extiende al 0005 | `proposed` |
| [0008](./0008-escenarios-por-industria-en-una-caja-aislada.md) | 2026-11-21 | Los escenarios por industria corren en una caja aislada; cada barrera se mide con su herramienta (reglas, simulación, eval) | `proposed` |
| [0007](./0007-servicios-en-vivo-sesion-stream-y-calificacion.md) | 2026-11-21 | Servicios en vivo: la sesión une el edge con la OT, un WebSocket por OT y la calificación ok · warning · error se calcula por capa | `proposed` |
| [0006](./0006-la-ot-nace-del-protocolo.md) | 2026-11-21 | La OT nace del protocolo: el disparo puede ser calendario, pedido o falla | `proposed` |
| [0005](./0005-producto-general-mineria-como-caso-del-demo.md) | 2026-11-21 | El producto es general; la minería es el caso del demo. Reemplaza al 0001 | `proposed` |
| — | 2026-11-21 | Predecir fallas, abrir OT automáticas y cruzar con OT históricas quedan como visión, fuera del alcance del demo y del pitch | `proposed` |
| [0004](./0004-verificacion-por-capas.md) | 2026-11-21 | Verificación en tres capas: sensores y reglas primero, aprendizaje automático sobre señales, y VLM solo para lo que se ve o se redacta | `proposed` |
| [0003](./0003-patrones-de-arquitectura-para-el-mvp.md) | 2026-11-21 | Tres patrones ahora (registro que solo agrega, aprobación humana, pauta versionada); el resto espera a que duela | `proposed` |
| [0002](./0002-la-aplicacion-impone-el-orden-de-la-pauta.md) | 2026-11-21 | La aplicación impone el orden de la pauta y el VLM solo comprueba el paso actual | `proposed` |
| [0001](./0001-mineria-como-mercado-de-entrada.md) | 2026-11-21 | Minería como mercado de entrada; eléctrica y construcción como expansión | `superseded by 0005` |
| — | 2026-11-21 | Fuera de alcance: gemelos digitales basados en física | `accepted` |
| — | 2026-11-21 | El knowledge vive en `knowledge/` y el estado vivo solo en `roadmap/SEGUIMIENTO.md` | `proposed` |
