# Sabetta et al. 2026 — Gemini Robotics-ER 1.5 en montaje manual

> Leído completo por Francisco el 2026-11-21. REFERENCIAS 9.

**Cita.** Sabetta, N., Colabianchi, S., Costantino, F., Freire, S. K. y Niforatos, E. (2026). Evaluating Vision–Language Models Capabilities for Object, Tool, and Action Recognition in Industrial Manual Assembly Process: The Case of Gemini Robotics-ER 1.5. *IEEE Access* 14, 166819. DOI [10.1109/ACCESS.2026.3747249](https://doi.org/10.1109/ACCESS.2026.3747249). Acceso abierto, CC BY 4.0. Sapienza, Mercatorum, The Hague y TU Delft.

## Qué hicieron

Probaron un solo VLM, Gemini Robotics-ER 1.5, sin entrenarlo, sobre cuatro montajes del dataset HA-ViD. Cada montaje lo hizo un operario distinto y se grabó desde tres cámaras fijas (lateral, frontal y cenital): 12 videos de 50 segundos a 3 minutos, a 15 fps.

1. **Cuadro a cuadro, una pregunta por vez:** qué herramienta, qué objeto, qué acción, con un vocabulario cerrado de 3 herramientas, 15 objetos y 10 acciones.
2. **Cuadro a cuadro, las tres juntas** en un solo prompt.
3. **Video completo** con tres prompts: la pauta correcta, una pauta alterada (sin una fase, con dos fases cambiadas de lugar y con una acción agregada), o sin pauta. Dos profesores de ingeniería de planta evaluaron las 36 respuestas, con kappa de Cohen de 0,95.

## Lo que importa para nosotros

| Resultado | Cifra | Para el producto |
|---|---|---|
| Acción de la pauta que no ocurrió en el video | Detectada en 12 de 12 | El paso saltado es el caso del demo |
| Pasos en otro orden | Detectado en 3 de 12 | No confiar el orden del bloqueo al modelo |
| Fase hecha y omitida en la pauta | Detectada en 0 de 12 | No atrapa improvisaciones |
| Pauta correcta | Rechazada en 5 de 12 | Avisar, no bloquear |
| Fases descritas con la pauta correcta | 68% (correcta o parcial) | Borrador de pauta, no pauta |
| Fases descritas sin pauta | 54,6% | Ídem |
| Cobertura con la cámara cenital frente a la frontal (pauta correcta) | 80% frente a 56% | Probar la posición de la cámara |
| Reconocer la herramienta en un cuadro (F1 ponderado) | 58% a 77% | Confunde los dos destornilladores |
| Reconocer la acción en un cuadro (F1 ponderado) | 15% a 17% | Casi todo lo clasifica como «sostener» |
| Intervalo temporal reportado que se solapa con el real | 85% a 91% | La evidencia con marca de tiempo es usable |

Además, las descripciones sin pauta recogieron más ajustes, inspecciones y pruebas de movimiento que el operario no dice. Los autores lo proponen como punto de partida para preguntarle al experto, no como captura de su conocimiento.

## Lo que concluyen los autores

El modelo puede apoyar la redacción y la revisión de pautas, pero no establece fiabilidad para verificar cumplimiento de forma autónoma. Rechazar una pauta incorrecta no implica identificar qué está mal. Sugieren separar la verificación en pasos: primero describir el video sin ver la pauta, y después comprobar pasos sin respaldo, fases faltantes y orden por separado.

## Límites

Un solo modelo, cuatro procedimientos y cuatro operarios, en mesa de trabajo y con cámaras fijas. No hay cámara en el cuerpo ni terreno. Los propios autores advierten que los patrones no se atribuyen a los VLM en general.

## Qué cambió en el proyecto

- [ADR-0002](../../../decisions/0002-la-aplicacion-impone-el-orden-de-la-pauta.md): la aplicación impone el orden y el modelo comprueba un paso a la vez.
- [FLUJO](../../../architecture/FLUJO.md), pasos 2 y 4.
