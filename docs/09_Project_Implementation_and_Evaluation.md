# 09 — Project Implementation and Evaluation

## 1. Purpose

This document records the implementation decisions, validation tests, and retrieval observations from the working Multi-PDF RAG application.

The goal is not only to show that the application runs, but to explain what was validated and what the experiments revealed about baseline retrieval.

## 2. Implemented Application

The application is implemented in a single:

```text
rag_app.py
```

The baseline pipeline is:

```text
Multiple PDF uploads
        ↓
PDF page extraction
        ↓
File + page metadata
        ↓
Recursive chunking
        ↓
OpenAI embeddings
        ↓
Single FAISS vector store
        ↓
Semantic retrieval
        ↓
Retrieved candidate context
        ↓
Grounded chat model
        ↓
Answer + source citations
```

## 3. Validation Corpus

The working test used:

| Metric | Observed value |
|---|---:|
| PDF documents | 3 |
| PDF pages | 19 |
| Indexed chunks | 68 |
| Vector index | FAISS |

The application also exposes indexing performance, chunk previews, retrieval timing, LLM generation timing, and total query timing.

## 4. Validation Test 1 — Successful Baseline Retrieval

Question:

> What is Distill all about?

The application retrieved candidate chunks from the uploaded knowledge base and generated a grounded answer with file/page sources.

Representative result:

```text
Retrieval      ~0.75s
LLM generation ~2.16s
Total          ~2.94s
```

The exact latency can vary between runs because the LLM call is external.

### Conclusion

The baseline pipeline is functioning correctly for straightforward semantic questions whose evidence exists in the uploaded documents.

## 5. Validation Test 2 — Missing Evidence

Question:

> What is a reward-penalty mechanism?

The initial behavior looked like a possible retrieval problem. A diagnostic check showed that the phrase was not present in the indexed documents.

The root cause was later identified:

```text
Relevant source PDF
        ↓
Not uploaded
        ↓
Not indexed
        ↓
Cannot be retrieved
```

### Conclusion

This was not a defect in FAISS, chunking, or generation.

It demonstrated a fundamental RAG boundary:

> **Retrieval is constrained by the indexed knowledge base.**

A trustworthy application should say that the uploaded documents do not contain enough evidence rather than fabricate an answer.

## 6. Validation Test 3 — Cross-Document Retrieval

Question:

> Who manages FastML, and what PEFT technique does the FinVector-Market-4B paper use?

The intended evidence is distributed across two PDFs.

```text
Machine Learning (ML).pdf
        ↓
FastML evidence

FinVector-Market.pdf
        ↓
LoRA / PEFT evidence
```

### Experiment A — k = 4

The retriever returned candidates dominated by the FinVector document.

The FastML evidence was not retrieved.

### Experiment B — k = 8

Increasing the candidate count to eight still did not surface the required Machine Learning evidence.

### Conclusion

Increasing `k` improved retrieval breadth numerically, but did not guarantee coverage of every evidence path required by a compound question.

This is a retrieval limitation of the simple single-query semantic baseline.

## 7. Generation Behavior Was Correct

An important observation is that the LLM did not invent the missing FastML information.

It responded that the retrieved context did not contain enough information.

Therefore:

```text
Retrieval failure
       ↓
Missing evidence
       ↓
Grounded generation
       ↓
No hallucinated answer
```

This is preferable to a fluent but unsupported answer.

## 8. What Could Improve This Later?

If the workload requires more reliable compound or cross-document retrieval, candidate improvements include:

```text
Query decomposition
       ↓
Multiple retrieval calls
       ↓
Evidence from separate documents
       ↓
Context fusion
       ↓
Grounded generation
```

Other options documented in this repository include Hybrid Retrieval, BM25, reranking, Fusion/RRF, and corrective retrieval.

These are deliberately treated as **future, evidence-driven improvements**, not mandatory parts of the baseline assignment.

## 9. Chunking Observation

The assignment asks whether an answer citing many pages indicates that chunking is doing its job.

The correct answer is not simply "fewer citations are always better."

A strong chunking configuration should:

- preserve enough local context;
- avoid mixing unrelated topics;
- create retrieval units that are semantically meaningful;
- preserve file/page metadata;
- allow the retriever to return focused evidence.

If a question consistently requires many unrelated pages, inspect chunk boundaries and retrieval ranking before assuming that the LLM is the problem.

## 10. Conflict Handling

When multiple uploaded documents disagree, the system should not silently select one source.

The grounded generation prompt is designed to surface conflicts when the retrieved context contains contradictory information.

Conceptually:

```text
Document A → 12 days
Document B → 15 days
        ↓
Retrieved context
        ↓
LLM detects conflict
        ↓
Answer states the disagreement
        ↓
User can verify the cited sources
```

## 11. Final Engineering Takeaway

The project demonstrates a baseline-first RAG engineering approach:

```text
Build
  ↓
Observe
  ↓
Test retrieval separately
  ↓
Diagnose root cause
  ↓
Keep the baseline when it works
  ↓
Add advanced retrieval only when justified
```

The most important lesson is:

> **A working vector database does not guarantee good retrieval. RAG quality depends on the entire path from document ingestion and chunking through retrieval, context construction, generation, and source verification.**
