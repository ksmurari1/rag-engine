# 07 — Self-RAG and Corrective RAG

## 1. Why Reflection Matters

A standard RAG pipeline assumes:

```text
Retriever found something
        ↓
It must be useful
```

That assumption can fail.

A retriever can return:

- irrelevant chunks;
- outdated information;
- incomplete information;
- conflicting information;
- superficially similar text.

Advanced RAG can add evaluation and correction.

---

## 2. Self-RAG

Self-RAG introduces reflection into the retrieval and generation process.

A simplified application-level pattern is:

```text
Question
   ↓
Decide whether retrieval is needed
   ↓
Retrieve
   ↓
Evaluate retrieved context
   ↓
Generate
   ↓
Check grounding / support
   ↓
Accept or revise
```

### Use cases

Self-reflection is useful when:

- hallucination risk is high;
- answer grounding matters;
- retrieval quality varies;
- the application can afford additional model calls.

### Important distinction

A custom application that adds relevance and grounding graders is best described precisely as a **Self-RAG-inspired workflow** unless it actually implements the specific research architecture.

---

## 3. Corrective RAG

Corrective RAG focuses primarily on the quality of retrieval.

```text
Question
   ↓
Retrieve
   ↓
Grade retrieved information
   │
   ├── Good
   │    ↓
   │  Generate
   │
   ├── Ambiguous
   │    ↓
   │  Refine / broaden search
   │
   └── Poor
        ↓
      Correct retrieval
```

The correction could involve:

- changing the query;
- searching a different source;
- broadening retrieval;
- using external search where appropriate;
- rejecting unsupported context.

## 4. Self-RAG vs Corrective RAG

| | Self-RAG | Corrective RAG |
|---|---|---|
| Main focus | Reflection over retrieval and generation | Retrieval quality and correction |
| Typical question | "Is my retrieved evidence and answer good?" | "Is my retrieval good enough?" |
| Correction | Can occur before/after generation | Primarily retrieval correction |
| Complexity | Higher | Moderate to high |

## 5. Example

Suppose the uploaded PDFs contain:

```text
policy_v1.pdf
policy_v2.pdf
```

The user asks:

> What is the current policy?

If the retriever returns an old policy:

```text
Retriever
   ↓
Old policy
   ↓
Retrieval grader
   ↓
Insufficient
   ↓
Correct search / refine
```

A basic RAG system may confidently answer from the wrong document.

## 6. When NOT to Use These Techniques

Do not add reflection loops simply because they are advanced.

Avoid unnecessary complexity when:

- the corpus is small;
- retrieval is highly reliable;
- latency is important;
- a simple baseline already meets the quality target.

## 7. Relationship to Our Project

Our first Multi-PDF application should establish:

```text
Reliable ingestion
+
Good metadata
+
Good chunking
+
Good baseline retrieval
+
Source citations
```

Only after that should we test whether retrieval grading or answer validation improves results.
