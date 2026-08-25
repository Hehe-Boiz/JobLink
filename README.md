# JobLink

<p align="center">
  <strong>Recruitment Platform · Explainable CV–Job Matching · Career Intelligence RAG</strong>
</p>

<p align="center">
  A full-stack recruitment platform with evidence-grounded AI for deterministic
  candidate matching and Vietnamese career intelligence.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white" alt="Django 5.2">
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL with pgvector">
  <img src="https://img.shields.io/badge/React%20Native-Expo-000020?logo=expo&logoColor=white" alt="React Native with Expo">
  <img src="https://img.shields.io/badge/RAG-multilingual--E5-blueviolet" alt="RAG with multilingual E5">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
</p>

JobLink combines candidate and employer workflows with two separate AI systems:
an explainable CV–job matcher and a citation-grounded Career RAG assistant. The
repository also contains the construction, integrity, evaluation, and TEST
protection code for **CareerRAGBench-Auto-V3**, an audited and reproducible
silver benchmark over a frozen VietJobs snapshot.

> Retrieval similarity and the Application Match score are evidence signals,
> not hiring probabilities.

## Highlights

- Full-stack candidate, employer, job, application, and profile workflows.
- Deterministic CV–job scoring with dense + BM25 evidence retrieval and grounded
  LLM explanations.
- Vietnamese Career RAG with section-aware evidence packing and explicit job
  citations.
- Frozen, family-disjoint CareerRAGBench-Auto-V3 DEV/TEST evaluation with
  integrity hashes and a one-shot TEST protocol.
- Clean dense retrieval reached **nDCG@5 = 0.7000** and
  **Strong Precision@5 = 0.7125** on held-out TEST.
- Clean RAG reached **weighted nugget coverage = 0.1394**, compared with
  **0.0622** for no-RAG; the paired family-level delta was **+0.0772**
  (95% CI [0.0312, 0.1336], exact sign-flip p = 0.0078).
- Clean RAG achieved **98.2% faithfulness** and **99.0% citation support** on
  the frozen TEST protocol.

## Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│                 React Native / Expo client                    │
└───────────────────────────────┬───────────────────────────────┘
                                │ REST / OAuth2
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                    Django REST Framework                      │
│ users · jobs · applications · matching · career · payments   │
└──────────────────────┬───────────────────────┬────────────────┘
                       │                       │
                       ▼                       ▼
          ┌──────────────────────┐  ┌─────────────────────────┐
          │ Application Matching │  │ Career Intelligence RAG │
          │ deterministic rules  │  │ multilingual E5        │
          │ dense + BM25 + RRF   │  │ evidence packing       │
          │ grounded explanation │  │ grounded answer        │
          └───────────┬──────────┘  └────────────┬────────────┘
                      │                          │
                      └────────────┬─────────────┘
                                   ▼
                        PostgreSQL + pgvector
```

The backend stores application data in PostgreSQL, vectors through pgvector,
and uploaded media through Cloudinary. The mobile client uses the REST API for
candidate and employer workflows.

### Product workflows

Candidates can search and compare jobs, bookmark opportunities, submit a CV,
track applications, maintain profile information, and inspect current or
historical match analyses. Employers can manage company information and job
postings, inspect applicants, and update application status.

## Explainable CV–Job Matching

The official CV–job score is not delegated to an LLM. JobLink first resolves
explicit requirements, retrieves supporting CV evidence for unresolved items,
and computes the score from structured decisions.

```text
Submitted CV
  → PDF / DOCX parsing with OCR fallback
  → candidate evidence segmentation
  → job requirement extraction
  → exact / alias / related-skill resolution
  → dense + BM25 retrieval for unresolved requirements
  → Reciprocal Rank Fusion
  → MATCHED / PARTIAL / MISSING decisions
  → deterministic score
  → grounded natural-language explanation
```

Dense retrieval uses `intfloat/multilingual-e5-small` with the asymmetric E5
`query:` / `passage:` convention. BM25 preserves lexical evidence, while RRF
combines rankings without treating BM25 and cosine scores as directly
comparable. The LLM explains the resulting evidence and decisions; it does not
replace the official score.

## Career RAG

The Career Intelligence endpoint answers Vietnamese career questions from job
posting evidence:

```text
Career question
  → query embedding
  → chunk retrieval
  → unique-job ranking
  → section-aware evidence packing
  → LLM answer
  → explicit job citations
```

The production retrieval path uses PostgreSQL/pgvector. Benchmark construction
and evaluation deliberately use a separate, hash-bound **clean benchmark-only
E5 sidecar**. CareerRAGBench V3 does not fall back to historically unverified
production vectors when the clean sidecar is absent or invalid.

## CareerRAGBench-Auto-V3

CareerRAGBench-Auto-V3 evaluates retrieval and end-to-end answer generation on
a frozen VietJobs corpus. It is a **silver, LLM-generated benchmark**, not
human-gold ground truth.

### Frozen status

- Benchmark status: **frozen and verified**.
- Split: held-out, family-disjoint DEV/TEST.
- Evaluation protocol: frozen after DEV selection.
- TEST status: **consumed**; the published results are final and must not be
  tuned against or routinely rerun.
- Integrity: benchmark artifacts, clean-sidecar identity, evaluation protocol,
  and semantic evaluator source closures are hash-bound and verified before
  evaluation.

### Frozen snapshot

| Item | Count |
|---|---:|
| Raw VietJobs source rows | 48,092 |
| Indexed jobs | 47,097 |
| Active chunks | 152,379 |
| Source rows absent from the DB | 995 |
| DB-only rows | 0 |
| Career families | 15 |
| Topics | 30 |
| Queries | 90 |
| Query variants per topic | 3 |
| Certain silver qrels | 4,012 |
| Uncertain qrels | 46 |
| Silver nuggets | 14,995 |

These values describe the frozen V3 snapshot; they are not universal claims
about VietJobs or career-search methodology.

### Construction

```text
Frozen VietJobs snapshot
  → clean multilingual-E5 benchmark-only sidecar
  → 15 eligible career families
  → broad + specific topic per family
  → 30 topics
  → direct + conversational + noisy query per topic
  → BM25 + clean dense + title-lexical pooling
  → full direct union of each contributor's top 20
  → multi-view silver relevance judgments
  → nugget extraction, strict support verification, and importance judging
  → controls, leakage checks, and integrity audits
  → candidate-directory build and atomic freeze
  → family-disjoint DEV/TEST split and one-shot evaluation locks
```

Pooling membership is the deterministic full direct union across all three
retrievers and all three query variants. RRF orders candidates but cannot
remove them, and the legacy `max_pool` setting cannot truncate the V3 judged
universe.

Qrels preserve three different states: certain grades 0–3, uncertain, and
unjudged. Uncertain documents are condensed from metric rankings; an unjudged
document within the metric horizon fails evaluation instead of becoming grade
0. Nugget `support_job_keys` are adaptively verified examples rather than an
exhaustive support map, so observed-support coverage remains a lower-biased
diagnostic—not nugget recall.

The three qrel prompt views are consistency judgments from one judge model,
not three independent human annotators. No human calibration was performed.

## Evaluation Protocol

DEV was used for system selection. TEST was evaluated once only after freezing
the exact runtime configuration and semantic source identity.

| Setting | Frozen value |
|---|---|
| Evaluation protocol | `career-rag-evaluation-protocol-v2` |
| Retrieval evaluation depth | 10 |
| Selected RAG retriever | `dense` / `clean_dense` |
| RAG top-k | 10 |
| Generator model requested | `levuphong2909/gemini-3.5-flash-high` |
| Judge model requested | `gpt-5.4` |
| Generation temperature | 0 |
| Bootstrap unit | family |
| Bootstrap samples | 2,000 |
| Bootstrap seed | 20260819 |
| Alpha | 0.05 |
| RAG protocol | `career-rag-rag-eval-v2` |
| Answer prompt | `career-rag-answer-v1` |
| Judge protocol | `career-rag-answer-judge-strict-v1` |
| Evidence packing | `career-rag-evidence-packing-v1` |

Query variants are first aggregated to topics; confidence intervals then
resample family IDs so broad and specific topics from the same family remain in
the same cluster. Paired comparisons operate on family-level deltas and use a
family-clustered bootstrap CI plus an exact sign-flip test when enumeration is
tractable.

Before TEST lock consumption, the evaluator verifies the benchmark, clean
sidecar, frozen runtime settings, and evaluator source hashes. Retrieval and
RAG use separate atomic one-shot lock files. A mismatch fails before consuming
the corresponding lock.

## Retrieval Results

The headline retrieval metrics are graded nDCG@5 and Strong Precision@5, where
strong relevance means a certain qrel grade of at least 2 and the precision
denominator is exactly 5.

### DEV

| System | nDCG@5 | Strong Precision@5 |
|---|---:|---:|
| BM25 | 0.4032 | 0.4286 |
| **Clean dense** | **0.6925** | **0.6857** |
| Title lexical | 0.3790 | 0.4190 |
| Hybrid RRF | 0.5645 | 0.5810 |

Clean dense was selected on DEV for the final RAG protocol.

### Held-out TEST

| System | nDCG@5 | Strong Precision@5 |
|---|---:|---:|
| BM25 | 0.4099 | 0.4125 |
| **Clean dense** | **0.7000** | **0.7125** |
| Title lexical | 0.4332 | 0.4542 |
| Hybrid RRF | 0.5790 | 0.5917 |

The selected clean-dense retriever retained strong point estimates on held-out
TEST: nDCG@5 increased from 0.6925 on DEV to 0.7000 on TEST, while Strong
Precision@5 increased from 0.6857 to 0.7125. These results support the selected
system on this frozen benchmark; they do not establish universal superiority.

## End-to-End RAG Results

The final evaluation compares three answer systems:

1. **No-RAG** — the generator receives no retrieved job context.
2. **Clean RAG** — the selected clean-dense retriever supplies the top 10 jobs.
3. **Gold-context RAG** — an oracle-like diagnostic using strong, certain silver
   context. It is an upper-bound/headroom control, not a deployable retriever.

Weighted nugget coverage is the weighted fraction of canonical silver nuggets
matched by an answer. The current judge schema identifies matched gold nuggets,
not a defensible predicted-nugget denominator, so the benchmark does not report
manufactured nugget precision or F1.

### Final held-out TEST

Values below are means with 95% family-cluster bootstrap confidence intervals.

| Metric | No-RAG | Clean RAG | Gold-context RAG |
|---|---:|---:|---:|
| Weighted nugget coverage | 0.0621735289<br>[0.0394214458, 0.0898208847] | **0.1393598501**<br>**[0.0851364683, 0.2001511607]** | 0.2713255073<br>[0.2127625154, 0.3331741845] |
| Faithfulness | N/A | 0.9816131169 (98.2%)<br>[0.9623378791, 0.9945012270] | 0.9857675149 (98.6%)<br>[0.9763575606, 0.9938525422] |
| Unsupported claim rate | N/A | 0.0183868831 (1.8%)<br>[0.0054987730, 0.0376621209] | 0.0142324851 (1.4%)<br>[0.0061474578, 0.0236424394] |
| Citation coverage | N/A | 0.9585227273 (95.9%)<br>[0.9157196970, 0.9920454545] | 0.9583333333 (95.8%)<br>[0.8958333333, 1.0] |
| Citation support rate | N/A | 0.9901493723 (99.0%)<br>[0.9854536842, 0.9945680005] | 0.9857675149 (98.6%)<br>[0.9763575606, 0.9938525422] |
| Context utilization | N/A | 0.7395833333 (74.0%)<br>[0.65, 0.8458333333] | 0.9395833333 (94.0%)<br>[0.8875, 0.98125] |

No-RAG grounding and citation metrics are **not applicable by design**: without
retrieved context, the judge cannot identify context-grounded faithfulness,
citation quality, or context utilization. They are excluded from macro
aggregation rather than converted to zero or one.

### DEV-to-TEST nugget coverage

| System | DEV | TEST |
|---|---:|---:|
| No-RAG | 0.3380748941 | 0.0621735289 |
| Clean RAG | 0.3994389930 | 0.1393598501 |
| Gold-context RAG | 0.4808132877 | 0.2713255073 |

TEST families appear substantially harder for nugget coverage. Retrieval itself
did not collapse—clean-dense TEST retrieval remained strong—and both no-RAG and
gold-context coverage also fell materially. The available measurements therefore
do not support attributing the entire drop to retrieval degradation.

## Statistical Tests

Paired tests use the eight held-out TEST families as the independent units.

| Comparison | Mean family delta in weighted nugget coverage | 95% paired family bootstrap CI | Exact sign-flip p-value | Families | Assignments |
|---|---:|---:|---:|---:|---:|
| Clean RAG − no-RAG | **+0.0771863212** | **[0.0312293005, 0.1335618216]** | **0.0078125** | 8 | 256 |
| Gold-context RAG − clean RAG | **+0.1319656571** | **[0.0714777425, 0.1874805992]** | **0.015625** | 8 | 256 |

Clean RAG significantly improved weighted nugget coverage over no-RAG on the
held-out family-level TEST split. This is a **system-level RAG comparison**:
the prompt/context conditions differ, so it is not a causal retrieval-only
ablation.

Gold-context RAG significantly outperformed retrieved-context RAG, indicating
substantial remaining context-quality headroom. The effect size and interval
remain visible alongside the p-value; statistical significance alone does not
establish practical importance outside this benchmark.

## Interpretation

- Clean dense retrieval generalized well from DEV to the frozen TEST split on
  the reported retrieval metrics.
- Under the frozen system protocol, clean RAG more than doubled the mean
  weighted silver-nugget coverage of no-RAG while remaining highly grounded in
  retrieved context.
- The gold-context gap shows that stronger context selection or coverage could
  unlock additional answer coverage; it does not represent a deployable system.
- The no-RAG and gold-context TEST drops show that the harder TEST coverage
  cannot be explained solely by retrieved-context degradation.
- These findings apply to a frozen silver benchmark over one VietJobs snapshot,
  not all job domains or career-assistance settings.

## Reproducibility

Run management commands from `backend/`. The large corpus, clean vector matrix,
and generated benchmark/report artifacts live under `backend/data/`, which is
intentionally excluded from Git. Verification or evaluation therefore requires
the corresponding local frozen artifacts.

### Verify the frozen benchmark

```bash
cd backend
python3 manage.py verify_career_rag_benchmark_v3
```

Verification checks artifact hashes, qrel partitioning, corpus identity, clean
sidecar identity, and frozen construction invariants without an LLM call.

### Run DEV retrieval evaluation

```bash
python3 manage.py evaluate_career_rag \
  --kind retrieval \
  --split dev \
  --top-k 10
```

### Run DEV RAG evaluation

RAG evaluation calls configured model providers and may incur cost. DEV remains
the only split intended for experimentation.

```bash
python3 manage.py evaluate_career_rag \
  --kind rag \
  --split dev \
  --retriever dense \
  --top-k 10 \
  --generator-model levuphong2909/gemini-3.5-flash-high \
  --judge-model gpt-5.4
```

Relevant environment variables, loaded from `backend/.env`, include:

```env
CKEY_API_KEY=your_api_key
CKEY_BASE_URL=https://your-openai-compatible-provider.example/v1
CAREER_RAG_GENERATOR_MODEL=your_generator_model
CAREER_RAG_JUDGE_MODEL=your_judge_model
CAREER_RAG_CLEAN_INDEX_DIR=data/career_eval/career_rag_clean_index_v3
```

Never commit credentials. The frozen TEST has already been consumed. TEST uses
permanent, evaluator-specific lock files and exact protocol matching; it is not
a normal reproducibility or tuning command and is intentionally omitted here.

For construction methodology and audit rationale, see the
[CareerRAGBench V3 Construction Spec and Audit Bible](backend/apps/career/doc/CAREER_RAG_BENCHMARK_V3_CONSTRUCTION_SPEC_AND_AUDIT_BIBLE_2026-08-22.md).
Where that evolving design document contains historical proposals, the frozen
V3 code and protocol define the implemented behavior.

## Limitations

- Qrels and nuggets are LLM-generated silver labels, not human-gold ground
  truth.
- Human calibration has not been performed
  (`human_calibration_status = NOT_PERFORMED`).
- The corpus covers one frozen VietJobs source/domain snapshot.
- Fifteen career families provide a meaningful held-out evaluation but remain a
  limited sample of career domains.
- Results depend on LLM-as-judge behavior under the frozen strict schema.
- Clean RAG versus no-RAG is a system-level comparison, not a causal
  retrieval-only ablation.
- TEST families were substantially harder than DEV for nugget coverage; the
  available reports do not identify a single definitive cause.
- Gold-context RAG is an oracle-like diagnostic upper bound, not production
  retrieval.
- The evaluation does not establish generalization beyond the frozen corpus,
  source, language distribution, or model protocol.

## Tech Stack

### Backend

- Python, Django 5.2, Django REST Framework
- PostgreSQL, pgvector, psycopg
- OAuth2, django-filter, drf-yasg / Swagger
- Cloudinary

### AI and information retrieval

- Sentence Transformers and `intfloat/multilingual-e5-small`
- NumPy, PyTorch, Transformers
- BM25 via `rank-bm25`
- Reciprocal Rank Fusion
- PostgreSQL vector search and a benchmark-only NumPy sidecar
- OpenAI-compatible chat-completion APIs

### Document processing

- PyMuPDF, python-docx
- Tesseract OCR, Pillow

### Mobile

- React Native 0.81, React 19, Expo 54
- React Navigation, Axios, AsyncStorage
- React Native Paper, Reanimated, SVG, chart libraries

## Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL with pgvector
- Node.js and npm
- Expo tooling for mobile development
- Tesseract OCR for scanned CV fallback

### Backend

```bash
git clone https://github.com/Le-Minh-Nhut/JobLink.git
cd JobLink/backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If using the existing Conda environment on the development machine, activate it
instead:

```bash
conda activate joblink
cd JobLink/backend
pip install -r requirements.txt
```

Install Tesseract on Ubuntu when OCR support is required:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

Create the database and enable pgvector:

```sql
CREATE DATABASE joblinkdb;
\c joblinkdb
CREATE EXTENSION IF NOT EXISTS vector;
```

Create `backend/.env`:

```env
POSTGRES_DB=joblinkdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

CKEY_API_KEY=your_api_key
CKEY_BASE_URL=https://your-openai-compatible-provider.example/v1
APPLICATION_MATCH_EXPLAINER_MODEL=your_model_name
```

Then initialize and run Django:

```bash
python3 manage.py migrate
python3 manage.py runserver
```

The development API defaults to `http://127.0.0.1:8000/`.

### Career RAG indexing

The production Career RAG index is built separately from the clean benchmark
sidecar:

```bash
python3 manage.py index_career_jobs
```

This command performs section-aware chunking, multilingual-E5 embedding, and
PostgreSQL/pgvector persistence. Do not confuse it with benchmark-sidecar
construction.

### Mobile

```bash
cd ../mobile
npm install
npm start
```

Available scripts are `npm run android`, `npm run ios`, and `npm run web`.
Configure the API base URL in `mobile/src/utils/Apis.js`. A physical device on
the same LAN normally needs the host machine's LAN IP rather than `127.0.0.1`.

## API Documentation

After starting Django:

- Swagger: `/swagger/`
- ReDoc: `/redoc/`

Authentication uses OAuth2.

### Career Intelligence

```http
POST /career/ask/
```

Retrieves relevant job evidence and returns a grounded career answer with job
citations.

### Application Match

```http
POST /candidate/applications/<application_id>/analysis/
GET  /candidate/applications/<application_id>/analysis/
GET  /candidate/applications/<application_id>/analyses/
GET  /candidate/applications/<application_id>/analyses/<analysis_id>/
```

These endpoints run or retrieve the latest analysis and expose analysis
history.

## Repository Structure

```text
JobLink/
├── backend/
│   ├── apps/
│   │   ├── applications/        # applications and status workflows
│   │   ├── career/              # production Career RAG
│   │   │   ├── evaluation/
│   │   │   │   └── career_rag/  # V3 construction, audits, and evaluation
│   │   │   └── management/
│   │   │       └── commands/    # indexing and benchmark commands
│   │   ├── jobs/
│   │   ├── matching/            # CV parsing, retrieval, scoring, explanation
│   │   ├── payments/
│   │   └── users/
│   ├── joblink/                 # Django settings and URL configuration
│   ├── manage.py
│   └── requirements.txt
├── mobile/                      # React Native / Expo client
├── LICENSE
└── README.md
```

## Design Principles

- **Evidence before explanation:** structured evidence and decisions precede
  natural-language generation.
- **Deterministic official matching:** LLM output does not control the CV–job
  score.
- **Submitted CV means submitted CV:** profile data must not silently inflate
  evidence from the CV submitted with an application.
- **Similarity is not probability:** embedding proximity is neither candidate
  quality nor probability of being hired.
- **Grounded Career RAG:** answers should cite retrieved job evidence and avoid
  unsupported claims when evidence is insufficient.
- **TEST isolation:** DEV supports selection; TEST is frozen, one-shot, and not
  a tuning resource.

## Contributing

For substantial changes:

1. Use a dedicated branch.
2. Keep retrieval and scoring behavior reproducible.
3. Add tests or evaluation evidence for changes to AI behavior.
4. Do not tune against the consumed benchmark TEST split.
5. Do not commit credentials, caches, generated artifacts, or private candidate
   data.

## License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <strong>JobLink</strong><br>
  Recruitment AI built around evidence, reproducibility, and measurable quality.
</p>
