# 03 — RAG Types

## 1. Important Principle

Different RAG techniques solve different problems.

They are **not a checklist of components that every RAG application must implement**.

The correct question is:

> What retrieval or generation problem are we trying to solve?

Then select the simplest technique that addresses it.

## 2. Basic RAG

```text
Question
   ↓
Retriever
   ↓
Context
   ↓
LLM
   ↓
Answer
```

### Use when

- the knowledge base is relatively clean;
- questions are straightforward;
- semantic retrieval is working well;
- application complexity should remain low.

This is the correct starting point for our Multi-PDF assignment.

## 3. Self-RAG

Self-RAG introduces reflection around retrieval and generation.

Conceptually:

```text
Question
   ↓
Should retrieval be used?
   ↓
Retrieve
   ↓
Are results useful?
   ↓
Generate
   ↓
Is answer supported?
   ↓
Accept / Correct
```

### Use when

- answer grounding is critical;
- retrieval quality varies;
- the system needs a reflection or validation loop.

### Important terminology

A production application can implement a **Self-RAG-inspired reflective workflow** using graders or validation steps. That should not automatically be described as reproducing the original research architecture.

## 4. Corrective RAG

Corrective RAG evaluates retrieval quality and takes corrective action when the retrieved information is insufficient.

```text
Question
   ↓
Retrieve
   ↓
Grade retrieval
   ├── Good → Generate
   ├── Ambiguous → Refine / broaden
   └── Poor → Correct / search another source
```

### Use when

- the knowledge base may be incomplete;
- retrieval can fail;
- external or alternate search is available;
- wrong retrieval is more dangerous than slower retrieval.

## 5. Fusion RAG

Fusion RAG creates multiple query perspectives and combines the resulting rankings.

```text
Original Question
       ↓
 ┌─────┼─────┐
 ▼     ▼     ▼
Q1    Q2    Q3
 │     │     │
 ▼     ▼     ▼
Search each query
       ↓
Combine rankings
       ↓
RRF / fusion
       ↓
Final candidates
```

### Use when

- one wording may miss relevant documents;
- questions are ambiguous;
- terminology varies across documents;
- broader retrieval coverage is required.

## 6. BM25 + Reranking

BM25 provides lexical retrieval, while reranking improves the ordering of retrieved candidates.

```text
Question
   ↓
BM25 / Vector / Hybrid
   ↓
Candidate documents
   ↓
Reranker
   ↓
Best context
```

### Use when

- exact terms matter;
- semantic search misses important terminology;
- initial retrieval returns relevant-but-not-optimal results.

## 7. Hybrid Retrieval

Hybrid Retrieval combines different retrieval signals, commonly:

```text
Vector Search + BM25
```

It is especially useful when both semantic meaning and exact terms matter.

## 8. Decision Table

| Problem | Good starting strategy |
|---|---|
| Simple semantic questions | Basic vector RAG |
| Exact IDs / codes / names | BM25 |
| Meaning + exact terminology | Hybrid |
| Weak candidate ordering | Reranking |
| Multiple interpretations | Fusion |
| Poor/incomplete retrieval | Corrective |
| Need answer/retrieval reflection | Self-RAG-inspired workflow |

## 9. Design Rule

> **Start simple. Measure. Then add retrieval intelligence where the evidence shows it is needed.**

A complex RAG pipeline is not automatically a better RAG pipeline.
