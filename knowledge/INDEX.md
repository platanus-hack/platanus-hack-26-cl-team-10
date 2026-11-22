# Knowledge del equipo 10 — índice

> Factum vuelve verificable cualquier flujo operacional; el caso de uso es el mantenimiento de maquinaria en operaciones críticas. Acá está qué es, qué evidencia lo respalda, qué se decidió y en qué va. Track Physical World, Platanus Hack 26 Santiago.

## Empezar aquí

- [README](./README.md): qué es este knowledge y cómo leerlo.
- [CONTEXTO](./domain/CONTEXTO.md): problema, visión, alcance y criterios de evaluación de la hackathon.
- [SEGUIMIENTO](./roadmap/SEGUIMIENTO.md): **el estado vivo**. Único lugar donde se escribe el avance.

## Dominio

- [CONTEXTO](./domain/CONTEXTO.md): el problema, el operario, las industrias y cómo nos juzgan.
- [GLOSARIO](./domain/GLOSARIO.md): OT, pauta matriz, bloqueo y etiquetado, VLM y el resto del vocabulario.
- [fuentes/](./domain/fuentes/): el planteamiento del equipo y el pitch del copiloto tal como se dictaron, íntegros.

## Arquitectura

- [LOGICA](./architecture/LOGICA.md): **las reglas de negocio.** Qué es un paso y un evento, quién decide que un paso está hecho, qué puede interrumpir al operario y cómo se traspasa un turno. Se acuerda antes de escribir código.
- [Servicios en vivo](./architecture/servicios.html): **el recorrido animado** de una lectura del edge por cada servicio de la API hasta la bitácora, la calificación y la pantalla, más el catálogo de endpoints y qué admite cada recurso. GitHub no lo renderiza: descárgalo y ábrelo en el navegador.
- [SIMULADOR](./architecture/SIMULADOR.md): **la ejecución de una OT en 3D, con las pautas y los operarios de la base.** Se abre en `/simulador` del servidor del demo y desde la barra del monitor. Las pautas, sus protocolos y las personas son reales; las OT que corre son simuladas y no se escriben. Cada pauta aprobada se puede ejecutar con distintos operarios, cada uno siguiéndola o desviándose, con relevos dentro de la misma OT y un reporte que agrupa por paso. Reemplaza a la página «Del protocolo a la OT ejecutada».
- [Factum por dentro](./architecture/factum-por-dentro.html): **el detalle, en diez pantallas**, para quien quiera ir más hondo. Siete muestran lo construido, con cada número sacado del código: del protocolo a la pauta y a la OT, el recorrido de una lectura, los algoritmos de las tres capas, la calificación, el diagrama de software y hardware, y la pauta LOTO paso a paso. Tres son diseño: la celda del brazo en 3D con un borrador de su pauta, los requerimientos contra la evidencia de cada caso, y el plan del 2026-11-21: protocolo, pautas creadas con un modelo y OT por API, con la complejidad en la verificación a la medida de cada proceso. GitHub no lo renderiza: descárgalo y ábrelo en el navegador.
- [API](./architecture/API.md): **la API frente a los estándares.** Qué servicio usa cada quien, cómo entra y en qué cumple o no cumple OpenAPI, los RFC de HTTP y de tokens y la lista de OWASP, con lo que hay que decidir primero. El detalle de cada ruta lo sirve el servidor en `/referencia`.
- [Conformidad de pautas](./architecture/conformidad-de-pautas/index.html): **cómo se decide a qué protocolo pertenece una pauta y cómo se comprueba que cumple sus controles críticos** ([ADR-0016](./decisions/0016-una-pauta-sale-del-protocolo-que-aplica-a-su-tarea.md)), con lo que se construyó y sus límites. GitHub no lo renderiza: descárgalo y ábrelo en el navegador.
- [FRONTEND](./architecture/FRONTEND.md): el alcance y el reparto de la interfaz (`web/`), y cómo se despliega en Vercel.
- [FLUJO](./architecture/FLUJO.md): los pasos por actor, del protocolo a la OT y a la ejecución guiada, con evidencia, cómo construirlo y qué falta decidir en cada uno. Incluye las capas de verificación y el demo propuesto.

## Decisiones

- [Registro de decisiones](./decisions/decisions.md). Las de la mejora continua: [ADR-0014](./decisions/0014-mejora-continua-por-evidencia-y-metricas-por-pauta.md) (el ciclo, las propuestas y las mejoras sugeridas), [ADR-0016](./decisions/0016-una-pauta-sale-del-protocolo-que-aplica-a-su-tarea.md) (la conformidad con el protocolo) y [ADR-0018](./decisions/0018-la-pauta-tiene-un-protocolo-dueno-y-cada-protocolo-itera-por-separado.md) (cada protocolo itera por separado y el ciclo converge).

## Proyectos

- [Servicios en vivo · PRD](./projects/servicios-en-vivo/PRD.md): atribuir lo del edge a la OT en curso, calificarlo y llevarlo a la UI por WebSocket, y el CRUD con las reglas de negocio.
- [Skills · PRD](./projects/skills/PRD.md): las ocho skills que un agente usa en `.claude/skills/`: reconocer un proceso y generar su pauta con la capa que corresponde a cada paso, optimizarla con las tres capas, y del lado del cliente pedir, ejecutar, reportar y medir. Cómo se hace hoy en una planta, cómo se mide cada skill y qué les da la API.
- [Simulación de la mejora continua](./projects/mejora-continua/simulacion.md): OT simuladas con conductas erróneas por causa (olvido, presión, sensor que falla, ruido), por los servicios reales. Mide si la mejora continua distingue un patrón del ruido y si se adjudica mejoras que no causó. Incluye cuándo le llega el aviso al supervisor y si el ciclo converge, por causa. Generada por `scripts/simular_mejora.py`.
- [Escenarios por industria · PRD](./projects/escenarios-por-industria/PRD.md): cada forma de ejecutar un paso (saltarlo, decirlo antes, deshacer un control) en minería, eléctrica y construcción, contra cada barrera, con las reglas de capa 1 por industria y su norma. Con la [simulación de capa 2](./projects/escenarios-por-industria/capa2-simulacion.md).

## Research

- [research](./projects/research/research.md): hallazgos, vacíos y lectura prioritaria.
- [REFERENCIAS](./projects/research/REFERENCIAS.md): las 80 referencias verificadas, numeradas y con enlace.
- [notas/](./projects/research/notas/): una nota por paper leído completo.
- [Presentaciones del último año](./projects/research/tour-platanus.md): tracks, preguntas del jurado y ganadores de Santiago 2025 y las cuatro paradas del Latam Tour 26, y las preguntas que nos van a hacer. Una nota por edición en [tour/](./projects/research/tour/) y las transcripciones en [fuentes/videos-platanus/](./projects/research/fuentes/videos-platanus/).
- [PDI con OpenCV](./projects/research/pdi/pdi-opencv.md): lo medido en el curso TEL328 de Procesamiento Digital de Imágenes (filtros, bordes, segmentación, tracking) y qué le sirve al edge, con las [guías de estudio](./projects/research/pdi/control-1.html) en HTML.
- [fuentes/](./projects/research/fuentes/): la revisión IEEE original en CSV.
- [Board interactivo](./projects/research/board-mantenimiento-verificado.html): problema, flujo y referencias en una página. Resume el FLUJO con el planteamiento del equipo y los ADR 0004 a 0006; ante una diferencia, manda el FLUJO. GitHub no lo renderiza: descárgalo y ábrelo en el navegador.

## Código

- [app/README](../app/README.md): cómo correr la API y los tests, y qué archivo hace qué.
- La guía para un agente que se conecta se sirve en `/agente`, y la referencia para leer y probar cada ruta, en `/referencia`. Las dos se arman desde las rutas reales.

## Cómo se trabaja

- [CONTRIBUTING](./CONTRIBUTING.md): el estándar y cómo sube cada uno su research.
- [_TEMPLATE](./_TEMPLATE/): plantillas de PRD, de ADR y de nota de lectura.
