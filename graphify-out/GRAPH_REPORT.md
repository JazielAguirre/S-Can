# Graph Report - .  (2026-05-12)

## Corpus Check
- 25 files · ~50,000 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 186 nodes · 208 edges · 21 communities (14 shown, 7 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.83)
- Token cost: 31,064 input · 59,163 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Frontend UI Layer|Frontend UI Layer]]
- [[_COMMUNITY_Model Training Pipeline|Model Training Pipeline]]
- [[_COMMUNITY_Dataset Preparation|Dataset Preparation]]
- [[_COMMUNITY_Express API Server|Express API Server]]
- [[_COMMUNITY_AI Service & Breeds Catalog|AI Service & Breeds Catalog]]
- [[_COMMUNITY_Backend Controllers & Routes|Backend Controllers & Routes]]
- [[_COMMUNITY_ML Concepts & Documentation|ML Concepts & Documentation]]
- [[_COMMUNITY_FastAPI Inference Server|FastAPI Inference Server]]
- [[_COMMUNITY_Frontend App Shell|Frontend App Shell]]
- [[_COMMUNITY_Inference Endpoints|Inference Endpoints]]
- [[_COMMUNITY_Image Utils & Processing|Image Utils & Processing]]
- [[_COMMUNITY_History Module|History Module]]
- [[_COMMUNITY_Stats Module|Stats Module]]
- [[_COMMUNITY_History JS Files|History JS Files]]
- [[_COMMUNITY_Stats JS Files|Stats JS Files]]
- [[_COMMUNITY_Health Check Endpoint|Health Check Endpoint]]
- [[_COMMUNITY_History Save|History Save]]
- [[_COMMUNITY_History Clear|History Clear]]
- [[_COMMUNITY_Stats Record|Stats Record]]
- [[_COMMUNITY_Stats Clear|Stats Clear]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 9 edges
2. `main.js — Frontend Orchestrator` - 9 edges
3. `train.py main — Training Orchestrator` - 7 edges
4. `ARCHITECTURE.md — System Architecture Document` - 7 edges
5. `analyzeImage()` - 6 edges
6. `AI_PIPELINE.md — Machine Learning Pipeline Deep-dive` - 6 edges
7. `README.md (docs/) — Project Overview` - 6 edges
8. `README.md (root) — Public Project README` - 6 edges
9. `process_breed()` - 5 edges
10. `main()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `validateFile — Client-side File Validator` --semantically_similar_to--> `API.md — HTTP Endpoint Reference`  [INFERRED] [semantically similar]
  frontend/js/main.js → docs/API.md
- `main.js — Frontend Orchestrator` --conceptually_related_to--> `Rationale: Invariant JSON Contract from Node.js to Frontend`  [INFERRED]
  frontend/js/main.js → docs/ARCHITECTURE.md
- `IIFE Module Pattern for Frontend Encapsulation` --rationale_for--> `DogDexHistory — IIFE History Module`  [EXTRACTED]
  docs/README.md → frontend/js/history.js
- `IIFE Module Pattern for Frontend Encapsulation` --rationale_for--> `DogDexStats — IIFE Stats Module`  [EXTRACTED]
  docs/README.md → frontend/js/stats.js
- `claude.md — Development Rules for Claude Code` --references--> `ARCHITECTURE.md — System Architecture Document`  [INFERRED]
  claude.md → docs/ARCHITECTURE.md

## Hyperedges (group relationships)
- **End-to-End Inference Pipeline: Upload → Node → Python → Response** — upload_middleware, detectcontroller_detectimage, aiservice_analyzeimage, aiservice_callpythonapi, predict_predictendpoint, predict_preprocess, aiservice_todisplayname, aiservice_findcare [INFERRED 0.95]
- **Full ML Training Pipeline: Dataset → Generators → Train → Artifacts** — preparedataset_main, trainingutils_buildgenerators, train_main, train_buildmodel, train_runphase1, train_runphase2, train_saveartifacts [INFERRED 0.95]
- **Consistent Image Preprocessing Contract (224x224 RGB float [0,1])** — imageutils_resizeandsave, trainingutils_buildgenerators, predict_preprocess [INFERRED 0.90]
- **Frontend Analysis → localStorage Persistence Pipeline** — main_dogdex_app, history_dogdexhistory, stats_dogdexstats [EXTRACTED 1.00]
- **Three-Tier Inference Request Flow (Frontend → Node.js → Python)** — main_dogdex_app, doc_architecture, doc_api [EXTRACTED 1.00]
- **ML Training Artifact Pipeline (prepare → train → predict)** — ai_requirements, concept_two_phase_transfer_learning, concept_preprocessing_consistency [EXTRACTED 0.95]

## Communities (21 total, 7 thin omitted)

### Community 0 - "Frontend UI Layer"
Cohesion: 0.07
Nodes (19): ALLOWED_TYPES, careExercise, careGrooming, careTemperament, clearHistoryBtn, confidenceBar, error, fileNameEl (+11 more)

### Community 1 - "Model Training Pipeline"
Cohesion: 0.13
Nodes (20): build_model(), get_callbacks(), main(), parse_args(), train.py — DogDex ───────────────── Entrena un clasificador de razas caninas usa, Entrena solo la cabeza clasificadora con la base completamente congelada.     El, Descongela el bloque final de MobileNetV2 y reentrena con LR muy bajo.     Solo, Guarda el modelo en dos formatos y el mapeo índice→raza.     Se guardan ambos fo (+12 more)

### Community 2 - "Dataset Preparation"
Cohesion: 0.14
Nodes (17): main(), print_report(), process_breed(), prepare_dataset.py ────────────────── Lee imágenes crudas de dataset/raw/<raza>/, Imprime tabla resumen con conteo de imágenes por raza y por split., Divide la lista de imágenes en tres subconjuntos manteniendo las proporciones., Procesa todas las imágenes de una raza: valida el split,     redimensiona cada i, Verifica que el directorio raw exista y tenga subdirectorios de razas.     Retor (+9 more)

### Community 3 - "Express API Server"
Cohesion: 0.12
Nodes (12): app, cors, detectRouter, express, multer, path, storage, upload (+4 more)

### Community 4 - "AI Service & Breeds Catalog"
Cohesion: 0.14
Nodes (16): analyzeImage Service Function, callPythonApi — HTTP Bridge to FastAPI, findCare — Breed Care Lookup, Node.js → Frontend JSON Contract, toDisplayName — Snake to Title Case, Breeds Catalog Data (breeds.js), Detect Express Router, detectImage Controller Function (+8 more)

### Community 5 - "Backend Controllers & Routes"
Cohesion: 0.2
Nodes (11): { analyzeImage }, detectImage(), breeds, analyzeImage(), axios, breeds, callPythonApi(), findCare() (+3 more)

### Community 6 - "ML Concepts & Documentation"
Cohesion: 0.24
Nodes (14): requirements.txt — Python AI Dependencies, claude.md — Development Rules for Claude Code, Preprocessing Must Be Identical in Training and Inference, Two-Phase Transfer Learning Strategy, AI_PIPELINE.md — Machine Learning Pipeline Deep-dive, API.md — HTTP Endpoint Reference, ARCHITECTURE.md — System Architecture Document, DEPLOYMENT.md — Ubuntu Deployment Guide (+6 more)

### Community 7 - "FastAPI Inference Server"
Cohesion: 0.18
Nodes (12): FastAPI Inference App (predict.py), FastAPI Lifespan — Model Load on Startup, build_model — MobileNetV2 Transfer Learning Model, get_callbacks — EarlyStopping/Checkpoint/ReduceLR, train.py main — Training Orchestrator, run_phase1 — Feature Extraction Training, run_phase2 — Fine-Tuning Training, save_artifacts — Export Model + class_indices (+4 more)

### Community 8 - "Frontend App Shell"
Cohesion: 0.23
Nodes (12): IIFE Module Pattern for Frontend Encapsulation, DogDexHistory — IIFE History Module, index.html — Single-Page App Entry Point, API_URL — Hardcoded Backend Endpoint, main.js — Frontend Orchestrator, renderResult — Result Card Renderer, setLoading — Upload Button Loading State, showPreview — Image Preview via FileReader (+4 more)

### Community 9 - "Inference Endpoints"
Cohesion: 0.22
Nodes (9): health(), lifespan(), predict(), preprocess(), predict.py — DogDex Inference API ────────────────────────────────── Servidor Fa, Recibe una imagen y devuelve la raza inferida y la confianza.      Respuesta:, Carga el modelo al arrancar; libera recursos al detener el servidor., Convierte los bytes de la imagen al tensor que espera el modelo.     Debe ser id (+1 more)

### Community 10 - "Image Utils & Processing"
Cohesion: 0.29
Nodes (7): collect_images — Valid Image Path Collector, is_valid_image — Extension + Corruption Validator, resize_and_save — LANCZOS Resize to JPEG, prepare_dataset.py main — Dataset Pipeline Orchestrator, process_breed — Per-Breed Dataset Processor, split_images — Reproducible 70/15/15 Split, validate_raw_dir — Input Directory Validator

### Community 11 - "History Module"
Cohesion: 0.67
Nodes (3): buildCard — Build History Entry DOM Card, formatDate — Relative Time Formatter, DogDexHistory.render — Rebuild History DOM

### Community 12 - "Stats Module"
Cohesion: 0.67
Nodes (3): avgConfidence — Average Confidence Calculator, DogDexStats.render — Update Stats DOM, topBreed — Find Most-Detected Breed

## Knowledge Gaps
- **94 isolated node(s):** `express`, `cors`, `detectRouter`, `app`, `breeds` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `preprocess — Image Bytes to Tensor` connect `AI Service & Breeds Catalog` to `Image Utils & Processing`, `FastAPI Inference Server`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `main()` (e.g. with `build_generators()` and `plot_history()`) actually correct?**
  _`main()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ARCHITECTURE.md — System Architecture Document` (e.g. with `API.md — HTTP Endpoint Reference` and `AI_PIPELINE.md — Machine Learning Pipeline Deep-dive`) actually correct?**
  _`ARCHITECTURE.md — System Architecture Document` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `express`, `cors`, `detectRouter` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend UI Layer` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._
- **Should `Model Training Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._
- **Should `Dataset Preparation` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._