# 06 — Fusion RAG

## 1. The Problem Fusion Solves

A single query can represent only one wording of a user's information need.

Consider:

> How does Fabric improve analytics performance?

Possible useful formulations include:

```text
How does Microsoft Fabric improve query performance?
What performance benefits does Fabric provide?
How does Fabric optimize analytical workloads?
What Fabric capabilities improve analytics efficiency?
```

Different formulations can retrieve different documents.

## 2. Fusion RAG

Fusion RAG creates multiple search perspectives and combines their results.

```text
                 User Question
                      │
                      ▼
                Query Generation
              ┌──────┼──────┐
              ▼      ▼      ▼
             Q1     Q2     Q3
              │      │      │
              ▼      ▼      ▼
           Search Search Search
              │      │      │
              └──────┼──────┘
                     ▼
               Rank Fusion
                     │
                     ▼
             Final candidates
```

## 3. Reciprocal Rank Fusion

A common rank-fusion approach is RRF.

Conceptually:

```text
RRF score = Σ 1 / (rank + k)
```

where `k` is a smoothing constant.

The key idea is:

> A document appearing near the top in multiple rankings receives a stronger combined score.

## 4. Why Fusion Works

Suppose:

```text
Query 1 → Document A ranked #1
Query 2 → Document A ranked #3
Query 3 → Document A ranked #2
```

Document A is consistently relevant.

Another document may appear #1 for only one query but not appear in the other rankings.

Fusion rewards repeated evidence across query perspectives.

## 5. When to Use Fusion

Consider it when:

- user questions are ambiguous;
- terminology varies significantly;
- one query formulation frequently misses useful chunks;
- retrieval recall is more important than minimal latency.

## 6. Fusion vs Hybrid

These solve different problems.

### Hybrid Retrieval

Combines **different retrieval signals**:

```text
Vector + BM25
```

### Fusion

Combines **multiple rankings or query perspectives**:

```text
Query 1 → ranking
Query 2 → ranking
Query 3 → ranking
       ↓
     Fusion
```

They can also be combined:

```text
Multiple Queries
      ↓
Vector + BM25
      ↓
Multiple rankings
      ↓
RRF
      ↓
Rerank
```

## 7. Trade-offs

Benefits:

- better retrieval coverage;
- less dependence on one query wording;
- useful for ambiguous questions.

Costs:

- more searches;
- more latency;
- more tokens if query generation uses an LLM;
- additional ranking complexity.

## 8. Project Guidance

Fusion is an enhancement, not a baseline requirement for the Multi-PDF assignment.

First establish whether ordinary retrieval is insufficient.
