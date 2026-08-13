# JobLink

JobLink is a full-stack recruitment platform that connects candidates and employers through job discovery, application management, and explainable CV–job matching.

Beyond traditional job-board features, JobLink includes an AI-assisted matching pipeline that analyzes a candidate's submitted CV against a job's requirements and produces a deterministic match score, matched/partial/missing requirements, supporting evidence, and grounded explanations.

> The matching score is a heuristic CV–job compatibility score, not a hiring probability.

---

## ✨ Features

### For Candidates

- Browse and search job postings
- Advanced job filtering
- View company and job details
- Save/bookmark jobs
- Compare job opportunities
- Submit applications with a CV
- Manage candidate profile, education, experience, skills, and languages
- Track submitted applications
- Analyze how well a submitted CV matches a job
- View:
  - overall match score
  - matched requirements
  - partially matched requirements
  - missing requirements
  - supporting CV evidence
  - previous match analyses

### For Employers

- Manage employer/company profiles
- Create and manage job postings
- View applicants for each job
- Inspect candidate information
- Manage application status and evaluation
- Access employer dashboard functionality

### CV–Job Matching

JobLink includes an explainable matching pipeline that combines deterministic skill matching with hybrid evidence retrieval.

```text
Submitted CV
    ↓
Document parsing
    ↓
Text segmentation
    ↓
Skill extraction
    ↓
Job requirement extraction
    ↓
Exact / Alias / Related matching
    ↓
Unresolved requirements
    ↓
Dense Retrieval + BM25
    ↓
Reciprocal Rank Fusion
    ↓
Semantic evidence matching
    ↓
Deterministic scoring
    ↓
Grounded LLM explanation
```

The system distinguishes between:

```text
MATCHED
PARTIAL
MISSING
```

and preserves evidence from the CV sections that support each decision.

---

## 🧠 Matching Architecture

### 1. Deterministic Skill Matching

The first stage performs explicit skill matching using normalized skill names and curated aliases/relationships.

Examples:

```text
Postgres ↔ PostgreSQL
DRF ↔ Django REST Framework
Spring ↔ Spring Boot
Java ≠ JavaScript
```

This stage produces structured requirement decisions instead of delegating the official score directly to an LLM.

### 2. Dense Semantic Retrieval

Job requirements and CV segments are embedded using:

```text
intfloat/multilingual-e5-small
```

Job requirements are encoded as queries:

```text
query: <job requirement>
```

while CV segments are encoded as passages:

```text
passage: <cv evidence>
```

Embeddings are normalized and compared using cosine similarity.

### 3. BM25 Retrieval

JobLink also uses BM25 lexical retrieval to capture exact terminology and keyword-level evidence that dense embeddings may miss.

### 4. Reciprocal Rank Fusion

Dense and BM25 rankings are combined using Reciprocal Rank Fusion (RRF):

```text
Dense Retrieval
       +
BM25 Retrieval
       ↓
      RRF
       ↓
Fused CV evidence
```

This avoids directly adding raw BM25 and cosine-similarity scores, which operate on different scales.

### 5. Deterministic Scoring

The final match score is calculated from structured matching decisions.

Current scoring components include:

```text
Required skills
Preferred skills
Evidence quality
```

The scorer remains deterministic. Retrieval signals are used to discover evidence rather than being treated as final match percentages.

### 6. Grounded LLM Explanation

After scoring, an optional LLM explanation layer converts the structured result into a candidate-friendly explanation.

The LLM receives only:

```text
match score
matched requirements
partial requirements
missing requirements
selected evidence
```

It does not calculate or modify the official match score.

The implementation supports an OpenAI-compatible API endpoint.

---

## 🛠 Tech Stack

### Backend

- Python
- Django 5
- Django REST Framework
- OAuth2 authentication
- MySQL
- django-filter
- drf-yasg / Swagger
- Cloudinary
- PyMuPDF
- python-docx
- Tesseract OCR

### Matching / AI

- Sentence Transformers
- `intfloat/multilingual-e5-small`
- NumPy
- BM25 (`rank-bm25`)
- Reciprocal Rank Fusion
- OpenAI-compatible LLM API

### Mobile

- React Native
- Expo
- React Navigation
- Axios
- AsyncStorage
- React Native Paper
- Reanimated
- React Native SVG

---

## 📁 Project Structure

```text
JobLink/
├── backend/
│   ├── apps/
│   │   ├── applications/
│   │   ├── core/
│   │   ├── jobs/
│   │   ├── matching/
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
│   │
│   ├── App.js
│   └── package.json
│
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Le-Minh-Nhut/JobLink.git
cd JobLink
```

### 2. Backend Setup

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file:

```env
USER_DB=your_mysql_user
PASSWORD_DB=your_mysql_password

CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret

CKEY_API_KEY=your_llm_api_key
CKEY_BASE_URL=https://api.xah.io/v1
APPLICATION_MATCH_EXPLAINER_MODEL=your_model_name
```

Create the MySQL database:

```sql
CREATE DATABASE joblinkdb;
```

Run migrations:

```bash
python manage.py migrate
```

Start the backend:

```bash
python manage.py runserver
```

The API is available by default at:

```text
http://127.0.0.1:8000/
```

---

## 📱 Mobile Setup

```bash
cd mobile
npm install
npm start
```

or:

```bash
npx expo start
```

The mobile client connects to the backend through the API base URL configured in:

```text
mobile/src/utils/Apis.js
```

Update `BASE_URL` to point to your local or deployed backend.

---

## 📖 API Documentation

The Django backend exposes Swagger and ReDoc documentation:

```text
/swagger/
/redoc/
```

Authentication is handled through OAuth2.

---

## 🔍 Application Match API

Candidate-facing match analysis endpoints include:

```http
POST /candidate/applications/<application_id>/analysis/
GET  /candidate/applications/<application_id>/analysis/

GET  /candidate/applications/<application_id>/analyses/
GET  /candidate/applications/<application_id>/analyses/<analysis_id>/
```

These APIs allow candidates to run an analysis, retrieve the latest result, inspect analysis history, and open a specific historical result.

---

## 🔒 Matching Design Principles

The matching system follows several constraints:

- A submitted CV is the source of candidate evidence for an Application Match.
- Candidate profile information is not silently used to inflate the submitted-CV score.
- Retrieval similarity is not interpreted as a hiring probability.
- LLM output does not directly control the deterministic match score.
- Evidence is preserved so matching decisions can be inspected and explained.
- Sensitive personal attributes should not contribute to candidate scoring.

---

## 🗺 Roadmap

- [x] Deterministic skill matching
- [x] Required / preferred skill scoring
- [x] Multilingual E5 embeddings
- [x] Dense semantic retrieval
- [x] BM25 lexical retrieval
- [x] Reciprocal Rank Fusion
- [x] Semantic evidence matching
- [x] Evidence persistence
- [x] Candidate match-analysis UI
- [x] Match-analysis history/detail
- [x] Grounded LLM explanation layer
- [ ] Background analysis with Celery + Redis
- [ ] Idempotent analysis requests
- [ ] Analysis cancellation
- [ ] Retrieval/ranking evaluation
- [ ] Optional CrossEncoder reranking
- [ ] Optional grounded LLM verification

---

## ⚠️ Project Status

JobLink is currently under active development.

The CV–job matching system is designed as an explainable heuristic matching system. Retrieval thresholds, relation credits, and scoring weights are implementation policies that should be validated with evaluation data before being interpreted as calibrated measures of candidate quality.

---

## 📄 License

This project is licensed under the MIT License.

See [`LICENSE`](LICENSE) for details.