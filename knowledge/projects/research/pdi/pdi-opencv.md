# PDI con OpenCV — hallazgos del curso TEL328

Destilado del **Taller 1 de TEL328** (2026-09-02). Dos cosas
reusables: los **hallazgos técnicos** que no estaban en las clases y aparecieron
al medir, y el **método** para armar un entregable tipo notebook con agente.

Nota de contexto: el docente enseña con `skimage` + `scipy`, pero el taller exige
OpenCV. Vale usar OpenCV y citar la equivalencia con lo visto en clases.

**Origen y estado.** Curso TEL328 Procesamiento Digital de Imágenes, USM, segundo
semestre de 2026, subido desde el vault de Francisco el 2026-11-21. Las cifras son
**mediciones propias** sobre la imagen (740×494) y el video (640×480, 20 fps, 300
cuadros) del Taller 1: `Confirmada` para esos datos, `Candidata a validar` para las
cámaras del edge. Las diapositivas y los notebooks del curso no se versionan.

## El curso en una tabla

| Unidad | Contenido |
|---|---|
| U1 | Imagen como matriz, color (RGB, HSV, Lab), ruido, filtros, bordes (Sobel, Canny), segmentación (umbral, K-Means, SLIC), cuantización (Median Cut) y tracking con Mean-Shift |
| U2 | Deep learning: clasificación, detección de objetos, segmentación semántica y generación |
| U3 | Morfología |

Bibliografía del curso: Gonzalez & Woods, *Digital Image Processing*; Bradski & Kaehler, *Learning OpenCV*.

Las guías de estudio de la U1, en HTML (GitHub no las renderiza: descárgalas y ábrelas en el navegador):

- [control-1](./control-1.html): resumen largo de las clases 1 a 6, con el mapa problema → herramienta.
- [control-1-express](./control-1-express.html): la versión corta, en orden de mini-clase.
- [guia-1-explicada](./guia-1-explicada.html): la guía 1 resuelta ejercicio por ejercicio (convolución, Canny con histéresis, K-Means, Median Cut).

## Qué le sirve a este proyecto

El edge captura cuadros con OpenCV ([edge/edge.py](../../../../edge/edge.py), [edge/colector.py](../../../../edge/colector.py)) y detecta objetos con YOLO-World ([edge/detectar.py](../../../../edge/detectar.py)); la capa 3 la juzga un VLM. Tres hallazgos de abajo aplican directo, todos `Candidata a validar` con nuestras cámaras:

1. **Cuando algo funciona, buscar dónde se rompe.** El tracking pasó de 1,38 px a 31 px de error con solo bajar los cuadros por segundo. Si el edge muestrea pocos cuadros, la oclusión (la mano del operario sobre la tarjeta) pesa más que el distractor.
2. **Una métrica puede decir lo contrario de la verdad.** El MAE premió la imagen sin filtrar frente al ruido impulsivo; el MSE la delató. Al evaluar el juez de capa 3, reportar más de una métrica.
3. **Contorno no es objeto.** Dos objetos que se tocan cuentan como uno y uno con hueco cuenta como varios. Cualquier conteo por máscara necesita morfología, no un filtro de mediana.

---

## La lección central: tres hipótesis, tres desmentidas

Lo más valioso del taller no fue ningún algoritmo. Fue que **escribí el análisis
antes de correr el experimento y las tres veces me equivoqué**, siempre en la
misma dirección: razonando correctamente sobre el método en abstracto y
falsamente sobre estos datos.

| Hipótesis | Lo que midió | Por qué falló el razonamiento |
|---|---|---|
| Lab separa mejor que RGB los objetos pálidos | Idénticos: los dos separan recién en K=8 | La distancia euclidiana no pondera canales. El tinte difería 17 unidades en `b` sobre un rango de 200 en `L` |
| Dos pelotas del mismo rojo son indistinguibles por matiz | Retroproyección 213 vs 0,7 | "Rojo" para el ojo son H=4 y H=1: pegados pero sin solapar |
| El punto débil de Mean-Shift es el distractor | Es la oclusión | Mean-Shift es **local**: nunca llega a ver al distractor |

**La regla que sale de acá:** el análisis se escribe **después** de la salida, no
antes. Y con un agente esto es un riesgo mayor, porque el agente redacta un
análisis convincente sobre resultados que todavía no existen. La contramedida es
mecánica: **toda cifra citada en prosa tiene que venir de una celda ejecutada del
propio entregable**, no de un script exploratorio aparte. Cuando encontré tres
cifras que había medido "por fuera", las volví celdas del notebook.

**El corolario, más incómodo:** un resultado bueno tampoco es evidencia. El
tracking dio 1,38 px de error medio y lo fácil era cerrar la sección. Al bajar la
tasa de cuadros a 1,3 fps se rompió con 141 px. **Cuando algo funciona, hay que
buscar dónde deja de funcionar** — si no, no sabés por qué funcionaba.

---

## Hallazgos técnicos

### Métricas: el MAE miente con ruido impulsivo

La imagen con sal y pimienta **sin filtrar** tuvo MAE 5,18, más bajo que cuatro
de las seis versiones filtradas. El MSE la delató: 968 contra ~150.

El MAE promedia errores absolutos y el ruido impulsivo afecta a pocos píxeles,
así que se diluye entre la mayoría intacta. El MSE eleva al cuadrado y castiga
los pocos errores grandes. **Elegir filtro por MAE con ruido impulsivo lleva a la
conclusión opuesta a la correcta.** Reportar siempre los dos.

### Filtros: el emparejamiento filtro-ruido es todo

| Ruido | Mejor | PSNR | Peor de los tres |
|---|---|---|---|
| Gaussiano | Gaussiano 5x5 | 28,68 dB | Mediana (27,7) |
| Sal y pimienta | **Mediana 3x3** | **32,36 dB** | Gaussiano (25,5) |

Seis decibeles de diferencia. Y el tamaño de ventana no tiene dirección fija:
con gaussiano 5x5 mejora, con sal y pimienta la mediana 5x5 **empeora** respecto
de 3x3, porque el ruido ya se acabó y lo único que sigue borrando es señal.

### Grises: la fórmula importa más que la implementación

`cv2.cvtColor(RGB2GRAY)` es **exactamente** Rec.601 (`0.299R + 0.587G + 0.114B`):
100% de píxeles idénticos si redondeás. Si truncás (`.astype(np.uint8)` directo),
difiere en el 58% de los píxeles por sesgo sistemático de medio nivel.

En cambio Rec.709 (la de la Clase 2) difiere hasta 14 niveles y el promedio simple
hasta 17. **La diferencia entre recomendaciones es un orden de magnitud mayor que
cualquier detalle de implementación.**

### Lo que ningún umbral puede resolver

Objetos cuyo nivel de gris cae **dentro** del rango del fondo son inseparables por
umbral, punto. En esta imagen el fondo iba de 202 a 235 y dos post-its estaban en
210 y 213. No es elegir mal el número: la información que los distingue es
cromática y la conversión a grises ya la descartó.

Diagnóstico rápido: si el histograma no tiene un valle entre las dos poblaciones,
no hay umbral. Otsu tampoco lo inventa.

### K-Means: Lab no es magia

El error fue asumir que cambiar a Lab bastaba. **K-Means usa distancia euclidiana
sobre los tres canales sin ponderarlos**, así que el eje que domina el rango
domina el clustering. Con `L` recorriendo 200 unidades y el tinte 17, el
algoritmo gasta sus centroides separando oscuros de claros.

Para que Lab rinda de verdad hay que **escalar `a` y `b`** antes de agrupar. Es
una decisión de diseño que el algoritmo no toma solo. *(Pendiente de probar; sería
lo primero a intentar en el Taller 2.)*

Y hay una tensión sin solución por parámetro: con K=8 se separan los objetos
pálidos, pero el fondo se parte en varios clusters (el mayor cae de 76% a 38% de
la imagen). No existe un K que satisfaga las dos cosas.

### La regla del borde para identificar el fondo

La salida de K-Means es una partición, no una máscara: falta decidir qué cluster
es fondo. Las reglas obvias fallan (el más grande, el más claro, el del centro).
La que funcionó:

```python
borde = np.concatenate([et[0,:], et[-1,:], et[:,0], et[:,-1]])
fraccion = np.bincount(borde, minlength=K) / len(borde)
clusters_fondo = np.where(fraccion >= 0.05)[0]   # varios, no uno
```

Tolera que el fondo se fragmente y no supone que sea claro. **Supuesto que
introduce:** los objetos no tocan el borde. Es la fragilidad #1 del pipeline.

### Cuantización: K-Means gana calidad, Median Cut gana tiempo

| Colores | K-Means | Median Cut (Clase 6) | Pillow |
|---|---|---|---|
| 8 | 28,42 dB / 0,86 s | 18,24 dB / 0,13 s | 21,11 dB / 0,09 s |
| 16 | 32,51 dB / 2,52 s | 21,97 dB / 0,11 s | 26,02 dB / 0,16 s |

Diez decibeles a cambio de un orden de magnitud de tiempo. K-Means optimiza
exactamente lo que mide el MSE; Median Cut no optimiza nada.

**La debilidad estructural de Median Cut:** corta por la mediana de los *píxeles*,
no por importancia visual. Con 70% de fondo uniforme gasta la mitad de sus cubos
subdividiendo grises indistinguibles. Es peor cuanto más dominante sea el fondo.

**La opción real para producción:** paleta con K-Means sobre una muestra, después
asignación barata a esa paleta. Calidad de K-Means a costo de Median Cut.

*Detalle práctico:* el `median_cut.py` del docente aplana con doble loop de Python.
Vectorizándolo con `np.indices` pasa de minutos a 0,1 s, mismo algoritmo. Y solo
acepta potencias de 2, que es por qué el taller pide 4, 8 y 16.

### Sobel y Canny

`cv2.filter2D` con los kernels de la Clase 4 da diferencia **exactamente 0,0**
contra `cv2.Sobel(ksize=3)` (ambos usan `BORDER_REFLECT_101` por defecto). Buena
verificación de que uno entiende qué hace la función.

Derivar amplifica el ruido: los píxeles sobre umbral de gradiente pasaron de
28.404 a 61.597 con ruido gaussiano, y suavizando antes volvieron a 27.323. **Por
eso Canny empieza filtrando.** El orden reducir-ruido → derivar no es negociable.

Sobel entrega una **medición** (magnitud continua); Canny entrega una **decisión**
(binaria, un píxel de ancho, con contornos conexos por histéresis). Son preguntas
distintas.

### Mean-Shift: es local, y eso lo explica casi todo

El descriptor de la Clase 6 (histograma de Hue) funcionó mejor de lo esperado:
1,38 px de error medio sobre 300 frames. Pero **no falla por robustez del
descriptor sino porque el objeto se mueve ~2 px por frame**, así que el máximo de
densidad más cercano siempre es el correcto.

La prueba de estrés (procesar 1 de cada N frames = bajar los fps):

| 1 de cada N | fps | Hue | Hue + Valor |
|---|---|---|---|
| 1 | 20 | **1,38 px** | 2,70 px |
| 10 | 2 | 1,28 px | 2,65 px |
| 15 | 1,3 | **31,38 px** ❌ | **3,00 px** ✅ |
| 20 | 1 | 33 px ❌ | 33 px ❌ |

**Se rompe en la oclusión, no en el distractor.** Con el objeto tapado por un
poste la retroproyección dentro de la ventana cae de 158 a 21; a 20 fps no importa
porque reaparece a 2 px, a 1,3 fps reaparece a 55 px y la ventana ya quedó sobre
fondo vacío, sin gradiente, derivando por el piso de ruido.

**Por qué el histograma 2D (H+V) salva el caso difícil:** no por separar mejor los
objetos, sino porque **limpia el piso de ruido**. La retroproyección media de toda
la imagen baja de 2,64 a 0,88 y el fondo claro de 0,18 a 0,00 exacto. Sin ruido
espurio, una ventana perdida no tiene de qué engancharse.

**Y el costo, que hay que medir:** en el caso fácil el 2D es *peor* (2,70 vs 1,38),
porque reparte los mismos píxeles de la ROI entre 180×64 celdas en vez de 180.
Robustez a cambio de precisión.

CamShift **no** ayudó acá: adapta la ventana según los momentos de una
retroproyección que tiene piso de ruido, así que se expande hacia zonas vacías.
Primero se arregla lo que se mide, después cómo se busca.

### Ground truth sin anotar a ojo

Para evaluar un tracker no hace falta marcar frames a mano si existe un **método
independiente** del tracker. Acá: umbral de rojo + condición sobre el canal `V`
(la pelota seguida es clara, la otra oscura). Aísla el objetivo **incluso cuando
está superpuesto al distractor**, y da los 300 frames en vez de 12 puntos.

Lo que sí hay que declarar: durante la oclusión el centroide de la parte visible
no es el centro del objeto, así que el error en esa zona sale artificialmente bajo.

### Contorno ≠ objeto

El pipeline final dio 17 detecciones sobre 18 objetos reales (recall 0,83,
precisión 0,88). Los dos modos de error son el mismo problema visto de los dos
lados: **objetos que se tocan dan un contorno y se cuentan como uno; un objeto con
un hueco del color del fondo (la esfera blanca de un reloj) da varios y se cuenta
como varios**. `findContours` sabe de componentes conexas, no de objetos.

El otro error: un filtro de mediana sobre la máscara **destruye objetos delgados**
(se perdieron 3 de 5 pinzas de ropa). El criterio de área no distingue "chico" de
"ruido". La solución es morfología (Unidad 3): apertura con elemento estructurante
alargado + cierre para tapar huecos, que arregla los dos errores a la vez.

---

## El método: cómo se armó el entregable

### Builder que parchea, no que reescribe

El notebook final **no se escribió a mano ni se reescribió entero**. Un script
carga el `.ipynb` del docente y aplica dos diccionarios:

```python
REEMPLAZOS  = {5: CODE_RUT, 10: CODE_PIXELES, ...}   # por índice de celda original
INSERCIONES = {10: [md(ANALISIS)], 19: [code(FIGURA)], ...}  # celdas nuevas después de
```

Ventajas concretas, todas verificadas en esta corrida:

- **Los enunciados quedan intactos**, byte a byte. Cero riesgo de alterar sin
  querer lo que pidió el docente.
- **Regenerable**: cuando tres análisis resultaron falsos, se reescribieron los
  strings y se rearmó todo en 2 minutos, sin editar el notebook a mano.
- **El texto largo vive en `.py`**, no dentro de JSON escapado. Editable y
  diffeable.

### `nbconvert --execute` como Restart & Run All auditable

```bash
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=900 Taller1.ipynb
```

Y la verificación que reemplaza al "confía en mí": **`execution_count` tiene que
quedar 1..n en orden y sin celdas de error**. Eso *es* la evidencia de que el
notebook corre desde cero, y es chequeable con tres líneas de Python. El checklist
del ramo lo pide y así se demuestra en vez de afirmarlo.

### Detalles operativos

- **Venv fuera de carpetas sincronizadas** (iCloud, Dropbox), creado con `uv venv`.
  Un `.venv` sincronizado son miles de archivos subiendo de fondo.
- El notebook ejecutado pesa ~14 MB por las figuras embebidas. Es lo esperado.
- Un HTML exportado (`nbconvert --to html`) es mucho más cómodo para **revisar** el
  texto de corrido antes de entregar.
- Antes de decidir cualquier cosa, **leer los notebooks de las clases**. Cambió el
  plan: reveló que el docente usa `skimage`, que Otsu y el umbral adaptativo nunca
  se enseñaron (hay que explicarlos), y que la sección de Median Cut está hecha a
  la medida de su implementación.

---

## Para la próxima

1. **No escribir una línea de análisis antes de tener la salida.** Redactar sobre
   resultados imaginados cuesta más rehacer de lo que ahorra adelantar.
2. **Cuando un resultado sale bien, diseñar el caso que lo rompa.** Es donde
   apareció todo el contenido bueno de la sección de tracking.
3. **Escalar `a` y `b` en Lab** antes de meter a K-Means, y medir si ahí sí gana a
   RGB. Quedó pendiente.
4. Probar **morfología** sobre la máscara en vez de mediana, para el conteo de
   objetos (ya es Unidad 3, así que entra en el Taller 2 o el proyecto).
5. El patrón builder + `nbconvert` sirve para **cualquier entregable tipo
   notebook**, no solo este ramo.
