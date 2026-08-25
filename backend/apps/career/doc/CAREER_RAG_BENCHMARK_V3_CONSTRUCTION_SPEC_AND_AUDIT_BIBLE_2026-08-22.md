# CareerRAGBench-Auto-V3


## Construction Specification, Methodology, Threat Model, Reproducibility Contract, and Full-Pipeline Audit Bible

**Project:** JobLink  
**Repository:** `Le-Minh-Nhut/JobLink`  
**Primary branch during hardening:** `fix/career-rag-benchmark-integrity`  
**Document date:** 2026-08-22  
**Intended benchmark version:** `CareerRAGBench-Auto-V3`, version `3.0`  
**Purpose:** authoritative handoff for a final comprehensive Codex audit before any paid V3 construction or TEST evaluation.

---

# 0. How to use this document

This document is deliberately stricter than a normal README. It is simultaneously:

1. a **methodology specification** — what the benchmark measures and why;
2. a **construction contract** — exact invariants required while building;
3. a **threat model / red-team checklist** — ways the benchmark can silently become invalid;
4. an **audit source of truth** — Codex must inspect code and tests and prove conformance.

Every implementation claim should be classified as:

- **VERIFIED-REMOTE** — directly observed on the pushed branch;
- **TARGET-V3** — intended final design that code must satisfy;
- **LOCAL-UNVERIFIED** — reported by a local patch/output but not independently inspected from the exact modified code.

At the time this document was written, the latest full-pipeline Codex patch had **not yet been pushed**. New local files such as `clean_index.py`, `evaluation_integrity.py`, and final evaluator changes therefore require independent inspection from the working-tree diff before any completion claim.

A green summary is not sufficient. The final audit must prove that:

- the intended code paths are actually exercised;
- the real Django test runner discovers and runs tests;
- dependency stubs do not hide import/runtime failures;
- no unknown judgment state is silently converted to a negative label;
- V3 never falls back to historical production embeddings;
- frozen artifacts cannot be changed without detection;
- TEST cannot be repeatedly inspected after results are known.

---

# 1. Executive summary

CareerRAGBench-Auto-V3 is a **silver, job-level retrieval and grounded-answer benchmark** for Vietnamese career information needs over the VietJobs corpus used by JobLink.

The benchmark targets questions such as:

> For a career family or specific job title, what skills/tools, responsibilities/capabilities, and experience/qualification requirements are commonly present in real job descriptions?

It does **not** claim to be human-authored gold ground truth. Relevance qrels and information nuggets are generated/verified with an LLM judging pipeline and then protected with structural validation, controls, provenance, deterministic construction, and artifact hashing.

Correct description:

> CareerRAGBench-Auto-V3 is a reproducible, audited **silver benchmark** over a frozen VietJobs corpus.

Incorrect descriptions include:

- fully human-annotated ground truth;
- three independent annotators;
- exhaustive relevance truth over all 47k jobs;
- exhaustive nugget-to-job support truth when adaptive verification stops early.

High-level target pipeline:

```text
Frozen VietJobs source + frozen chunk corpus
                |
                v
Benchmark-only clean E5 embedding sidecar
                |
                v
15 career families
  x 2 scopes (broad + specific)
= 30 topics
                |
                v
3 query variants/topic
(direct, conversational, noisy)
= 90 queries
                |
                v
BM25 + clean dense + title lexical
                |
                v
FULL DIRECT UNION of top-20 rankings
(no RRF/max_pool membership truncation)
                |
                v
LLM silver relevance judgments 0..3
+ uncertain judgments separated
                |
                v
Strong-relevance evidence
                |
                v
Atomic information nuggets
+ verified support examples
+ VITAL/OKAY importance
                |
                v
Controls + construction audits
                |
                v
Immutable atomic freeze
+ manifest + hashes + TEST lock
                |
                v
DEV evaluation
                |
                v
Family-clustered statistics
                |
                v
Protocol freeze -> one-shot TEST
```

---

# 2. External methodology references

CareerRAGBench should be interpreted in the context of established information-retrieval test-collection methodology.

## 2.1 TREC pooling and qrels

TREC describes pooling as selecting top documents from multiple retrieval runs and judging that set to build qrels. This motivates using heterogeneous retrieval systems to improve candidate coverage.

References:

- NIST TREC, **How To TREC**: https://trec.nist.gov/howto.html
- NIST TREC relevance judgments: https://trec.nist.gov/data/reljudge_eng.html

## 2.2 Incomplete judgments are dangerous

Conventional retrieval metrics may become unreliable when relevance judgments are substantially incomplete, and pooled qrels can favor systems that contributed to the pool.

References:

- Buckley & Voorhees, **Retrieval Evaluation with Incomplete Information**, SIGIR 2004:  
  https://www.nist.gov/publications/retrieval-evaluation-incomplete-information
- Büttcher et al., **Reliable Information Retrieval Evaluation With Incomplete and Biased Judgements**, SIGIR 2007:  
  https://www.nist.gov/publications/reliable-information-retrieval-evaluation-incomplete-and-biased-judgements
- Buckley et al., **Bias and the Limits of Pooling for Large Collections**, SIGIR 2007:  
  https://www.nist.gov/publications/bias-and-limits-pooling-large-collections
- Voorhees, Craswell & Lin, **Too many Relevants: Whither Cranfield Test Collections?**, 2022:  
  https://www.nist.gov/publications/too-many-relevants-whither-cranfield-test-collections

**V3 consequence:** `unjudged` must never be silently treated as relevance grade 0.

## 2.3 Heterogeneous retrieval systems

BEIR demonstrates the value of lexical and neural retrieval baselines under a common qrels framework.

Reference:

- Thakur et al., **BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models**, NeurIPS 2021 Datasets and Benchmarks:  
  https://arxiv.org/abs/2104.08663  
  https://github.com/beir-cellar/beir

**V3 consequence:** BM25, dense, and title retrieval contribute independently to pool membership. One aggregate fusion score must not delete a candidate discovered by another independent system.

## 2.4 E5 embedding protocol

Dense retrieval uses:

```text
intfloat/multilingual-e5-small
```

References:

- Wang et al., **Text Embeddings by Weakly-Supervised Contrastive Pre-training**:  
  https://arxiv.org/abs/2212.03533
- Wang et al., **Multilingual E5 Text Embeddings: A Technical Report**:  
  https://arxiv.org/abs/2402.05672

The benchmark must freeze not only the model name but also the actual passage input policy, query encoding convention, dimension, vector bytes/hash, and corpus identity.

## 2.5 LLM-as-a-judge limitations

Silver qrels/nuggets use an LLM judge. This scales labeling but is not equivalent to independent human annotation.

Reference:

- Zheng et al., **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena**, NeurIPS 2023 Datasets and Benchmarks:  
  https://arxiv.org/abs/2306.05685

The literature documents issues such as position, verbosity, and self-enhancement bias.

**V3 consequence:** three prompt views from one model are a consistency device, not three statistically independent annotators.

---

# 3. Benchmark research questions

## 3.1 Primary retrieval question

> Given a Vietnamese career-information query, can a system rank real job descriptions containing useful evidence about skills/tools, responsibilities/capabilities, and experience/qualification requirements?

**Primary retrieval unit:** job.

Chunks are internal retrieval/evidence units; qrels are job-level.

Final identity:

```text
source::source_job_id
```

For VietJobs:

```text
vietjobs::VietJobs:<id>
```

## 3.2 Secondary RAG question

> Given retrieved real job evidence, can a generator produce a complete career answer whose factual career claims are grounded in the supplied evidence?

Retrieval quality and answer quality must remain analytically separate.

---

# 4. Frozen corpus identity

Expected VietJobs snapshot:

| Quantity | Expected |
|---|---:|
| Raw source rows | 48,092 |
| Indexed unique jobs | 47,097 |
| Active VietJobs chunks | 152,379 |
| Source rows absent from DB | 995 |
| DB-only source IDs | 0 |

V3 construction must fail closed on unexpected drift.

Required identity material:

- source CSV SHA-256;
- sorted indexed source-job membership SHA-256;
- deterministic chunk/context SHA-256;
- relevant source-code hashes;
- git HEAD;
- git dirty state.

A chunk/context identity should bind at least:

```text
source_job_id
chunk_id
chunk_index
job_title
section
content
location_key
experience_level
employment_type
category_key
```

Serialization and hash framing must be deterministic and boundary-safe.

## 4.1 Historical filtering caveat

The surviving code does not necessarily reconstruct the exact historical reason that 995 raw rows are absent from the indexed DB.

Therefore V3 should freeze:

```text
dataset SHA
+ indexed membership SHA
+ active chunk/context SHA
```

and explicitly record that historical membership selection is not fully reconstructible rather than fabricating a reconstruction.

---

# 5. Leakage and embedding provenance

Forbidden derived fields include at least:

```text
technical_skills
soft_skills
gold_nuggets
judge_labels
derived_role_labels
```

Historical production chunking could append `metadata["technical_skills"]` into `embedding_text`. The stored raw `CareerJobChunk.content` is distinct from that historical embedding prefix.

Therefore current production vectors cannot be declared clean merely because the raw `content` field is clean.

Allowed provenance states:

```text
VERIFIED_CLEAN
VERIFIED_LEAKED
UNVERIFIED
```

Rules:

- no durable artifact => `UNVERIFIED`;
- contract mismatch => `UNVERIFIED`;
- explicit forbidden-field inclusion => `VERIFIED_LEAKED`;
- only genuine build-time evidence proving the clean input contract may yield `VERIFIED_CLEAN`.

Never fabricate a new provenance JSON to retroactively bless old vectors.

---

# 6. Benchmark-only clean embedding sidecar

Production vectors are historically unverified. V3 should not mutate production DB vectors.

**TARGET-V3 directory:**

```text
data/career_eval/career_rag_clean_index_v3/
    vectors.npy
    chunk_map.jsonl
    embedding_provenance.json
```

## 6.1 Source rows

Read exactly the frozen active VietJobs chunks in deterministic order:

```python
CareerJobChunk.objects.filter(
    active=True,
    source="vietjobs",
).order_by(
    "source_job_id",
    "chunk_index",
    "chunk_id",
)
```

No DB writes. No re-chunking.

## 6.2 Clean passage whitelist

Construct embedding text only from:

```text
job_title
location_key
category_key
experience_level
employment_type
section
content
```

Never read `metadata` while constructing clean passage input.

Conceptual deterministic format:

```text
passage: Job title: <job_title>
Location: <location_key>
Category: <category_key>
Experience level: <experience_level>
Employment type: <employment_type>
Section: <section>

<raw chunk content>
```

Optional lines are omitted when absent.

Version this policy, e.g.:

```text
career-rag-clean-sidecar-input-v1
```

## 6.3 Model contract

Freeze:

```text
embedding_model = intfloat/multilingual-e5-small
dimension = 384
dtype = float32
normalization = L2 normalized
query prefix = "query: "
passage prefix = "passage: "
```

Expected vector shape under current corpus:

```text
(152379, 384)
```

Memory-mapped NumPy storage is appropriate.

## 6.4 Chunk map

Each vector row maps to:

```json
{
  "row_index": 0,
  "chunk_id": "...",
  "source": "vietjobs",
  "source_job_id": "...",
  "job_key": "vietjobs::<id>"
}
```

Required:

- contiguous row index;
- unique chunk ID;
- map rows == vector rows;
- deterministic ordering;
- no derived metadata.

## 6.5 Genuine provenance artifact

`embedding_provenance.json` must be generated by the actual clean-index builder after real vectors are written.

At minimum bind:

```text
status = VERIFIED_CLEAN
provenance_schema_version
indexing_timestamp
index_type
embedding_model
embedding_dimension
input_field_policy
clean_embedding_input_policy_version
forbidden_derived_fields
forbidden_derived_fields_excluded = true
derived_fields_included = []
indexing_policy_version
corpus_membership_sha256
corpus_chunks_sha256
chunk_context_sha256
indexed_job_count
indexed_chunk_count
vectors_filename
vectors_sha256
vectors_dtype
vectors_shape
chunk_map_filename
chunk_map_sha256
embedding_source_sha256
clean_index_source_sha256
```

Timestamp must be timezone-aware UTC.

## 6.6 Sidecar verifier

Fail on:

- missing file;
- wrong model/dimension/dtype/shape;
- NaN/Inf;
- normalization mismatch if normalization is part of contract;
- vector/map hash mismatch;
- duplicate chunk IDs;
- non-contiguous row indices;
- row-count mismatch;
- corpus membership mismatch;
- chunk/context mismatch;
- relevant source-code hash mismatch;
- forbidden-field policy mismatch.

No silent repair.

---

# 7. Topic construction

Observed remote policy version:

```text
all-supported-nongeneric-wilson-specificity-v3
```

Relevant constants:

```text
preferred broad-family support = 100
minimum specific-title support = 8
hard minimum specific-title support = 8
Wilson z = 1.96
random seed = 20260819
```

Generic categories such as `other`, `misc`, etc. are excluded.

For a title:

```text
local_support  = support inside category
global_support = support across corpus
```

Specificity score:

```text
score =
    log1p(local_support)
    *
    WilsonLowerBound(local_support / global_support, z=1.96)
```

Each selected family creates exactly:

```text
1 broad topic
1 specific topic
```

Current V3 preflight snapshot:

```text
15 families
30 topics
```

## 7.1 No personalization in base V3

Actual V3 base construction must produce:

```text
known_skills = []
```

for topics and queries.

A personalized residual-gap query changes the information need and must not share generic qrels.

---

# 8. Canonical information need

All surface variants for one topic share one canonical need covering:

1. skills / tools / technologies;
2. responsibilities / capabilities / competencies;
3. experience / qualifications / education / language requirements.

Judging should use this canonical need rather than treating each wording variant as a new semantic topic.

The canonical-need policy must be versioned.

---

# 9. Query variants

Exactly:

```text
direct
conversational
noisy
```

Thus:

```text
30 topics x 3 variants = 90 queries
```

They test robustness to formal wording, conversational wording, and noisy/ASCII/informal search wording.

They are repeated perturbations, not independent samples.

Required per-topic invariant:

```text
count == 3
variant set exact
topic IDs consistent
known_skills empty
canonical need shared
```

Historical V2 had 120 queries because it contained an additional personalized-style variant.

---

# 10. DEV / TEST split

The split unit is **family**.

Both:

```text
family-X-broad
family-X-specific
```

must stay together.

Required:

```text
DEV family IDs ∩ TEST family IDs = empty
```

The exact family IDs and deterministic seed must be frozen.

---

# 11. Pool construction

Independent systems:

```text
BM25
clean dense E5
title lexical
```

For every topic and each of 3 query variants:

```text
top-20 BM25
top-20 clean dense
top-20 title
```

## 11.1 Final judged-pool membership

**TARGET-V3 policy:**

```text
FULL_DIRECT_UNION_V1
```

Membership is the deduplicated union over:

```text
3 variants x 3 systems x top-20
```

Theoretical maximum before dedup:

```text
180
```

## 11.2 RRF

RRF may compute ordering/metadata, but cannot remove any candidate contributed by an independent top-20 list.

## 11.3 `max_pool`

Historical `max_pool=80` must not control final V3 judged membership.

It may remain only as a diagnostic/backward-compatible parameter.

Historical failure pattern:

```text
direct union
-> aggregate RRF
-> truncate 80
-> candidate unjudged
-> evaluator defaults missing qrel to 0
```

This is exactly the incomplete-judgment bias the V3 redesign must prevent.

---

# 12. Pool artifact requirements

Preserve why a candidate entered the pool.

Useful fields include topic/job identity and original ranks for each system/variant, e.g.:

```text
rank_bm25_direct
rank_bm25_conversational
rank_bm25_noisy
rank_dense_direct
...
rank_title_noisy
RRF diagnostics
```

Absence from a system is distinct from rank zero.

Membership and order must be deterministic.

---

# 13. Section-aware evidence packing

Nominal evidence budget:

```text
5000 characters
```

Priority:

1. required qualifications / requirements;
2. responsibilities;
3. preferred qualifications;
4. description;
5. benefits;
6. other.

The packer must be deterministic, remain within budget, avoid duplicate content, and prioritize high-value sections before lower-value prose.

The same policy should be reused in:

- qrel judging;
- nugget extraction;
- nugget support verification;
- controls;
- nugget importance preview.

The packing policy is part of benchmark semantics and must be versioned/frozen.

---

# 14. Silver qrels

Qrels are job-level.

Grade scale:

```text
0 = not useful / not relevant
1 = weak or tangential
2 = clearly useful / strong relevant
3 = highly/directly useful
```

Remote prompt version has used three views:

1. query-centric;
2. evidence-centric;
3. conservative.

One judge model produces the views. They are not independent annotators.

Historical uncertainty rule:

```text
max(judge_grades) - min(judge_grades) >= 2
```

Uncertain rows belong in:

```text
qrels.uncertain.jsonl
```

not as implicit grade 0.

Strict validation must reject malformed candidate mappings, invalid grades, missing/extra IDs, bool-as-int values, and protocol-inconsistent payloads.

Schema retries must alter the cache identity, e.g.:

```text
SCHEMA_RETRY_ATTEMPT=<n>
```

Retry budget must be bounded and tested.

---

# 15. Judge transport / persistent cache

Expected safeguards:

- temperature 0;
- exact frozen judge model;
- prompt-response cache;
- atomic cache writes;
- cache key includes model/base URL/temperature/system/user;
- bounded schema retries;
- bounded transport retries;
- 429 cooldown/backoff;
- no hidden fallback model;
- preflight creates no paid client and performs no external call.

A judge-model change before construction is acceptable only if the final V3 build uses the chosen model consistently and records it in the manifest.

---

# 16. Construction controls

Historical V2 control thresholds/results provide context, not proof for V3.

Approximate historical thresholds:

```text
paraphrase consistency >= 0.90
order invariance       >= 0.90
positive accuracy      >= 0.90
negative accuracy      >= 0.95
```

Historical observed V2:

```text
paraphrase_consistency_rate = 0.90
order_invariance_rate       = 1.00
positive_accuracy           = 0.9333
negative_accuracy           = 1.00
passed                      = true
```

V3 must rerun controls with the final model/protocol.


# 17. Nugget construction

Nuggets are atomic career-information units extracted from strong relevant jobs.

Typical examples:

```text
Python
Docker
REST API design
Bachelor's degree in Computer Science
2+ years backend experience
Cross-functional communication
```

The goal is to represent answerable informational facets, not whole job descriptions.

## 17.1 Source jobs

Use strongly relevant **certain** qrels, typically:

```text
grade >= 2
```

Uncertain qrels must not silently become strong source jobs.

## 17.2 Extraction

The extractor sees the canonical information need and section-aware raw evidence and proposes:

```json
{
  "text": "...",
  "support_job_keys": ["..."]
}
```

These support keys are **hints only**.

## 17.3 Deduplication

Remote V3 normalizes nugget text and uses token-set overlap; an approximate Jaccard threshold around:

```text
0.85
```

has been used to merge near-duplicates.

## 17.4 Support verification

Extractor claims do not establish support.

Every recorded support job must pass a separate verifier.

Verifier support values must be literal JSON booleans:

```text
true
false
```

Reject:

```text
"true"
"false"
0
1
```

This avoids the Python trap:

```python
bool("false") == True
```

Remote code already uses:

```python
type(value) is bool
```

This must never regress.

## 17.5 Adaptive support verification

Hints may be checked first for efficiency, but they are non-authoritative.

If the minimum support threshold has not been reached, verification must continue through the remaining strong-job universe, including unhinted jobs.

This avoids:

```text
extractor omission
-> true support never checked
-> good nugget incorrectly discarded
```

## 17.6 Minimum support

Current intended minimum:

```text
2 verified supporting jobs
```

Nuggets failing the minimum are discarded.

## 17.7 Partial support semantics

Under adaptive stopping:

```text
support_job_keys
```

means:

> verified supporting examples observed before adaptive verification stopped.

It does **not** mean:

> exhaustive set of every strong job supporting the nugget.

Therefore:

```text
support_count = len(unique support_job_keys)
```

is an observed-example count, not true prevalence.

## 17.8 Prevalence

Because support is partial:

```text
prevalence = -1.0
```

acts as an explicit unavailable sentinel.

Do not estimate prevalence from the adaptive sample.

---

# 18. Nugget importance

Importance values:

```text
VITAL
OKAY
```

Current weighting:

```text
VITAL = 1.0
OKAY  = 0.5
```

Importance answers:

> How important is this fact for satisfying the canonical information need?

It must not answer:

> How often did this fact appear?

The importance prompt must therefore hide:

- support count;
- prevalence;
- omitted-job count;
- extraction frequency.

A small fixed evidence preview, historically up to 3 verified jobs, is acceptable.

---

# 19. Critical warning: partial nugget support is not true retrieval recall

This is a high-priority audit item.

Because `support_job_keys` are adaptive verified examples and not exhaustive mappings, this logic:

```text
retrieved jobs intersect support_job_keys
```

cannot legitimately be called exhaustive:

```text
nugget_recall@K
```

Example:

```text
true support             = {J1, J2, J3, J4}
stored verified examples = {J1, J2}
retriever returns         = J3
```

A metric based only on stored examples reports no coverage even though J3 truly supports the nugget.

Final audit must choose one:

### Preferred

Do not report retrieval `nugget_recall@K` as a headline metric unless exhaustive support mapping exists.

### Acceptable diagnostic

Rename it explicitly, e.g.:

```text
observed_support_coverage@K
verified_example_coverage@K
```

and disclose false-negative bias.

### Not acceptable

Call adaptive-example intersection "recall" without qualification.

This issue is distinct from answer-level nugget matching, where answer text can be judged directly against nugget text.

---

# 20. Offline preflight

Command:

```bash
python3 manage.py preflight_career_rag_benchmark_v3
```

Preflight must make:

```text
external_llm_calls = 0
```

Required checks:

- source CSV existence/hash;
- raw row count;
- indexed job count;
- active chunk count;
- DB-only IDs;
- membership/context hashes;
- leakage audit;
- clean-sidecar verification;
- provenance exactly `VERIFIED_CLEAN`;
- topic construction;
- exactly 30 topics under current frozen corpus;
- exactly 90 base queries;
- no personalized `known_skills`;
- family-disjoint DEV/TEST;
- real offline BM25;
- real clean dense;
- real title lexical;
- full-direct-union pool diagnostics;
- evidence truncation diagnostics;
- configuration/dependency readiness.

Final states:

```text
READY_FOR_PAID_BUILD
BLOCKED
```

Any blocker means nonzero exit.

Default terminal output should be concise; full JSON belongs in report files and/or `--json`.

---

# 21. Paid-build state machine

The paid benchmark builder must follow:

```text
START
 |
 v
Does final output already exist?
 | yes -> FAIL before paid client
 no
 |
 v
Create unique sibling .building-<pid>-<nonce>
 |
 v
Run complete free preflight
 |
 +-- BLOCKED -> clean candidate -> FAIL
 |
 v
Validate API/model
 |
 v
Write corpus/topics/queries/pool
 |
 v
Judge qrels
 |
 v
Run controls
 |
 v
Build nuggets
 |
 v
Run construction audit
 |
 +-- FAIL -> clean candidate -> FAIL
 |
 v
Write manifest + hashes + test lock
 |
 v
Offline verify candidate
 |
 +-- FAIL -> clean candidate -> FAIL
 |
 v
Atomic same-filesystem rename
 |
 v
FROZEN FINAL BENCHMARK
```

A failed/partial candidate must never masquerade as final output.

---

# 22. Frozen artifact set

The final V3 freeze should bind at least:

```text
corpus_manifest.json
topics.jsonl
queries.jsonl
pool.jsonl
qrels.silver.jsonl
qrels.uncertain.jsonl
controls.jsonl
nuggets.silver.jsonl
dev_ids.json
test_ids.json
benchmark_manifest.json
test_lock.json

reports/build_audit.json
reports/preflight_corpus.json
reports/preflight_leakage.json
reports/preflight_topics.json
reports/preflight_report.json
reports/preflight_embedding_provenance.json
reports/preflight_evidence_truncation.json
reports/preflight_pooling.json
reports/clean_embedding_provenance.json
```

If implementation names differ, every semantically critical artifact still must be hash-bound.

---

# 23. Manifest and freeze verification

## 23.1 Generic artifact map

Use a generic mapping:

```json
"artifact_sha256": {
  "relative/path": "<sha256>"
}
```

Verifier requirements:

- every required artifact exists;
- every required artifact is recorded;
- every recorded hash matches;
- recorded paths cannot escape benchmark root.

## 23.2 Bind exact clean embedding state

Frozen benchmark must record:

```text
clean_embedding_index_type
clean_embedding_model
clean_embedding_dimension
clean_embedding_input_policy_version
clean_embedding_vectors_sha256
clean_embedding_chunk_map_sha256
clean_embedding_provenance_sha256
clean_embedding_corpus_membership_sha256
clean_embedding_chunk_context_sha256
```

`vectors.npy` may remain external, but its exact identity must be cryptographically frozen.

## 23.3 Test lock

`test_lock.json` should bind:

- benchmark name/version;
- manifest SHA;
- TEST IDs SHA;
- frozen/immutable status.

Mismatch => evaluation refusal.

---

# 24. Retrieval evaluator semantics

## 24.1 Integrity first

Before retrieval evaluation:

1. verify frozen benchmark;
2. verify clean sidecar;
3. verify sidecar hashes equal frozen manifest;
4. only then load models/rankings.

## 24.2 Three relevance states

Explicitly distinguish:

```text
JUDGED_CERTAIN
JUDGED_UNCERTAIN
UNJUDGED
```

### Certain

Loaded from:

```text
qrels.silver.jsonl
```

Grades 0..3 are valid.

### Uncertain

Loaded from:

```text
qrels.uncertain.jsonl
```

They are not grade 0.

A frozen policy may condense/skip uncertain rows from metric positions, e.g.:

```text
condense-uncertain-v1
```

### Unjudged

A job in neither file is unknown.

Never use a primary-metric default like:

```python
qrels.get(job_key, 0)
```

If an unjudged job enters the evaluated top-K horizon, fail clearly or use a deliberately chosen incomplete-judgment measure. Do not disguise unknown as negative.

## 24.3 Recommended primary retrieval metrics

Because production retrieval returns roughly top-5 jobs, recommended primary:

```text
nDCG@5
```

Secondary:

```text
nDCG@10
Strong Precision@5
Strong Precision@10
```

where strong relevance is typically:

```text
grade >= 2
```

## 24.4 Precision denominator must be explicit

Audit whether `Precision@K` means:

```text
relevant / K
```

or:

```text
relevant / len(returned)
```

Metric name/documentation/code must agree.

## 24.5 Misleading aliases

If `context_precision@K` is mathematically identical to job-level `strong_precision@K`, it is not a true context metric. Rename/remove or document honestly.

---

# 25. Statistical unit and confidence intervals

Hierarchy:

```text
family
  +-- broad topic
  |    +-- direct
  |    +-- conversational
  |    +-- noisy
  |
  +-- specific topic
       +-- direct
       +-- conversational
       +-- noisy
```

Variants are perturbations, not independent observations.

Broad/specific topics from one family are related.

Therefore the resampling unit is:

```text
family
```

Recommended procedure:

1. compute query scores;
2. aggregate variants to topic score;
3. retain topic scores;
4. group topics by family;
5. bootstrap family IDs;
6. selecting a family includes both broad and specific topics.

For paired system comparisons:

1. compute topic-level differences;
2. group by family;
3. resample families.

Freeze:

```text
bootstrap_unit = family
bootstrap_seed
bootstrap_samples
alpha
```

---

# 26. TEST policy

TEST is for final protocol confirmation, not iterative optimization.

Before TEST freeze:

- topic selection;
- query protocol;
- clean sidecar;
- pool policy;
- qrels/nuggets;
- retriever configuration;
- generator model;
- prompts;
- metrics;
- bootstrap;
- RAG judge protocol.

Require explicit:

```text
--allow-test
```

Use evaluator-specific atomic one-shot locks, e.g.:

```text
reports/TEST_RETRIEVAL_ALREADY_RUN.lock
reports/TEST_RAG_ALREADY_RUN.lock
```

Lock should be created exclusively before TEST execution. Conservative policy treats a crashed TEST run after lock creation as consumed.

---

# 27. RAG evaluation

Possible systems:

```text
no_rag
retrieved_context_rag
gold_context_rag
```

Interpretation:

- `no_rag`: generator prior knowledge/general capability;
- retrieved-context RAG: deployable retrieval+generation system;
- gold-context RAG: oracle-style upper-bound diagnostic.

## 27.1 Controlled-comparison caveat

If claiming:

> retrieval itself improves generation,

then generator model, decoding, and answer protocol should be controlled across no-RAG and RAG.

If prompts/protocols differ materially, report a **system-level comparison**, not a clean causal retrieval ablation.

## 27.2 Gold context

Gold context should use strong, **certain** qrels only.

Uncertain/unjudged documents should not become oracle context.

---

# 28. Strict RAG judge schema

Required exact top-level keys:

```text
matched_nugget_ids
claim_count
supported_claim_count
unsupported_claim_count
citation_required_claim_count
cited_claim_count
citation_supported_count
context_used_job_keys
```

No missing keys. No extras.

Counts must satisfy literal:

```python
type(value) is int
```

Reject bools, numeric strings, floats, negative values.

List IDs must be unique and valid subsets of supplied nugget/context IDs.

Arithmetic invariants:

```text
supported_claim_count <= claim_count
unsupported_claim_count <= claim_count

supported_claim_count
+ unsupported_claim_count
== claim_count

citation_required_claim_count <= claim_count
cited_claim_count <= citation_required_claim_count
citation_supported_count <= cited_claim_count
```

For no-context:

```text
supported_claim_count == 0
context_used_job_keys == []
cited_claim_count == 0
citation_supported_count == 0
```

Invalid payload => bounded schema retry, never coercion.

Retry prompts need distinct cache identity, e.g.:

```text
SCHEMA_RETRY_ATTEMPT=<n>
```

---

# 29. Answer-level nugget metrics

Answer-level nugget matching can judge generated text directly against the canonical nugget list.

Possible weighted metrics:

```text
weighted nugget precision
weighted nugget recall
weighted nugget F1
```

using:

```text
VITAL = 1.0
OKAY = 0.5
```

The exact formulas must be explicit and unit tested.

This is conceptually different from retrieval-time `support_job_keys` coverage.

---

# 30. Reproducibility and dependencies

A benchmark pipeline is not reproducible if a clean environment installed from repository declarations cannot import/run it.

At this document snapshot, remote:

```text
backend/requirements.txt
```

does not declare the `openai` SDK even though code imports:

```python
from openai import OpenAI
```

This is a real reproducibility issue.

Final audit must ensure:

- runtime dependencies are declared;
- the real Django test command imports the real installed SDK;
- no import-only stub is used as evidence of full success;
- `Ran 0 tests` is always failure;
- offline tests may mock network calls, but not hide missing packages.

---

# 31. Local configuration and secrets

Django settings call:

```python
load_dotenv()
```

A local `.env` may contain:

```env
CKEY_API_KEY=...
CKEY_BASE_URL=https://api.xah.io/v1
CAREER_RAG_JUDGE_MODEL=<frozen judge model>
CAREER_RAG_CLEAN_INDEX_DIR=data/career_eval/career_rag_clean_index_v3
```

Never commit/print secrets.

The secret key must not become part of persisted cache/artifact content.

---

# 32. Historical V2 snapshot

Historical root:

```text
data/career_eval/career_rag_bench_auto_v2
```

Observed rows:

| Artifact | Rows |
|---|---:|
| topics.jsonl | 30 |
| queries.jsonl | 120 |
| pool.jsonl | 2,400 |
| qrels.silver.jsonl | 2,391 |
| qrels.uncertain.jsonl | 9 |
| controls.jsonl | 120 |
| nuggets.silver.jsonl | 3,691 |

Historical DEV baselines:

| System | nDCG@5 | nDCG@10 | Strong P@5 | Strong P@10 | Nugget R@5* | Nugget R@10* |
|---|---:|---:|---:|---:|---:|---:|
| Dense | 0.7503 | 0.7301 | 0.7786 | 0.7446 | 0.2820 | 0.4187 |
| BM25 | 0.4487 | 0.4376 | 0.4786 | 0.4750 | 0.1790 | 0.2806 |
| RRF | 0.6136 | 0.6017 | 0.6286 | 0.6250 | 0.2413 | 0.3859 |

Historical dense-minus-BM25:

```text
nDCG@5 delta = +0.3016
95% CI ≈ [0.2027, 0.4092]
```

`*` Historical nugget retrieval recall should be interpreted cautiously because support mapping is not exhaustive.

The old nDCG numbers are not automatically invalid solely because nugget support semantics were weak.

---

# 33. V2 -> V3 methodological changes

| Area | Historical V2 | V3 target |
|---|---|---|
| Base query variants | 4 incl. personalized | exactly 3 non-personalized |
| Embedding provenance | historical vectors not provably clean | clean benchmark-only sidecar |
| Pool membership | fixed-size/fusion truncation risk | full independent direct union |
| Unjudged | could default to 0 | explicit unknown/fail |
| Uncertain | could disappear -> 0 | explicit condensation |
| Bootstrap | topic | family-clustered |
| Embedding freeze | insufficient binding | exact sidecar identity |
| TEST lock | partial | evaluator-specific one-shot |
| RAG schema | permissive | exact strict schema |
| Judge interpretation | easy to overclaim | explicitly silver |

---

# 34. Known historical bug matrix

## P0

### Pool truncation / unjudged bias

Required final status:

```text
FIXED
```

via full direct union + unknown-state handling.

### Nugget `bool("false")`

Required:

```text
ALREADY FIXED + REGRESSION TEST
```

### Nugget only verifies extractor claims

Required:

```text
ALREADY FIXED + REGRESSION TEST
```

Adaptive verifier must inspect unhinted strong jobs when needed.

## P1

### Wrong bootstrap unit

Required:

```text
family-clustered bootstrap
```

### Freeze lacks exact embedding state

Required:

```text
vectors SHA + chunk-map SHA + provenance SHA + corpus identity
```

### Atomic/integrity

Atomic build was already hardened remotely; evaluator must additionally verify freeze before running.

### Leakage-free index not reproducible

Required:

```text
new benchmark-only clean sidecar + genuine build-time provenance
```

## P2

### Uncertain -> grade 0

Required explicit uncertainty state.

### RAG TEST repeatable

Required one-shot atomic lock.

### RAG judge counts permissive

Required exact types, exact keys, arithmetic invariants, bounded retries.


# 35. Additional issues the final audit must search for

Fixing the historical list is not proof the full pipeline is correct. Codex must also audit the following.

## 35.1 Partial support mislabeled as recall

Search every use of:

```text
support_job_keys
nugget_recall
```

and prove partial adaptive support is not interpreted as exhaustive support truth.

## 35.2 Strong Precision denominator

Determine whether `Precision@K` uses:

```text
relevant / K
```

or:

```text
relevant / returned_count
```

and align name/documentation/code.

## 35.3 Misleading `context_precision`

If it is merely job-level strong precision under another name, remove/rename/document.

## 35.4 No-RAG / RAG protocol confounding

Check whether no-RAG and RAG use the same generator model and sufficiently controlled prompting before making a causal claim about retrieval.

## 35.5 Gold-context contamination

Gold context must be strong/certain only.

## 35.6 Same-model generation/judging

If the same model family generates and judges, report the limitation.

## 35.7 Cache contamination

A semantic prompt/protocol change must change cache identity. Old cache entries must not silently satisfy a new protocol.

## 35.8 Resume/checkpoint compatibility

If paid-build resume exists, prove reused artifacts match:

- benchmark version;
- judge model;
- prompt version;
- corpus identity;
- pool policy;
- evidence policy.

Never mix V2/V3 semantics or labels from different judge protocols.

## 35.9 Dirty git freeze

Manifest may record dirty state, but the recommended final paid-build working tree is clean:

```bash
git status --porcelain
```

should ideally output nothing.

## 35.10 Source-hash closure

If behavior depends on files outside `career_rag/*.py`, such as embedding/source/normalization code, bind semantically relevant source hashes too.

## 35.11 Production-vector fallback

Search all benchmark/evaluator imports for:

```text
CareerRetriever
CareerJobChunk.embedding
CosineDistance
```

No V3 dense path may silently fall back to historical production vectors.

## 35.12 Dependency completeness

Search imports versus `requirements.txt`, especially `openai`.

---

# 36. Required construction audit

The final construction audit must fail on any critical invariant.

## Corpus

- exact source hash;
- raw rows expected;
- indexed jobs expected;
- active chunks expected;
- DB-only IDs zero;
- membership hash;
- context hash.

## Leakage / provenance

- forbidden metadata audit passes;
- clean sidecar present;
- sidecar verifier passes;
- provenance exactly VERIFIED_CLEAN;
- clean-vector corpus identity matches benchmark corpus.

## Topics

- 15 current families;
- 30 topics;
- broad + specific per family;
- no personalized known skills;
- supported specific title;
- deterministic family split.

## Queries

- 90 total;
- exactly 3 per topic;
- exact variant set;
- shared canonical need.

## Pool

- real BM25;
- real clean dense;
- real title;
- top-20 independent rankings;
- judged membership equals full direct union;
- no RRF/max_pool membership removal;
- deterministic ranks/order.

## Qrels

- every pool job appears exactly once as certain or uncertain;
- no duplicate qrel key;
- certain grade literal int 0..3;
- uncertain rows structurally valid;
- no missing pooled candidate.

## Controls

- frozen thresholds pass.

## Nuggets

- source jobs strong/certain;
- nonempty text;
- literal bool support;
- minimum verified support;
- support keys subset of strong/certain jobs;
- support_count exact;
- prevalence unavailable sentinel;
- valid importance;
- weight matches importance.

## Freeze

- all artifacts complete;
- all hashes complete;
- clean sidecar identity bound;
- build audit passed;
- TEST lock valid;
- offline verifier passed;
- atomic finalize.

---

# 37. Required evaluator audit

Before DEV evaluation:

```text
verify benchmark freeze
verify clean sidecar
verify sidecar == manifest identity
load certain qrels
load uncertain qrels
construct explicit judgment-state lookup
```

Negative/tamper tests should include:

- alter qrel byte -> refuse;
- alter pool byte -> refuse;
- alter copied provenance -> refuse;
- use another `vectors.npy` -> refuse;
- remove uncertain qrels -> refuse;
- unknown top-K job -> never silently 0;
- second TEST invocation -> refuse.

---

# 38. Test matrix

A comprehensive final suite should cover at least:

## Topic/query

1. deterministic topic construction;
2. exactly 3 variants;
3. no personalized known skills;
4. family-disjoint split;
5. deterministic specific-title scoring.

## Evidence

6. late required qualifications survive packing;
7. deterministic output;
8. within char budget;
9. no duplicated evidence.

## Judge/qrels

10. exact candidate IDs;
11. literal integer grades;
12. invalid ranges rejected;
13. missing/extra IDs rejected;
14. schema retry changes cache key;
15. retry budget exact.

## Nuggets

16. string `"false"` rejected;
17. integer 0/1 rejected as bool;
18. extractor hints non-authoritative;
19. unhinted strong jobs checked;
20. support minimum enforced;
21. support semantics remain partial;
22. prevalence sentinel retained;
23. importance receives no frequency signal.

## Clean index

24. clean input deterministic;
25. metadata never read;
26. technical skills excluded;
27. soft skills excluded;
28. vectors/map aligned;
29. vector tamper rejected;
30. map tamper rejected;
31. NaN/Inf rejected;
32. wrong dimension rejected;
33. corpus mismatch rejected;
34. production-vector fallback impossible.

## Pool

35. full union membership;
36. RRF cannot remove candidate;
37. `max_pool` cannot remove candidate;
38. rank metadata preserved;
39. deterministic ordering.

## Judgment-state evaluator

40. judged grade 0 remains valid;
41. uncertain != 0;
42. unjudged != 0;
43. uncertain condensation;
44. unjudged top-K fails;
45. judged-fraction diagnostics.

## Statistics

46. variants -> topic aggregation;
47. family bootstrap unit;
48. broad+specific sampled together;
49. paired family bootstrap;
50. deterministic bootstrap seed.

## Freeze

51. existing final target refused;
52. partial target refused;
53. failure cleans candidate;
54. success atomic;
55. artifact tamper rejected;
56. sidecar identity bound;
57. manifest path escape rejected.

## RAG

58. exact top-level keys;
59. missing key rejected;
60. extra key rejected;
61. numeric string rejected;
62. float rejected;
63. bool count rejected;
64. negative count rejected;
65. arithmetic inconsistency rejected;
66. fake nugget ID rejected;
67. fake context job rejected;
68. no-context invariants;
69. retry key separation;
70. retry budget exact.

## TEST

71. DEV does not consume TEST;
72. first retrieval TEST consumes lock;
73. second retrieval TEST refused;
74. first RAG TEST consumes lock;
75. second RAG TEST refused.

## Reproducibility

76. `manage.py check` passes;
77. real Django test command discovers >0 tests;
78. real OpenAI SDK imports;
79. no network/API call in offline tests;
80. no DB mutation in benchmark-only sidecar tests.

---

# 39. Native validation commands

Use the real JobLink environment.

```bash
cd ~/data/JobLink/backend

python3 manage.py check

python3 manage.py test \
  apps.career.evaluation.career_rag.test_construction -v 2

python3 -m compileall -q \
  apps/career/evaluation/career_rag \
  apps/career/management/commands

git diff --check
```

If evaluator tests live separately, run them as well.

This result is unacceptable:

```text
Ran 0 tests
```

even if an alternative stubbed test harness reports green.

---

# 40. Operational procedure

## Stage 1 — Code audit

No API. Native tests green.

## Stage 2 — Build real clean sidecar

Target command:

```bash
python3 manage.py build_career_rag_clean_index_v3
```

Expected:

- no DB mutation;
- no LLM;
- atomic sidecar freeze;
- genuine VERIFIED_CLEAN provenance.

## Stage 3 — Offline preflight

```bash
python3 manage.py preflight_career_rag_benchmark_v3
```

Required:

```text
STATUS: READY_FOR_PAID_BUILD
```

If blocked, stop.

## Stage 4 — Freeze source state

Recommended:

```bash
git status --porcelain
```

empty.

## Stage 5 — Paid V3 construction

Only after READY.

The paid build itself must re-run free preflight before paid client creation.

## Stage 6 — Offline frozen verification

```bash
python3 manage.py verify_career_rag_benchmark_v3 \
  --output-dir data/career_eval/career_rag_bench_auto_v3
```

Must PASS.

## Stage 7 — DEV evaluation

Only DEV.

## Stage 8 — Protocol freeze

Freeze retriever, generator, prompts, top-K, metrics, uncertain policy, bootstrap, judge model, report schema.

## Stage 9 — One-shot TEST

Only after the above.

---

# 41. Meaning of readiness states

Do not collapse everything into generic PASS.

## `NO-GO: CODE`

A correctness bug remains.

## `NO-GO: ENVIRONMENT`

Code may look correct, but dependencies/native runtime do not pass.

## `NO-GO: DATA/PROVENANCE`

Code passes but corpus/sidecar/provenance is invalid or absent.

## `READY FOR SIDECAR BUILD`

Code/tests pass, sidecar not built.

## `READY FOR OFFLINE PREFLIGHT`

Real sidecar exists and verifies.

## `READY_FOR_PAID_BUILD`

Actual preflight passes all free gates.

## `FROZEN V3 VERIFIED`

Paid construction + offline frozen verifier pass.

## `DEV EVALUATED / TEST LOCKED`

DEV analyzed and protocol frozen.

## `TEST CONSUMED`

One-shot TEST executed.

---

# 42. Meaning of `READY_FOR_PAID_BUILD`

It does not mean benchmark correctness is magically proven.

It means:

> every free construction prerequisite and integrity contract has passed, so spending money to create final silver annotations is methodologically permissible.

---

# 43. Meaning of final frozen PASS

A frozen V3 PASS means at least:

1. corpus identity known;
2. clean embedding identity known;
3. topic/query policy frozen;
4. pool membership reproducible;
5. every pool member certain or explicitly uncertain;
6. silver qrel protocol recorded;
7. nugget protocol recorded;
8. controls/audits pass;
9. semantic artifacts hash-bound;
10. freeze immutable;
11. evaluator can independently verify integrity.

It still does not convert silver annotations into human gold labels.

---

# 44. Limitations that should be disclosed publicly

1. Qrels are LLM-generated silver judgments.
2. Multiple views use one judge model and are not independent annotators.
3. Job postings reflect hiring-market and dataset biases.
4. The 995 absent source rows come from a historical selection process not fully reconstructible from surviving code.
5. Nugget support examples are adaptive/partial, not exhaustive prevalence mappings.
6. LLM judge bias remains possible despite controls.
7. Topics cover supported families in one VietJobs snapshot, not all occupations.
8. Benchmark scope is Vietnamese career information.
9. A future radically different retriever may surface unjudged top results; evaluator must fail rather than hide incomplete judgments.
10. TEST is intended to be one-shot.

---

# 45. Required final Codex audit behavior

Codex must not merely answer "looks correct".

It must:

1. read this entire file;
2. inspect exact working-tree diff including untracked files;
3. inspect affected call sites;
4. create requirement-to-code mapping;
5. create requirement-to-test mapping;
6. label untested invariants `UNPROVEN`;
7. run real Django tests;
8. reject stub-only evidence;
9. run compile/static checks;
10. red-team evaluator defaults;
11. search for all dangerous patterns;
12. verify dependency declarations;
13. prove no production DB mutation;
14. prove critical hashes are frozen;
15. cite exact file/function/test for every PASS.

A checklist entry without code evidence and test evidence is:

```text
UNPROVEN
```

not PASS.

---

# 46. Mandatory search patterns for Codex

Run at least:

```bash
grep -R "qrels.get" -n apps/career
grep -R "get(key, 0)" -n apps/career
grep -R "bool(" -n apps/career/evaluation/career_rag
grep -R "support_job_keys" -n apps/career/evaluation/career_rag
grep -R "nugget_recall" -n apps/career/evaluation/career_rag
grep -R "CareerRetriever" -n apps/career/evaluation/career_rag
grep -R "CareerJobChunk" -n apps/career/evaluation/career_rag
grep -R "\.embedding" -n apps/career/evaluation/career_rag
grep -R "CosineDistance" -n apps/career/evaluation/career_rag
grep -R "max_pool" -n apps/career/evaluation/career_rag
grep -R "allow-test\|allow_test\|TEST_" -n \
  apps/career/evaluation/career_rag \
  apps/career/management/commands
grep -R "matched_nugget_ids\|supported_claim_count\|citation_supported_count" -n \
  apps/career/evaluation/career_rag
grep -R "bootstrap" -n apps/career/evaluation/career_rag
grep -R "artifact_sha256\|verify_frozen_benchmark" -n \
  apps/career/evaluation/career_rag
grep -R "openai" -n . requirements.txt
```

Also search semantic prompt versions and cache directories to detect stale-checkpoint reuse.

---

# 47. Final non-negotiable invariants

1. Production historical vectors are never used by V3.
2. Clean passage input never reads forbidden derived metadata.
3. Clean vectors have genuine build-time provenance.
4. Frozen benchmark binds exact clean-vector identity.
5. Topic construction is independent of retrieval/qrels/DEV/TEST outcomes.
6. Base V3 topics are non-personalized.
7. Exactly three base query variants exist per topic.
8. DEV/TEST are family-disjoint.
9. BM25, clean dense, and title contribute independently.
10. Judged pool is the full independent top-20 direct union.
11. RRF changes order only, never membership.
12. `max_pool` cannot remove a V3 judged candidate.
13. Every pool job receives certain or uncertain state.
14. Judged grade 0 and unjudged are different.
15. Uncertain and grade 0 are different.
16. Unjudged top-K never silently scores as negative.
17. Three LLM views are not described as independent annotators.
18. Nugget extractor hints never establish support.
19. Support booleans are literal JSON booleans.
20. Adaptive support can inspect unhinted jobs.
21. Support examples are never falsely described as exhaustive.
22. Partial support examples are not used as unqualified recall ground truth.
23. Nugget prevalence remains unavailable without exhaustive verification.
24. Importance is independent of prevalence/frequency.
25. Evidence packing is deterministic and section-aware.
26. Free preflight performs zero external LLM calls.
27. Paid resources are initialized only after free blockers pass.
28. Failed construction cannot publish final output.
29. Finalization is atomic.
30. Critical artifacts are hash-bound.
31. Evaluators verify frozen integrity before work.
32. Evaluators verify sidecar identity before dense retrieval.
33. Family is bootstrap independent unit.
34. Retrieval TEST is one-shot.
35. RAG TEST is one-shot.
36. RAG judge schema is exact.
37. RAG arithmetic invariants are enforced.
38. Invalid schema retries use distinct cache identity.
39. Runtime dependencies are declared.
40. Native Django tests execute >0 tests.
41. No TEST is run during hardening.
42. No silent V2/V3 checkpoint mixing.
43. No hidden fallback model.
44. No evaluator continues after integrity failure.
45. No metric name overclaims what its data can support.

Any violation is a blocker unless the methodology is deliberately versioned and changed **before** inspecting TEST results.

---

# 48. Closing principle

CareerRAGBench-Auto-V3 should be judged by a stricter standard than:

> "the script runs."

A defensible benchmark makes invalid states explicit:

```text
unknown != negative
uncertain != negative
extractor hint != verified support
partial support != exhaustive recall
current source code != historical provenance
three prompts != three independent annotators
mocked green tests != native runtime reproduction
manifest exists != manifest verified
atomic write != reproducible semantics
DEV tuning != permission to repeatedly inspect TEST
```

The objective is not to maximize the number of reported metrics.

The objective is to build a benchmark whose corpus, annotation protocol, limitations, evidence, statistical assumptions, and frozen state can be reconstructed and defended after the original implementation context is gone.

That is the standard the final Codex audit should enforce.
