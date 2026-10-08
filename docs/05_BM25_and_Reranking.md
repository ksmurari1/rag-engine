# 05 — BM25 and Reranking

## 1. BM25

BM25 is a lexical information-retrieval method.

Instead of asking:

> Which text has the most similar meaning?

it primarily asks:

> Which documents contain terms that are important to this query, and how useful are those term matches?

## 2. Why BM25 Matters in RAG

BM25 is particularly useful for:

- exact names;
- IDs;
- product codes;
- error messages;
- technical terms;
- acronyms;
- policy numbers;
- strings where exact wording matters.

Example:

```text
Question:
What does error E4012 mean?
```

A lexical retriever has a natural advantage in finding documents containing `E4012`.

## 3. Vector Search vs BM25

| Dimension | Vector Search | BM25 |
|---|---|---|
| Main signal | Semantic similarity | Term relevance |
| Paraphrases | Strong | Weaker |
| Exact terms | Can be weaker | Strong |
| Codes / IDs | Can be weaker | Strong |
| Meaning across different wording | Strong | Weaker |
| Typical role | Semantic retrieval | Lexical retrieval |

## 4. Reranking

Initial retrieval is usually optimized for speed.

It can return a larger candidate set:

```text
Question
   ↓
Retriever
   ↓
20 candidates
```

A reranker then examines the question and each candidate more carefully:

```text
20 candidates
     ↓
 Reranker
     ↓
Top 5
```

This creates a two-stage retrieval architecture.

## 5. Why Two Stages?

Searching the entire corpus with an expensive relevance model would be costly.

Instead:

```text
Stage 1 — Fast retrieval
      ↓
Large candidate set

Stage 2 — More precise ranking
      ↓
Small final set
```

This is the standard recall-then-precision pattern.

## 6. Hybrid + Rerank

A stronger architecture can be:

```text
              Question
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
    Vector Search          BM25
        │                   │
        └─────────┬─────────┘
                  ▼
            Candidate Set
                  │
                  ▼
              Reranker
                  │
                  ▼
             Top Context
                  │
                  ▼
                 LLM
```

## 7. When to Add Reranking

Consider reranking when:

- top-k results are often only partially relevant;
- similar documents are difficult to distinguish;
- the vector store returns noisy candidates;
- answer quality improves when fewer, more precise chunks are supplied.

## 8. Reranking Trade-offs

Benefits:

- improved relevance ordering;
- better context quality;
- fewer distracting chunks.

Costs:

- additional computation;
- additional latency;
- more implementation complexity.

## 9. Engineering Rule

Do not assume:

```text
Top-k = good context
```

Measure whether the retrieved candidates actually answer the question.
