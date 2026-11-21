# ADR-0008 — Los escenarios por industria corren en una caja aislada y cada barrera se mide con su herramienta

> Estado: `proposed` · Fecha: 2026-11-21

## Contexto

Queremos saber cómo responde cada barrera del [ADR-0004](./0004-verificacion-por-capas.md) a las formas reales de equivocarse, en minería, eléctrica y construcción, y mejorar cada una con evidencia. El banco `/casos` corre los criterios del servicio contra un servidor vivo, y eso tiene tres límites para este fin. Primero, los sensores son una tabla global ([PRD de servicios en vivo §9](../projects/servicios-en-vivo/PRD.md#9-riesgos-y-decisiones-abiertas)). Segundo, el juez de cámara del servidor no se puede forzar sin afectar a otras OT. Tercero, el tiempo no se puede adelantar. Además, las tres barreras no se mejoran igual: la capa 1 depende de reglas, la capa 2 de un detector y la capa 3 de un modelo.

## Decisión

1. **Un escenario es una industria por un patrón de ejecución.** Lleva sus pasos (lecturas, declaraciones, cuadros, tiempo), lo esperado y su fuente: una regla de LOGICA, un ADR o una norma numerada en REFERENCIAS. Los patrones son los mismos en las tres industrias, así la matriz se lee por fila. Viven en `app/escenarios.py` y se sirven en `GET /escenarios`.
2. **Corren en una caja aislada.** Usan base en memoria, bus propio, video en un directorio temporal, y juez y reloj inyectados, pasando por el `servicios.py` real. Así no tocan la bitácora ni los sensores del servidor, dan lo mismo en local que en la VM y corren los 66 en menos de un segundo.
3. **Una brecha es un fallo esperado, con su razón.** El test exige que un escenario con brecha siga sin cumplir. Si alguien la cierra, el test lo avisa para quitar la marca. En la matriz, una brecha es ámbar y una falla, roja: algo que funcionaba se rompió.
4. **Cada barrera se mide con su herramienta.** La matriz prueba la política, es decir, qué hace el sistema con lo que la barrera dice. La calidad del modelo de cada barrera se mide aparte:
   - capa 1: reglas por industria con su norma;
   - capa 2: `scripts/simular_capa2.py`, detectores contra fallas sintéticas;
   - capa 3: `scripts/evaluar_capa3.py`, el juez contra escenas etiquetadas.
5. **Las imágenes del eval no se versionan.** Pueden mostrar a una persona y el repo es público. Se versiona el manifiesto de las escenas.

## Alternativas consideradas

- **A — Correr los escenarios por HTTP contra el servidor, como los CA:** muestra el camino real. Pero sus sensores son globales, el juez no se puede inyectar y el tiempo no se adelanta, y cada corrida deja una OT en la bitácora. El camino HTTP ya lo cubren los CA del servicio.
- **B — Escribir los escenarios como JSON:** se pueden compartir sin Python. Pero 66 escenarios son 22 patrones con 3 descripciones de industria, y en JSON cada cambio de patrón se repite tres veces. Como `GET /escenarios` ya entrega JSON, no hace falta.
- **C — Marcar las brechas con `skip`:** es más simple, pero una brecha que se cierra sola pasa inadvertida.

## Consecuencias

- Una industria nueva es una pauta y una descripción de sus sensores. Sus 22 escenarios salen solos y los que no aplican quedan a la vista como brecha.
- Las brechas de la matriz se vuelven decisiones con nombre ([PRD §9](../projects/escenarios-por-industria/PRD.md#9-riesgos-y-decisiones-abiertas)). Las de capa 1 piden reglas en `reglas.py` y tocan el contrato. Las de frescura, sin cuadro y declaración tardía se cierran en `servicios.py`.
- La caja no prueba HTTP ni el WebSocket real. Lo que reporta del stream es lo que el servicio publicó en su bus.

## Pendientes y no verificado

- Los resultados de la capa 2 salen de señales sintéticas: descartan detectores, no calibran umbrales. `Candidata a validar` con datos del ensayo.
- El eval de capa 3 no tiene imágenes todavía. `Brecha`.
- Las pautas de eléctrica y construcción son de demostración. Las escribió el equipo siguiendo las normas citadas, no salen de un procedimiento real de un cliente. `Candidata a validar`.

## Referencias

- [ADR-0004](./0004-verificacion-por-capas.md), [ADR-0005](./0005-producto-general-mineria-como-caso-del-demo.md) y [ADR-0007](./0007-servicios-en-vivo-sesion-stream-y-calificacion.md).
- [PRD de escenarios por industria](../projects/escenarios-por-industria/PRD.md).
- REFERENCIAS 9, 13 y 44 a 55.
