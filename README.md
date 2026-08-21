# JobLink

<p align="center">
  <strong>Recruitment Platform · Explainable CV–Job Matching · Career Intelligence RAG</strong>
</p>

<p align="center">
  An end-to-end recruitment system that combines traditional job-platform workflows with evidence-grounded AI for candidate matching and Vietnamese career intelligence.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/React%20Native-Expo-000020?logo=expo&logoColor=white" alt="Expo">
  <img src="https://img.shields.io/badge/RAG-multilingual--E5-blueviolet" alt="RAG">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
</p>

---

## Overview

**JobLink** is a full-stack recruitment platform for candidates and employers, built with Django REST Framework and React Native.

In addition to conventional recruitment features such as job discovery, applications, employer management, and candidate profiles, JobLink contains two independent AI systems:

* **Explainable Application Matching** — analyzes a submitted CV against a job description using deterministic skill matching, hybrid evidence retrieval, and grounded explanations.
* **Career Intelligence RAG** — retrieves evidence from real job postings and answers Vietnamese career questions using evidence-grounded generation with explicit job citations.

The repository also includes **CareerRAGBench-Auto-V2**, an evaluation framework created to measure retrieval and RAG quality instead of relying only on anecdotal examples.

> JobLink does **not** interpret retrieval similarity or the Application Match score as a hiring probability.

---

## Highlights

### Recruitment Platform

JobLink supports the main workflows of a recruitment system:

**Candidates**

* Search and browse jobs
* Filter job opportunities
* View job and company information
* Bookmark jobs
* Compare job postings
* Submit applications with a CV
* Track submitted applications
* Manage education, experience, languages, and skills
* Review CV–job match analyses
* Inspect historical match results

**Employers**

* Manage employer and company information
* Create and update job postings
* View applicants by job
* Inspect candidate information
* Update application status
* Access recruitment and application-management workflows

---

## AI System 1 — Explainable CV–Job Matching

JobLink does not delegate the official CV–job score directly to an LLM.

Instead, the system builds structured requirement decisions first and computes the score deterministically.

### Pipeline

```text
Submitted CV
    │
    ▼
Document Parsing
PDF / DOCX / OCR
    │
    ▼
Text Segmentation
    │
    ▼
Candidate Skill Extraction
    │
    ├─────────────────────────────┐
    │                             │
    ▼                             ▼
Job Requirement Extraction   CV Evidence
    │                             │
    ▼                             │
Exact / Alias / Related Match    │
    │                             │
    ▼                             │
Unresolved Requirements ─────────┘
    │
    ▼
Dense Retrieval + BM25
    │
    ▼
Reciprocal Rank Fusion
    │
    ▼
Semantic Evidence Matching
    │
    ▼
MATCHED / PARTIAL / MISSING
    │
    ▼
Deterministic Scoring
    │
    ▼
Grounded LLM Explanation
```

### Deterministic Skill Matching

The first stage resolves explicit skill relationships before semantic retrieval is considered.

Conceptually:

```text
Postgres  ↔ PostgreSQL
DRF       ↔ Django REST Framework
Spring    ↔ Spring Boot

Java      ≠ JavaScript
```

Each job requirement receives a structured decision:

```text
MATCHED
PARTIAL
MISSING
```

Only unresolved requirements are passed to the retrieval stage.

### Hybrid Evidence Retrieval

For requirements that cannot be resolved deterministically, JobLink searches the candidate CV using two complementary retrievers.

#### Dense retrieval

Requirements and CV segments are represented with:

```text
intfloat/multilingual-e5-small
```

The model follows E5's asymmetric retrieval convention:

```text
query:   <job requirement>
passage: <CV evidence>
```

Dense retrieval captures semantic similarity.

#### BM25 retrieval

BM25 provides lexical evidence for terminology that semantic embeddings may not rank highly enough.

#### Reciprocal Rank Fusion

The two rankings are combined using **Reciprocal Rank Fusion (RRF)** rather than directly adding incompatible BM25 and cosine-similarity scores.

```text
Dense Ranking ─┐
               ├──► Reciprocal Rank Fusion ──► Evidence Candidates
BM25 Ranking ──┘
```

### Deterministic Score

The final score is derived from structured decisions using:

```text
Required skill coverage
Preferred skill coverage
Evidence quality
```

The LLM is **not permitted to modify the official score**.

Its role is limited to converting the structured result into a readable explanation.

This provides a useful separation between:

```text
decision logic
        vs.
natural-language explanation
```

---

## AI System 2 — Career Intelligence RAG

JobLink also contains a separate RAG system for Vietnamese career questions.

Example questions:

```text
Data Engineer thường cần những kỹ năng gì?

Muốn làm Điều Dưỡng Viên thì nên chuẩn bị những năng lực nào?

Các JD cho vị trí Content Marketing thường yêu cầu gì?
```

### Career RAG Architecture

```text
User Career Question
        │
        ▼
multilingual-E5 Query Embedding
        │
        ▼
PostgreSQL + pgvector
        │
        ▼
Chunk-Level Cosine Retrieval
        │
        ▼
Metadata Filtering
        │
        ▼
Collapse Chunks → Unique Jobs
        │
        ▼
Top Evidence Chunks per Job
        │
        ▼
Evidence-Grounded LLM
        │
        ▼
Answer + Job Citations
```

The current production retriever uses:

```text
Embedding model : intfloat/multilingual-e5-small
Vector dimension: 384
Distance        : cosine
Vector store    : PostgreSQL + pgvector
```

Retrieval happens at the **evidence-chunk level**, but the final result is collapsed to unique jobs so one job cannot occupy multiple final ranking positions merely because several of its chunks rank highly.

Optional metadata filtering supports fields such as:

```text
source
location
experience level
employment type
career category
```

### Grounded Answer Generation

The Career Intelligence Assistant receives only retrieved job evidence.

Its prompt explicitly requires the model to:

* answer using retrieved evidence;
* avoid inventing jobs, companies, skills, or requirements;
* state when available evidence is insufficient;
* cite jobs using IDs such as `[J1]`, `[J2]`;
* avoid interpreting embedding similarity as hiring probability.

API endpoint:

```http
POST /career/ask/
```

---

# CareerRAGBench-Auto-V2

A major part of JobLink is the evaluation framework used to test the Career Intelligence retrieval system.

The goal is to evaluate retrieval using a frozen corpus and explicit relevance judgments instead of selecting a retriever from a few hand-written examples.

## Benchmark Snapshot

```text
Career families                15
Topics                         30
Queries                       120

Broad topics                   15
Occupation-specific topics     15

Certain silver qrels         2,391
Uncertain qrels                  9
Verified evidence nuggets    3,691
Judge controls                 120
```

Frozen source corpus:

```text
VietJobs source rows          48,092
Indexed unique jobs           47,097
Indexed evidence chunks      152,379
```

The benchmark uses a **family-disjoint DEV / TEST split**:

```text
DEV  : 7 career families
TEST : 8 career families
```

A family's broad and occupation-specific topics always stay in the same split.

This prevents closely related career-family information from leaking between DEV and TEST.

---

## Benchmark Construction

Each career family contributes:

```text
1 broad career-domain topic
+
1 occupation-specific topic
```

Each topic contains four query styles:

```text
direct
conversational
noisy
personalized
```

Specific occupations are selected using corpus statistics rather than downstream retrieval performance.

CareerRAGBench-Auto-V2 uses a support-aware specificity objective based on:

```text
log1p(local_support)
×
WilsonLowerBound(local_support / global_support)
```

This reduces the chance that globally generic occupations are incorrectly selected as representatives of a career domain.

---

## Silver Relevance Judgments

Candidate jobs are judged on a four-level relevance scale:

```text
3 = directly useful evidence
2 = clearly relevant/useful
1 = related but insufficient
0 = irrelevant/off-scope
```

Each candidate is independently evaluated from three perspectives:

```text
query-centric
evidence-centric
conservative
```

The final relevance grade is the median.

A judgment becomes uncertain when disagreement is large:

```text
max(grade) - min(grade) >= 2
```

Uncertain qrels are preserved separately rather than silently forced into the main silver set.

---

## Evidence Nuggets

Retrieval is evaluated not only by document relevance but also by whether retrieved jobs cover useful career information.

The benchmark extracts atomic evidence nuggets representing information such as:

```text
skills
technologies
qualifications
responsibilities
capabilities
```

Candidate nuggets are independently support-verified against their source job descriptions before being accepted.

This enables **evidence nugget recall** in addition to conventional ranking metrics.

---

## Benchmark Quality Gates

The benchmark is frozen only when all construction audits pass.

Quality checks include:

```text
Derived-label leakage
DEV / TEST family isolation
Minimum strong relevance per topic
Maximum uncertain-qrel rate
Positive judge controls
Negative judge controls
Order invariance
Query paraphrase consistency
Minimum verified nugget coverage
```

Current CareerRAGBench-Auto-V2 build:

```text
Derived-label leakage   PASS
Split audit             PASS
Qrel audit              PASS
Judge controls          PASS
Nugget audit            PASS

Overall                 PASS
```

---

# Retrieval Evaluation

The current frozen DEV comparison evaluates:

* BM25
* Dense retrieval
* equal-weight BM25 + Dense RRF

### DEV Results

| Retriever    |     nDCG@5 |    nDCG@10 | Strong P@5 | Strong P@10 | Nugget R@5 | Nugget R@10 |
| ------------ | ---------: | ---------: | ---------: | ----------: | ---------: | ----------: |
| BM25         |     0.4487 |     0.4376 |     0.4786 |      0.4750 |     0.1790 |      0.2806 |
| **Dense E5** | **0.7503** | **0.7301** | **0.7786** |  **0.7446** | **0.2820** |  **0.4187** |
| Equal RRF    |     0.6136 |     0.6017 |     0.6286 |      0.6250 |     0.2413 |      0.3859 |

Dense retrieval is the current selected DEV baseline.

Compared with BM25:

```text
Δ nDCG@5 = +0.3016

95% paired bootstrap CI:
[+0.2027, +0.4092]
```

The confidence interval remains entirely above zero.

This provides stronger evidence than comparing only the aggregate point estimates.

### Pool Coverage

For the selected dense baseline:

```text
Judged coverage @5  = 100%
Judged coverage @10 = 96.61%
```

The high judged coverage is important because unjudged documents cannot safely be assumed to be irrelevant for arbitrary future retrievers.

### Current Failure Mode

The largest observed retrieval weakness is robustness to diacritic-stripped, colloquial Vietnamese queries.

Dense retrieval performs strongly on clean query variants but degrades significantly on the current noisy-query subset.

This is being treated as an open retrieval research problem rather than silently hidden from the benchmark report.

> **Important:** all numbers above are **DEV results**. The benchmark TEST split remains locked and has not been used for model selection.

---

# Benchmark Commands

Build the frozen silver benchmark:

```bash
python manage.py build_career_rag_benchmark \
  --judge-model <model-name>
```

Default construction parameters include:

```text
seed       = 20260819
pool depth = 20
max pool   = 80
```

Run retrieval evaluation on DEV:

```bash
python manage.py evaluate_career_rag --kind retrieval --split dev
```

Run RAG evaluation on DEV:

```bash
python manage.py evaluate_career_rag --kind rag --split dev --judge-model <judge-model> --generator-model <generator-model>
```

TEST evaluation requires explicit unlocking and should only be performed after retrieval, generation, and prompt choices have been frozen.

---

# System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       React Native App                      │
│                         Expo Client                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ REST / OAuth2
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Django REST API                        │
│                                                             │
│  users │ jobs │ applications │ matching │ career │ payments│
└──────────────┬─────────────────────────────┬────────────────┘
               │                             │
               │                             │
               ▼                             ▼
┌──────────────────────────┐       ┌──────────────────────────┐
│  Application Matching    │       │ Career Intelligence RAG  │
│                          │       │                          │
│ deterministic matching   │       │ multilingual-E5         │
│ Dense + BM25             │       │ pgvector retrieval       │
│ RRF                      │       │ evidence grounding       │
│ deterministic scoring    │       │ citations                │
│ grounded explanation     │       │                          │
└──────────────┬───────────┘       └──────────────┬───────────┘
               │                                  │
               └────────────────┬─────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │ PostgreSQL + pgvector │
                    └───────────────────────┘
```

---

# Tech Stack

## Backend

* Python
* Django 5.2
* Django REST Framework
* OAuth2
* django-filter
* drf-yasg / Swagger
* PostgreSQL
* pgvector
* Cloudinary

## AI / Information Retrieval

* Sentence Transformers
* `intfloat/multilingual-e5-small`
* NumPy
* BM25 / `rank-bm25`
* Reciprocal Rank Fusion
* PostgreSQL vector search
* OpenAI-compatible LLM APIs
* Evidence-grounded generation

## Document Processing

* PyMuPDF
* python-docx
* Tesseract OCR
* Pillow

## Mobile

* React Native
* Expo
* React Navigation
* Axios
* AsyncStorage
* React Native Paper
* Reanimated
* React Native SVG
* Chart libraries

---

# Repository Structure

```text
JobLink/
├── backend/
│   ├── apps/
│   │   ├── applications/
│   │   │
│   │   ├── career/
│   │   │   ├── answering.py
│   │   │   ├── chunking.py
│   │   │   ├── embedding.py
│   │   │   ├── indexing.py
│   │   │   ├── models.py
│   │   │   ├── retrieval.py
│   │   │   │
│   │   │   ├── evaluation/
│   │   │   │   └── career_rag/
│   │   │   │       ├── audit.py
│   │   │   │       ├── build_benchmark.py
│   │   │   │       ├── judges.py
│   │   │   │       ├── metrics.py
│   │   │   │       ├── nuggets.py
│   │   │   │       ├── pooling.py
│   │   │   │       ├── run_rag_eval.py
│   │   │   │       ├── run_retrieval_eval.py
│   │   │   │       ├── schema.py
│   │   │   │       ├── semantics.py
│   │   │   │       └── topics.py
│   │   │   │
│   │   │   └── management/
│   │   │       └── commands/
│   │   │
│   │   ├── core/
│   │   ├── jobs/
│   │   ├── matching/
│   │   │   └── services/
│   │   │       ├── application_matching.py
│   │   │       ├── document_parser.py
│   │   │       ├── embeddings.py
│   │   │       ├── explanation.py
│   │   │       ├── fusion.py
│   │   │       ├── matcher.py
│   │   │       ├── pipeline.py
│   │   │       ├── retrieval.py
│   │   │       └── scorer.py
│   │   │
│   │   ├── payments/
│   │   ├── reports/
│   │   └── users/
│   │
│   ├── joblink/
│   ├── templates/
│   ├── manage.py
│   └── requirements.txt
│
├── mobile/
│   ├── assets/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── navigation/
│   │   ├── screens/
│   │   ├── styles/
│   │   └── utils/
│   ├── App.js
│   └── package.json
│
├── LICENSE
└── README.md
```

---

# Getting Started

## Prerequisites

Recommended local environment:

```text
Python 3.11+
PostgreSQL
pgvector
Node.js
npm
Expo tooling
Tesseract OCR
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/Le-Minh-Nhut/JobLink.git
cd JobLink
```

---

## 2. Backend Environment

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

If Tesseract is not installed on Ubuntu:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

---

## 3. Configure PostgreSQL

Create a PostgreSQL database:

```sql
CREATE DATABASE joblinkdb;
```

Ensure the `pgvector` extension is available, then enable it for the database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 4. Environment Variables

Create:

```text
backend/.env
```

Example:

```env
# PostgreSQL
POSTGRES_DB=joblinkdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Cloudinary
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

# OpenAI-compatible API
CKEY_API_KEY=your_api_key
CKEY_BASE_URL=https://api.xah.io/v1

# Application Match explanation
APPLICATION_MATCH_EXPLAINER_MODEL=your_model_name

# Career RAG benchmark / evaluation
CAREER_RAG_JUDGE_MODEL=your_judge_model
CAREER_RAG_GENERATOR_MODEL=your_generator_model
```

Never commit secrets or API credentials.

---

## 5. Database Migration

```bash
python manage.py migrate
```

---

## 6. Run Backend

```bash
python manage.py runserver
```

Default development API:

```text
http://127.0.0.1:8000/
```

---

# Career RAG Indexing

The repository includes a management command for indexing JobLink jobs into the Career RAG store:

```bash
python manage.py index_career_jobs
```

The indexing pipeline performs:

```text
job data
  ↓
section-aware chunking
  ↓
multilingual-E5 embedding
  ↓
PostgreSQL / pgvector persistence
```

---

# Mobile Setup

From the repository root:

```bash
cd mobile

npm install
npm start
```

or:

```bash
npx expo start
```

Available Expo scripts include:

```bash
npm run android
npm run ios
npm run web
```

The backend base URL is configured in:

```text
mobile/src/utils/Apis.js
```

Change `BASE_URL` to your local or deployed API endpoint before running the app.

For a physical device on the same LAN, the backend URL will normally need to use the host machine's LAN IP rather than `127.0.0.1`.

---

# API Documentation

Swagger:

```text
/swagger/
```

ReDoc:

```text
/redoc/
```

Authentication uses OAuth2.

---

# Important AI Endpoints

## Career Intelligence

```http
POST /career/ask/
```

Retrieves relevant job evidence and produces a grounded career answer.

---

## Application Match

Run or retrieve the latest analysis:

```http
POST /candidate/applications/<application_id>/analysis/
GET  /candidate/applications/<application_id>/analysis/
```

Retrieve analysis history:

```http
GET /candidate/applications/<application_id>/analyses/
```

Retrieve one historical analysis:

```http
GET /candidate/applications/<application_id>/analyses/<analysis_id>/
```

---

# Design Principles

JobLink's AI components follow several constraints.

### Evidence before explanation

The system first creates structured evidence and matching decisions.

Natural-language generation comes afterward.

### LLMs do not control the official match score

Application Match scoring remains deterministic.

### Submitted CV means submitted CV

The matching system uses the CV submitted with the application as candidate evidence.

Candidate-profile information should not silently inflate that score.

### Similarity is not probability

Cosine similarity represents embedding proximity.

It is not:

```text
probability of being hired
candidate quality
Application Match percentage
```

### Grounded Career RAG

Career answers should be supported by retrieved job evidence.

If available evidence is insufficient, the system should say so rather than invent unsupported claims.

### Benchmark TEST isolation

DEV is used for model selection and retrieval experimentation.

TEST should remain untouched until the system is frozen.

---

# Current Status

Implemented:

* [x] Candidate and employer recruitment workflows
* [x] Job search and filtering
* [x] Application management
* [x] Candidate profiles
* [x] CV parsing
* [x] OCR fallback
* [x] Deterministic skill matching
* [x] Required / preferred skill scoring
* [x] Dense CV evidence retrieval
* [x] BM25 CV evidence retrieval
* [x] Reciprocal Rank Fusion
* [x] Explainable application matching
* [x] Application-match history
* [x] Grounded LLM explanations
* [x] Career Intelligence RAG
* [x] PostgreSQL / pgvector career index
* [x] Evidence-grounded career citations
* [x] CareerRAGBench-Auto-V2
* [x] Graded silver qrels
* [x] Evidence nuggets
* [x] Benchmark quality gates
* [x] Topic-level bootstrap evaluation
* [x] BM25 / Dense / RRF DEV comparison

Research / engineering backlog:

* [ ] Improve noisy Vietnamese query robustness
* [ ] Evaluate reranking strategies
* [ ] Investigate dense-dominant fusion
* [ ] Complete RAG-generation DEV evaluation
* [ ] Freeze generation configuration before TEST
* [ ] Run TEST only after model-selection freeze
* [ ] Background analysis with Celery / Redis
* [ ] Idempotent long-running analysis requests
* [ ] Analysis cancellation and job-state tracking
* [ ] Production configuration hardening

---

# Research Notes

CareerRAGBench-Auto-V2 is a **silver benchmark**, not a human-gold benchmark.

Its qrels and evidence nuggets are LLM-assisted and protected by:

* multi-view judging;
* uncertainty separation;
* support verification;
* judge controls;
* leakage checks;
* explicit quality gates.

These mechanisms improve reliability but do not replace expert human adjudication.

Future retrievers should also audit judged-pool coverage before interpreting unjudged documents as irrelevant.

---

# Contributing

JobLink is currently under active development.

For major changes:

1. Create a dedicated branch.
2. Keep retrieval and scoring behavior reproducible.
3. Add tests or evaluation evidence for changes to AI behavior.
4. Avoid tuning against the benchmark TEST split.
5. Do not commit credentials, generated caches, or private candidate data.

---

# License

This project is licensed under the **MIT License**.

See [`LICENSE`](LICENSE) for details.

---

<p align="center">
  <strong>JobLink</strong><br>
  Building recruitment AI around evidence, reproducibility, and measurable retrieval quality.
</p>
