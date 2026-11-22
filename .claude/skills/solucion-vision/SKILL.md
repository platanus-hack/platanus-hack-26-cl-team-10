---
name: solucion-vision
description: Dado un paso que se comprueba mirando y fotos o video de ese paso, elige y arma la solución de visión más barata que sirve (pregunta al VLM, detector de vocabulario abierto o detector entrenado) y la mide. Úsala cuando el análisis de una pauta pida `solucion-vision`, o cuando pidan verificar algo con la cámara, armar un detector, o medir si el juez de cámara responde bien una pregunta.
---

# Armar una solución de visión para un paso

Entra un paso de cámara y sus imágenes. Sale el paso con su `pregunta_visual` y, si se justifica, su `deteccion`, más los casos que lo miden. Se sube un peldaño solo si el anterior no alcanza, con el número que lo muestra.

## 0. ¿Es de cámara?

Si un sensor de la estación distingue el resultado, el paso es de sensor y esto no aplica. Si el paso es un control crítico, la cámara no basta: ninguna capa de cámara interrumpe al operario. Dilo y propón instrumentarlo; lo que sigue sirve de mientras.

## 1. Pregunta al VLM (capa 3) · siempre

1. Escribe la `pregunta_visual`: de sí o no, sobre el estado final, nombrando lo que tiene que verse, y «sí» es hecho. Mira las imágenes antes: si tú no puedes responderla con una foto, el juez tampoco.
2. Agrega casos a `datos/evals/capa3/casos.jsonl`, con la forma de los que hay. Al menos uno de cada `tipo`: `correcto`, `correcto_dificil`, `omision`, `objeto_equivocado`, `fuera_de_cuadro`, `calidad`. La imagen de cada caso va en `datos/evals/capa3/imagenes/<id>.jpg`, que no se versiona porque puede mostrar a una persona.
3. Mide:

```bash
uv run python scripts/evaluar_capa3.py
```

Mira la sección «Con imagen». Un caso sin imagen no mide nada. Lo que importa: **falsa aceptación** (dice sí a un paso mal hecho) y **falso rechazo**. Si la falsa aceptación no es cero, reescribe la pregunta y vuelve a medir antes de pensar en otro modelo. Qué tasa es aceptable no está decidido (`Brecha`): entrega el número y que decida una persona.

## 2. Detector de vocabulario abierto (capa 2) · si el paso es «el objeto está» o «ya no está»

Sin entrenar nada. Sirve cuando la pregunta se reduce a la presencia de un objeto que tiene nombre común.

```bash
cd edge && .venv/bin/python detectar.py --clases "<objeto en inglés>" --foto <foto>
```

Pruébalo en fotos con el objeto y sin él. La capa 2 solo cierra el paso si **todas** las detecciones de la ventana pasan de 0,8, y solo decide «ya no está» si ninguna llega a 0,25 (`reglas.por_deteccion`). Si las confianzas no quedan a esos lados, el detector no decide y el paso sigue en el VLM: no bajes los umbrales.

Si sirve: agrega `"deteccion": {"clase": "<objeto>", "presente": true}` al paso, pon `capa_minima` en 2, y agrega la clase a la estación. El detector la recibe de la pauta: en modo edge no hay nada más que hacer (el edge pregunta qué clases pide la OT en sesión y las suma a las suyas); en modo servidor hay que exportar el modelo de nuevo con `edge/exportar_onnx.py --pautas <la pauta> ../datos/pauta-*.json` ([cómo se despliega](../../../app/README.md#dónde-corre-yolo-dos-modos)). Mientras el detector no conozca la clase, el paso lo cierra el VLM.

## 3. Detector entrenado · solo con el número que lo pida

Cuesta fotos y mantenerlo. Se justifica cuando los peldaños 1 y 2 se midieron y no alcanzan: `scripts/analizar.py ejecuciones` marca el paso (la cámara no lo cerró en varias OT), o el detector reconoce el objeto de cerca pero a la distancia de la cámara de la estación sus confianzas caen a los dos lados de 0,8. Antes de eso, no.

Hacen falta tres o más fotos de cerca de cada objeto, por lados distintos (la última de cada clase se aparta para medir), y los cuadros de la cámara que deja `edge/correr_colector.command`:

```bash
cd edge && .venv/bin/python entrenar.py --device mps --fotos "red soda can=data/fotos-polin/rojo-*.jpg" "green soda can=data/fotos-polin/verde-*.jpg"
```

`edge/entrenar.py` recorta el objeto de cada foto, lo pega chico y girado sobre los cuadros de la cámara, afina YOLO-World con esas escenas y lo mide contra el modelo base con los umbrales de la capa 2. Las fotos no se etiquetan a mano ni se versionan (`edge/data/` está ignorado). Deja `datos/modelos/yolo-factum.pt`, que entrega lo mismo que el base, `{clase, conf, caja}`: en modo edge va con `edge.py --pesos`, y en modo servidor se exporta con `exportar_onnx.py --pesos` y `DETECTOR_ONNX` apunta al archivo nuevo.

La medida es sobre escenas armadas, no sobre la estación. Antes de dejarlo por defecto, pruébalo con la cámara puesta donde va a estar.

## Entregar

El paso como queda, el informe del eval y qué peldaño se eligió y por qué no el siguiente. Si cambia la pauta, es una versión nueva y la aprueba una persona.
