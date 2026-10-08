# 01 — RAG Fundamentals

## 1. What is RAG?

**Retrieval-Augmented Generation (RAG)** is an application pattern in which a language model is supplied with relevant external information before generating an answer.

The core idea is:

```text
User Question
      ↓
Retrieve relevant information
      ↓
Augment the prompt with that information
      ↓
Generate an answer
```

Instead of expecting the model to know every piece of information internally, the application gives the model access to a knowledge source at query time.

## 2. Why RAG?

RAG is particularly useful when the answer depends on:

- private or enterprise documents;
- PDFs and manuals;
- policies and procedures;
- technical documentation;
- frequently changing information;
- a knowledge base that was not part of the model's training data.

### Traditional LLM

```text
Question → LLM → Answer
```

### RAG

```text
Question
   ↓
Retriever
   ↓
Relevant Context
   ↓
LLM
   ↓
Grounded Answer
```

## 3. The Three RAG Stages

### Retrieval

Find information relevant to the user's question.

### Augmentation

Place the retrieved information into the context supplied to the language model.

### Generation

Ask the language model to produce an answer using the question and retrieved context.

## 4. Core Components

| Component | Responsibility |
|---|---|
| Document Loader | Reads source documents |
| Text Splitter | Breaks documents into useful chunks |
| Embedding Model | Converts text into numerical vectors |
| Vector Store | Stores vectors and supports similarity search |
| Retriever | Finds relevant chunks for a question |
| Prompt | Defines how retrieved context should be used |
| LLM | Generates the final response |
| Metadata | Preserves source information such as file and page |

## 5. RAG Is More Than a Vector Database

A weak mental model is:

```text
PDF → Vector DB → LLM
```

A stronger model is:

```text
Documents
   ↓
Load
   ↓
Clean / Parse
   ↓
Chunk
   ↓
Metadata
   ↓
Embed
   ↓
Index
   ↓
Retrieve
   ↓
Rank / Filter
   ↓
Prompt
   ↓
Generate
   ↓
Cite Sources
```

Retrieval quality strongly affects answer quality.

## 6. Example

Suppose three PDFs contain HR information:

```text
policy.pdf
handbook.pdf
faq.pdf
```

The question is:

> How many leave days does a new joiner receive?

RAG searches the uploaded knowledge base, retrieves relevant chunks, and gives those chunks to the LLM.

A good answer should also identify the supporting sources.

If documents disagree, the application should not silently choose one. It should surface the conflict.

## 7. Key Principle

> **RAG does not make information automatically true. It makes external information available to the model.**

Therefore, source quality, chunking, retrieval, ranking, prompt design, and evaluation all matter.

## 8. Baseline for Our Project

The first implementation will use:

```text
Multiple PDFs
    ↓
PyPDFLoader
    ↓
Recursive chunking
    ↓
OpenAI embeddings
    ↓
FAISS
    ↓
Retriever
    ↓
Chat model
    ↓
Answer + file/page sources
```

This baseline directly matches the assignment before we consider advanced retrieval strategies.
