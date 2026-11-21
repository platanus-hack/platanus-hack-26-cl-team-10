# Referencias

> Documento vivo. Las 43 referencias verificadas, numeradas. El [FLUJO](../../architecture/FLUJO.md), las decisiones y el [board](./board-mantenimiento-verificado.html) las citan por número: una nueva va al final de su grupo con el número siguiente, y los números existentes no se reordenan.
>
> De casi todas se leyó solo el resumen. Las leídas completas tienen nota en [notas/](./notas/).

## Bitácora y texto de las OT

1. Brundage, Sexton, Hodkiewicz, Dima y Lukens (2021). [Technical language processing: Unlocking maintenance knowledge](https://doi.org/10.1016/j.mfglet.2020.11.001). *Manufacturing Letters* 27, 42–46. El marco del área.
2. Sexton, Brundage, Hoffman y Morris (2017). [Hybrid datafication of maintenance logs from AI-assisted human tags](https://www.nist.gov/publications/hybrid-datafication-maintenance-logs-ai-assisted-human-tags). IEEE Big Data. El sistema sugiere, el técnico confirma.
3. Sexton, Hodkiewicz y Brundage (2019). [Categorization Errors for Data Entry in Maintenance Work-Orders](https://papers.phmsociety.org/index.php/phmconf/article/view/790). PHM Society. Los errores al registrar son sistemáticos.
4. Bikaun y Hodkiewicz (2021). [Semi-automated Estimation of Reliability Measures from Maintenance Work Order Records](https://papers.phmsociety.org/index.php/phme/article/download/2950/1760). PHM Europe. El MTBF va de 97 a 226 días según el registro.
5. Hodkiewicz y Ho (2016). [Cleaning historical maintenance work order data for reliability analysis](https://www.emerald.com/insight/content/doi/10.1108/JQME-04-2015-0013/full/html). *Journal of Quality in Maintenance Engineering* 22(2), 146–163. Qué falta en las OT históricas.
6. Bikaun, French, Stewart, Liu y Hodkiewicz (2024). [MaintIE: A Fine-Grained Annotation Schema and Benchmark for Information Extraction from Maintenance Short Texts](https://aclanthology.org/2024.lrec-main.954/). LREC-COLING. OT reales anotadas, con [datos y código](https://github.com/nlp-tlp/maintie).
7. [Plant Memory: Technical Language Processing and a Verified Maintenance Ontology for Agent-Accessible Failure Knowledge from SAP PM Work Orders](https://arxiv.org/pdf/2610.19131) (2026). arXiv 2610.19131. OT de SAP PM en una planta.
8. [KPI Extraction from Maintenance Work Orders: A Comparison of Expert Labeling, Text Classification and AI-Assisted Tagging](https://arxiv.org/abs/2311.04064) (2023). arXiv 2311.04064. 88% menos tiempo de etiquetado.

## Verificar la ejecución con visión

9. Sabetta, Colabianchi, Costantino, Freire y Niforatos (2026). [Evaluating Vision–Language Models Capabilities for Object, Tool, and Action Recognition in Industrial Manual Assembly Process: The Case of Gemini Robotics-ER 1.5](https://doi.org/10.1109/ACCESS.2026.3747249). *IEEE Access* 14, 166819 y siguientes. Leído completo: ver la [nota](./notas/2026-sabetta-gemini-robotics-er.md).
10. Haneji et al. (2025). [EgoOops: A Dataset for Mistake Action Detection from Egocentric Videos Referring to Procedural Texts](https://arxiv.org/abs/2410.05343). ICCV Workshops. Contrasta el video con el texto de la pauta.
11. [PREGO: online mistake detection in PRocedural EGOcentric videos](https://arxiv.org/abs/2404.01933) (2024). CVPR. Detecta el error mientras ocurre. Autoría sin verificar.
12. [TI-PREGO: Chain of Thought and In-Context Learning for Online Mistake Detection in PRocedural EGOcentric Videos](https://arxiv.org/abs/2411.02570) (2024). arXiv 2411.02570. Usa un LLM para anticipar el paso siguiente.
13. Schoonbeek et al. (2024). [IndustReal: A Dataset for Procedure Step Recognition Handling Execution Errors in Egocentric Videos in an Industrial-Like Setting](https://arxiv.org/pdf/2310.17323). WACV. Con [código y pesos](https://github.com/TimSchoonbeek/IndustReal).
14. Lee, Lu, Zhang, Hoai y Elhamifar (2024). [Error Detection in Egocentric Procedural Task Videos (EgoPER)](https://www.khoury.northeastern.edu/home/eelhami/egoper.htm). CVPR. Entrena solo con videos sin error.
15. Seminara, Farinella y Furnari (2024). [Differentiable Task Graph Learning: Procedural Activity Representation and Online Mistake Detection from Egocentric Videos](https://arxiv.org/abs/2406.01486). NeurIPS. Aprende el grafo de la tarea. Con [código](https://github.com/fpv-iplab/Differentiable-Task-Graph-Learning).
16. Bansal, Arora y Jawahar (2022). [My View is the Best View: Procedure Learning from Egocentric Videos](https://arxiv.org/abs/2207.10883). ECCV. Descubre los pasos sin supervisión (EgoProceL).
17. Ragusa et al. (2024). [ENIGMA-51: Towards a Fine-Grained Understanding of Human-Object Interactions in Industrial Scenarios](https://arxiv.org/abs/2309.14809). WACV. Reparación de tarjetas eléctricas.
18. Manuri, Pizzigalli y Sanna (2019). [A State Validation System for Augmented Reality Based Maintenance Procedures](https://www.doi.org/10.3390/APP9102115). *Applied Sciences* 9(10), 2115. Valida cada paso por su estado final. [PDF abierto](https://iris.polito.it/retrieve/handle/11583/2755032/248400/applsci-09-02115.pdf).
19. Rukubayihunga, Didier y Otmane (2015). [Reprojection error as a new metric to detect assembly/disassembly maintenance tasks](https://researchr.org/publication/RukubayihungaDO15). Antecedente en IEEE.
20. [Automation of Monitoring Compliance with Technological Regulations Using the Example of the Process of Filling Petroleum Products](https://doi.org/10.3390/jimaging12080349) (2026). *Journal of Imaging* 12(8), 349. El único caso en terreno real.
21. [AI-based worker guidance in assembly and disassembly operations using multimodal ego/exo-centric data capture and structured task knowledge](https://arxiv.org/pdf/2608.22617) (2026). arXiv 2608.22617. Captura al experto.
22. [Vision-Based Mistake Analysis in Procedural Activities: A Review of Advances and Challenges](https://arxiv.org/pdf/2510.19292) (2025). arXiv 2510.19292. El mapa del área.
23. Chen. [A Design of a Digital Lockout Tagout System with Machine Learning](https://digitalcommons.calpoly.edu/theses/2629/). Tesis de magíster, Cal Poly. Bloqueo con candados inteligentes, sin cámara.

## Sensores, diagnóstico y OT

24. Aqueveque, Radrigan, Pastene, Morales y Guerra (2021). [Data-Driven Condition Monitoring of Mining Mobile Machinery in Non-Stationary Operations Using Wireless Accelerometer Sensor Modules](https://doaj.org/article/69042fd186ed4db4bec069840d11143a). *IEEE Access* 9, 17365–17381. Minería chilena, sensores sin integración.
25. O'Donncha, Zhou, Martinez, Rayfield, Heath, Langbridge y Vaculin (2026). [Evidence-Driven Reasoning for Industrial Maintenance Using Heterogeneous Data](https://aclanthology.org/2026.acl-industry.50/). ACL Industry Track. Lo más parecido al ciclo completo. Benchmark: [AssetOpsBench](https://ibm.github.io/AssetOpsBench/).
26. Li y Zhao (2026). [S2S-FDD: Bridging Industrial Time Series and Natural Language for Explainable Zero-shot Fault Diagnosis](https://arxiv.org/abs/2603.08048). arXiv 2603.08048. Diagnóstico sin datos de falla.
27. Vidyaratne, Lee, Kumar, Watanabe, Farahat y Gupta (2024). [Generating Troubleshooting Trees for Industrial Equipment using Large Language Models](https://ieeexplore.ieee.org/document/10626823/). IEEE ICPHM. Pautas de diagnóstico desde manuales.
28. [Generating Troubleshooting Trees With FMEA Using Large Language Models](https://ieeexplore.ieee.org/document/11062049/). IEEE. Lo mismo, partiendo del FMEA.
29. [RAFT: A Stateful Retrieval-Augmented Framework for Troubleshooting Agents](https://arxiv.org/abs/2609.20754) (2026). EMNLP Industry Track. Recupera casos históricos por etapa.
30. [A Hybrid Vision-Language Architecture for Automated Defect Reasoning and Report Generation in Industrial Inspection](https://arxiv.org/pdf/2605.26533) (2026). arXiv 2605.26533. Reporte anclado en protocolos.
31. Ansari et al. (2024). [Chronos: Learning the Language of Time Series](https://arxiv.org/pdf/2403.07815). TMLR. Series de tiempo sin entrenar por equipo.
32. Goswami, Szafer, Choudhry, Cai, Li y Dubrawski (2024). [MOMENT: A Family of Open Time-series Foundation Models](https://arxiv.org/pdf/2402.03885). ICML. Alternativa abierta a Chronos.

## Seguridad y cumplimiento de la pauta

33. Peres, Smith y Sasangohar (2020). [Worker-centered investigation of issues with procedural systems](https://acelab.tamu.edu/wp-content/uploads/sites/23/2020/09/1-s2.0-S0950423020305519-main.pdf). *Journal of Loss Prevention in the Process Industries*. Por qué se desvían. Petroquímica.
34. Reason y Hobbs (2003). [Managing Maintenance Error: A Practical Guide](https://www.routledge.com/Managing-Maintenance-Error-A-Practical-Guide-1st-Edition/Reason-Hobbs/p/book/9780754615910). Ashgate. El clásico del error en mantenimiento.
35. FAA. [Procedural non-compliance](https://www.faa.gov/about/initiatives/maintenance_hf/procedural_non-compliance). No seguir el procedimiento, en aviación.
36. Diario Financiero. [¿Cuánto han aumentado realmente los accidentes mineros?](https://www.df.cl/regiones/cuanto-han-aumentado-realmente-los-accidentes-mineros-fatalidades) Cifras de Sernageomin, vía prensa. Falta la fuente primaria.
37. MSHA. [Accident, Injuries and Illnesses Data Set](https://www.msha.gov/data-and-reports/data-sources-and-calculators/data-resources/mdsrg/accident-injuries-and-illnesses-data-set). Accidentes mineros de EE.UU. desde 1983.

## Costo de la detención

38. Reporte Minero (2026-07-01). [Ingemerca: sistemas de transferencia minera que reducen paradas millonarias](https://www.reporteminero.cl/noticia/entrevistas/2026/07/ingemerca-soluciones-transferencia-minera-paradas-planta). Entrevista a Ricardo Segovia, gerente general de Ingemerca: una parada de planta no programada cuesta entre USD 100.000 y 300.000 por hora y suele durar 4 o 5 horas. Es la estimación de un proveedor que vende la solución, sin estudio detrás. El mismo ejecutivo dijo USD 150.000 a 200.000 por hora en [REDIMIN, 2025-04-29](https://www.redimin.cl/innovaciones-de-ingemerca-en-2025-reducen-riesgos-y-costos-en-transporte-de-minerales-por-correas), la única nota que liga la cifra a las correas. Leídas completas.
39. CNN Chile. [Hasta $200.000 USD: Los pequeños errores en terreno que pueden costar millones a la minería](https://www.cnnchile.com/pais/hasta-200-000-usd-los-pequenos-errores-en-terreno-que-pueden-costar-millones-a-la-mineria/). Sin fecha visible en la página. Una hora de detención no planificada cuesta entre USD 40.000 y más de 200.000 «según estimaciones del sector»; menciona estudios de ABB sin título ni año. No habla de correas. Leída completa.

## Fatalidades y controles críticos

40. ICMM (2026). [Safety Performance: Benchmarking progress of ICMM company members in 2025](https://www.icmm.com/en-gb/research/health-safety/benchmarking-2025-safety-data). Fuente primaria, leída el 2026-11-21. **La «ejecución inefectiva del control» fue la falla de control más común en los incidentes fatales de 2025: 19 de 26.** De 28 incidentes fatales, dos quedaron en investigación y se excluyeron de esa clasificación. El reporte pide foco continuo en la identificación, implementación y **verificación** de los controles críticos, y entre los peligros de alta consecuencia nombra el **aislamiento de energía**, que es el bloqueo y etiquetado. La página ofrece un PDF que no se abrió.
41. ICMM (2026). [ICMM reports 2025 safety performance of members](https://www.icmm.com/en-gb/news/2026/2025-safety-performance). Fuente primaria, leída el 2026-11-21. 39 fallecidos en 2025, 43 en 2024 y 35 en 2023. De 26 miembros, 14 sin fallecidos. Caída de roca y equipo móvil, diez cada uno; dos incidentes catastróficos explican 13. Sudamérica y África, once cada una. 6.183 lesiones registrables, la cifra más baja desde que ICMM mide, en 2008.
42. Mining Weekly (2026-07-30). [ICMM calls for reinforcement of risk prevention efforts as fatalities among members remains high](https://www.miningweekly.com/article/icmm-calls-for-further-action-as-fatalities-among-members-remain-relatively-high-2026-07-30). Leída completa el 2026-11-21. Aporta lo que no está en las páginas de ICMM: trabajo en altura e irrupción, siete cada uno, con lo que esos cuatro peligros explican 34 de los 39; Chile tuvo seis fallecidos y uno de los dos incidentes catastróficos del año fue en Chile, por caída de roca; la tendencia sube desde 2021 y revierte una baja anterior.
43. Emol (2026-10-14). [Trece fallecidos en 2026: Gobierno convoca a una mesa transversal por la seguridad en la minería](https://www.emol.com/noticias/Economia/2026/10/14/1214147/mineria-fallecimientos-mesa-de-seguridad.html). Verificado el titular el 2026-11-21; el cuerpo de la nota no se pudo extraer de la página. Cifras de Sernageomin vía prensa, igual que (36). Falta la fuente primaria.

## No encontradas

Venían en la planilla de la revisión IEEE y no aparecieron en la web abierta. No se citan sin abrirlas desde el enlace original de la planilla.

- RAFTAR-FM: Retrieval-Augmented, Feedback-Tuned Agentic Resolution for Facilities Maintenance (2025).
- Mitigating Aviation Maintenance Challenges: A Technical Evaluation of AI-Enabled Sustainment (IEEE Aerospace, 2026).
- Research on Lightweight Algorithm for Multi-Source Data Consistency Verification of Power Work Orders Using AI Large Language Model (2026).
- Address Temporal-Semantic Gap: Dynamic Semantic Alignment for Time-Series Fault Representation and Zero-Shot Diagnosis (IEEE T-ASE, 2026). S2S-FDD (26) hace lo mismo.
- Thaduri et al. (2023), sobre calidad de datos y predicción.
- Bate, Orchard y Tagle (2024), sobre los molinos SAG de Los Pelambres. Vale la pena encontrarla: es la referencia minera chilena.
- Mendoza et al. (2024), sobre cuánto se desvían los técnicos de las pautas. Probablemente es [este PDF](https://acelab.tamu.edu/wp-content/uploads/sites/23/2024/04/j75.pdf), del mismo laboratorio de Peres (33), que lo cita; no se confirmó el título.

## Mencionadas, sin verificar

Aparecieron en la conversación de research o en búsquedas, pero no se confirmó la fuente ni se leyeron. No llevan número hasta verificarlas.

- **HoloAssist** (Wang et al., ICCV 2023): asistente que acompaña a una persona en una tarea física y detecta errores. Modelo de interacción con el operario.
- **Ego-Exo4D** (Grauman et al., CVPR 2024): reconocimiento de pasos clave y nivel de destreza; compara experto y novato.
- **Tixier et al. (2016)**, *Automation in Construction*: NLP sobre reportes de accidentes de construcción para extraer precursores.
- **Conte et al. (2021)**: los errores humanos en el texto libre de las OT no son aleatorios y distorsionan los indicadores.
- **MaintNorm** (grupo de Hodkiewicz): unos 12.000 ejemplos para normalizar el texto de las OT.
- **Van der Aalst (2016)**, *Process Mining: Data Science in Action*: descubrir procesos desde los registros de eventos, como los estados de las OT en SAP PM.
- **Arai et al. (2000)**, *CIRP Annals*: origen del término *plug-and-produce*.
- **TimesFM** (Das et al., ICML 2024, arXiv 2310.10688): modelo fundacional de series de tiempo de Google.
- **Wang et al. (2026), HCMA_GPT**: [diagnóstico de fallas no vistas en maquinaria rotatoria](https://strathprints.strath.ac.uk/96594/1/Wang-etal-2026-Towards-Generalizable-Fault-Diagnosis-via-LLM-Driven-Hierarchical-Cross-Modal-Alignment.pdf) alineando vibración y texto.
- **Cui et al.**, A*STAR: [marco de calidad de datos para mantenimiento predictivo](https://oar.a-star.edu.sg/storage/3/3rngr1xj2e/pdm-data-quality-assessment-framework-20240226.pdf), probado en remolcadores.
- **PARAM** ([arXiv 2508.04714](https://arxiv.org/html/2508.04714v2)) y **LLM-R** ([arXiv 2411.04476](https://arxiv.org/pdf/2411.04476)): agentes con RAG para planificar mantenimiento.
- **Tesis del MIT** sobre un [chatbot multimodal para causa raíz](https://dspace.mit.edu/bitstream/handle/1721.1/163337/LorenteAnon-cla6-mgt-2025-thesis.pdf?sequence=1&isAllowed=y), con sensores, OT y video.
- **Piper Alpha (1988) e informe Cullen**: el caso clásico de un accidente de mantenimiento por un relevo de turno y un permiso de trabajo mal traspasados. Citado de memoria; sirve para el [relevo de turno](../../architecture/FLUJO.md#5-bitácora-y-relevo-de-turno).
- **Proveedores de verificación de bloqueo con cámara**, no revisados por pares: [Roboflow](https://roboflow.com/ai/lockout-tagout-verification) e [iFactory](https://ifactoryapp.com/ai-vision-camera/ai-vision-lockout-tagout-verification).
- **«Los miembros de ICMM cubren cerca de un tercio de la industria»**: se afirmó al preparar el pitch y **ninguna** de las fuentes abiertas (40), (41) ni (42) lo dice. No se usa hasta encontrar de dónde sale.
- **PDF del benchmarking de ICMM 2025**: existe y está enlazado desde (40); no se abrió. Es la fuente más completa si se necesita el detalle por peligro.
- **Delve / IGF (2020)**, [How unsafe is ASM?](https://delvedatabase.org/uploads/resources/2020-SoS_OHS-1_How-unsafe-is-ASM.pdf): 592 muertes en minería artesanal en 2019, contando solo noticias en inglés. Enlace no abierto.
- **Prensa del cierre estadístico 2025 de Sernageomin**: [Diario Estrategia](https://www.diarioestrategia.cl/texto-diario/mostrar/6059013/seis-trabajadores-fallecidos-cinco-accidentes-mineros-tres-semanas-anticipar-riesgo-vuelve-centro-debate), [Redimin](https://www.redimin.cl/?p=57859) y [The Clinic](https://www.theclinic.cl/2026/10/14/es-un-fracaso-del-sistema-que-nos-duele-e-indigna-la-critica-de-sernageomin-por-accidentes-fatales-en-minas-tras-siete-muertes-en-21-dias/). Repiten lo que ya sostiene (36); no abiertas.
- **Más cobertura del reporte ICMM**: [Engineering News](https://engineeringnews.co.za/article/icmm-calls-for-further-action-as-fatalities-among-members-remain-relatively-high-2026-07-30), [Canadian Mining Journal](https://www.canadianminingjournal.com/?p=1003789055) y [Mining.com](https://www.mining.com/?p=1183238). Las dos primeras devolvieron 403; se usó (42) y las fuentes primarias en su lugar.

## Sin enlace verificado

ISO 14224, ISO 13374, ISO 13381-1, MIMOSA OSA-CBM y TimesFM (Das et al., ICML 2024). Existen, pero no se confirmó una fuente para enlazar.
