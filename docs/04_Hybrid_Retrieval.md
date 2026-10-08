# 04 — Hybrid Retrieval

## 1. What Is Hybrid Retrieval?

Hybrid Retrieval combines multiple retrieval methods so that their strengths complement one another.

A common design is:

```text
                  User Question
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Vector Search           BM25
       Semantic match       Keyword match
             │                   │
             └─────────┬─────────┘
                       ▼
                Result Fusion
                       │
                       ▼
                  Reranking
                       │
                       ▼
                Final Context
```

## 2. Why Vector Search Alone Can Miss Things

Vector search is strong at meaning.

Example:

> How can we reduce cloud spending?

It may retrieve:

> Cloud cost optimization techniques

even without the exact words "reduce cloud spending."

But vector retrieval may be less reliable for exact strings such as:

```text
SKU-7842
ERR_CONNECTION_RESET
Policy ID HR-204
Power BI
Direct Lake
```

## 3. Why BM25 Alone Can Miss Things

BM25 is strong at lexical overlap.

But:

```text
Question:
How can we reduce cloud spending?
```

may not rank:

```text
Cloud expenditure optimization
```

as highly as a semantic model would.

## 4. Combined Strength

```text
Vector Search
     +
BM25
     ↓
Hybrid Retrieval
```

This gives the application two signals:

- semantic similarity;
- lexical/exact-term relevance.

## 5. When Should We Use Hybrid?

Use it when the corpus contains a mixture of:

- natural language;
- technical terminology;
- identifiers;
- product names;
- policy numbers;
- codes;
- abbreviations;
- domain-specific vocabulary.

### Example

Question:

> What is the SLA for product ABC-123?

Vector search helps understand the concept of SLA.

BM25 helps locate the exact `ABC-123`.

Together they can outperform either signal alone.

## 6. When NOT to Add Hybrid Automatically

Do not add hybrid retrieval merely because it sounds more advanced.

Basic vector retrieval may be enough when:

- the corpus is small;
- documents are clean;
- questions are semantic;
- retrieval quality is already high;
- the extra infrastructure is not justified.

## 7. Fusion Options

After two retrieval systems return candidates, their results need to be combined.

Possible approaches include:

- score normalization and weighted combination;
- rank-based fusion such as Reciprocal Rank Fusion (RRF);
- deduplication followed by reranking.

The exact choice depends on the retrieval system and evaluation results.

## 8. RAG Architecture Position

Hybrid retrieval belongs in the retrieval layer:

```text
Question
   ↓
Query Processing
   ↓
┌────────────────────┐
│ Hybrid Retrieval   │
│                    │
│ Vector + BM25      │
└─────────┬──────────┘
          ↓
      Reranking
          ↓
       Context
          ↓
         LLM
```

## 9. Project Decision

Our first Multi-PDF version will start with vector retrieval because that is the cleanest baseline for the assignment.

After the baseline works, we can test whether exact-term or retrieval-coverage problems justify adding BM25 and Hybrid Retrieval.
