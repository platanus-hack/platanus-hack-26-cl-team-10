# Referencias

> Documento vivo. Las 37 referencias verificadas, numeradas. El [FLUJO](../../architecture/FLUJO.md), las decisiones y el [board](./board-mantenimiento-verificado.html) las citan por número: una nueva va al final de su grupo con el número siguiente, y los números existentes no se reordenan.
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

## No encontradas

Venían en la planilla de la revisión IEEE y no aparecieron en la web abierta. No se citan sin abrirlas desde el enlace original de la planilla.

- RAFTAR-FM: Retrieval-Augmented, Feedback-Tuned Agentic Resolution for Facilities Maintenance (2025).
- Mitigating Aviation Maintenance Challenges: A Technical Evaluation of AI-Enabled Sustainment (IEEE Aerospace, 2026).
- Research on Lightweight Algorithm for Multi-Source Data Consistency Verification of Power Work Orders Using AI Large Language Model (2026).
- Address Temporal-Semantic Gap: Dynamic Semantic Alignment for Time-Series Fault Representation and Zero-Shot Diagnosis (IEEE T-ASE, 2026). S2S-FDD (26) hace lo mismo.
- Thaduri et al. (2023), sobre calidad de datos y predicción.
- Bate, Orchard y Tagle (2024), sobre los molinos SAG de Los Pelambres. Vale la pena encontrarla: es la referencia minera chilena.

## Sin enlace verificado

ISO 14224, ISO 13374, ISO 13381-1, MIMOSA OSA-CBM y TimesFM (Das et al., ICML 2024). Existen, pero no se confirmó una fuente para enlazar.
