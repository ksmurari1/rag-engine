"""
RAG Engine — Multi-PDF RAG Application

Multi-PDF RAG pipeline:

    Multiple PDFs
          ↓
    PDF Page Loading
          ↓
    Metadata Preservation
          ↓
    Recursive Text Splitting
          ↓
    OpenAI Embeddings
          ↓
    FAISS Vector Store
          ↓
    Semantic Retrieval
          ↓
    Grounded LLM Generation
          ↓
    Answer + Source Citations

Performance principles:
    1. Do not rebuild the vector store on every Streamlit rerun.
    2. Do not embed the same chunks twice.
    3. Cache reusable model objects.
    4. Rebuild the knowledge base only when uploaded PDFs change.
    5. Measure retrieval and LLM latency separately.
"""

# ============================================================
# BLOCK 1 — IMPORTS
# ============================================================

import hashlib
import os
import tempfile
import time

import streamlit as st

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# BLOCK 2 — APPLICATION INITIALIZATION
# ============================================================
# PURPOSE:
#   Initialize Streamlit and load environment variables.
#
# PERFORMANCE:
#   No expensive RAG processing happens here.
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="Multi-PDF RAG",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Multi-PDF RAG Assistant")

st.write(
    "Upload multiple PDF documents and ask questions "
    "across the combined knowledge base."
)


# ============================================================
# BLOCK 3 — API KEY VALIDATION
# ============================================================
# PURPOSE:
#   Validate the OpenAI API key before attempting embeddings
#   or LLM generation.
# ============================================================

if not os.getenv("OPENAI_API_KEY"):

    st.error(
        "OPENAI_API_KEY was not found. "
        "Please add it to your .env file."
    )

    st.stop()


# ============================================================
# BLOCK 4 — CACHED MODEL INITIALIZATION
# ============================================================
# PURPOSE:
#   Create reusable OpenAI model objects.
#
# PERFORMANCE:
#   Streamlit reruns the script whenever the user interacts
#   with the application.
#
#   @st.cache_resource prevents these reusable model objects
#   from being recreated unnecessarily.
# ============================================================


@st.cache_resource
def get_embeddings():
    """
    Create and cache the OpenAI embedding model.

    The same embedding model object can be reused for:
        - document indexing
        - user question retrieval
    """

    return OpenAIEmbeddings(
        model="text-embedding-3-small"
    )


@st.cache_resource
def get_llm():
    """
    Create and cache the ChatOpenAI model.

    Temperature 0 is used for deterministic,
    document-grounded answers.
    """

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )


# ============================================================
# BLOCK 5 — MULTI-PDF UPLOAD
# ============================================================
# PURPOSE:
#   Allow the user to upload multiple PDFs.
#
# ASSIGNMENT REQUIREMENT:
#   All uploaded PDFs become one combined knowledge base.
# ============================================================

uploaded_files = st.file_uploader(
    "Upload PDF documents",
    type=["pdf"],
    accept_multiple_files=True
)


if not uploaded_files:

    st.info(
        "Please upload one or more PDF documents to begin."
    )

    st.stop()


# ============================================================
# BLOCK 6 — DISPLAY UPLOADED DOCUMENTS
# ============================================================

st.success(
    f"{len(uploaded_files)} PDF document(s) uploaded."
)

with st.expander("📄 Uploaded Documents", expanded=True):

    for uploaded_file in uploaded_files:

        st.write(
            f"📄 **{uploaded_file.name}** "
            f"({uploaded_file.size:,} bytes)"
        )


# ============================================================
# BLOCK 7 — CREATE CORPUS FINGERPRINT
# ============================================================
# PURPOSE:
#   Detect whether the uploaded PDF collection has changed.
#
# WHY:
#   Streamlit reruns the script whenever the user interacts
#   with the UI.
#
#   Without change detection:
#
#       Question 1
#           ↓
#       rebuild embeddings
#
#       Question 2
#           ↓
#       rebuild embeddings
#
#       Question 3
#           ↓
#       rebuild embeddings
#
#   This would be extremely inefficient.
#
# Instead:
#
#       Same PDFs
#           ↓
#       Reuse existing FAISS
#
#       New/changed PDFs
#           ↓
#       Rebuild FAISS
# ============================================================


def create_corpus_fingerprint(files):
    """
    Create a deterministic fingerprint for the uploaded PDFs.

    The fingerprint changes if:
        - a PDF is added
        - a PDF is removed
        - a PDF filename changes
        - PDF content changes
    """

    hasher = hashlib.sha256()

    for uploaded_file in sorted(
        files,
        key=lambda file: file.name
    ):

        file_bytes = uploaded_file.getvalue()

        hasher.update(
            uploaded_file.name.encode("utf-8")
        )

        hasher.update(
            file_bytes
        )

    return hasher.hexdigest()


corpus_fingerprint = create_corpus_fingerprint(
    uploaded_files
)


# ============================================================
# BLOCK 8 — PDF LOADING + PAGE METADATA
# ============================================================
# PURPOSE:
#   Load all pages from all PDFs.
#
# METADATA:
#   Preserve:
#       - source filename
#       - file_name
#       - page number
#
# IMPORTANT:
#   PyPDFLoader uses zero-based page numbering.
#   We convert to human-readable numbering only when displaying
#   citations.
# ============================================================


def load_pdf_documents(files):

    all_documents = []

    page_statistics = []

    for uploaded_file in files:

        temp_path = None

        try:

            # ------------------------------------------------
            # Create temporary PDF file
            # ------------------------------------------------

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_file:

                temp_file.write(
                    uploaded_file.getvalue()
                )

                temp_path = temp_file.name


            # ------------------------------------------------
            # Load PDF pages
            # ------------------------------------------------

            loader = PyPDFLoader(
                temp_path
            )

            pdf_pages = loader.load()


            # ------------------------------------------------
            # Preserve actual uploaded filename
            # ------------------------------------------------

            for page in pdf_pages:

                page.metadata["source"] = (
                    uploaded_file.name
                )

                page.metadata["file_name"] = (
                    uploaded_file.name
                )


            all_documents.extend(
                pdf_pages
            )

            page_statistics.append(
                (
                    uploaded_file.name,
                    len(pdf_pages)
                )
            )

        finally:

            # ------------------------------------------------
            # Remove temporary file
            # ------------------------------------------------

            if (
                temp_path
                and os.path.exists(temp_path)
            ):

                os.remove(temp_path)


    return (
        all_documents,
        page_statistics
    )


# ============================================================
# BLOCK 9 — BUILD KNOWLEDGE BASE ONLY WHEN NECESSARY
# ============================================================
# PURPOSE:
#   Build:
#
#       PDF pages
#           ↓
#       Chunks
#           ↓
#       Embeddings
#           ↓
#       FAISS
#
# PERFORMANCE:
#   This block executes only when the uploaded PDF collection
#   changes.
# ============================================================


if (
    "corpus_fingerprint" not in st.session_state
    or
    st.session_state["corpus_fingerprint"]
    != corpus_fingerprint
):

    # --------------------------------------------------------
    # New corpus detected
    # --------------------------------------------------------

    st.session_state["corpus_fingerprint"] = (
        corpus_fingerprint
    )

    st.session_state.pop(
        "vector_store",
        None
    )

    st.session_state.pop(
        "all_chunks",
        None
    )

    st.session_state.pop(
        "all_documents",
        None
    )

    st.session_state.pop(
        "page_statistics",
        None
    )


    # --------------------------------------------------------
    # Loading stage
    # --------------------------------------------------------

    loading_start = time.perf_counter()

    with st.spinner(
        "📄 Loading PDF documents..."
    ):

        all_documents, page_statistics = (
            load_pdf_documents(
                uploaded_files
            )
        )

    loading_time = (
        time.perf_counter()
        - loading_start
    )


    # --------------------------------------------------------
    # Store loaded pages
    # --------------------------------------------------------

    st.session_state["all_documents"] = (
        all_documents
    )

    st.session_state["page_statistics"] = (
        page_statistics
    )


    # --------------------------------------------------------
    # Text splitting
    # --------------------------------------------------------

    chunking_start = time.perf_counter()

    text_splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    )

    all_chunks = (
        text_splitter.split_documents(
            all_documents
        )
    )

    chunking_time = (
        time.perf_counter()
        - chunking_start
    )


    st.session_state["all_chunks"] = (
        all_chunks
    )


    # --------------------------------------------------------
    # Embedding + FAISS creation
    # --------------------------------------------------------
    #
    # IMPORTANT PERFORMANCE FIX:
    #
    # We DO NOT call:
    #
    #     embeddings.embed_documents(...)
    #
    # first.
    #
    # FAISS.from_documents() will perform the embedding operation
    # itself.
    #
    # This prevents the previous implementation from embedding
    # the same chunks twice.
    # --------------------------------------------------------

    indexing_start = time.perf_counter()

    embeddings = get_embeddings()

    with st.spinner(
        "🧠 Creating embeddings and FAISS index..."
    ):

        vector_store = (
            FAISS.from_documents(
                documents=all_chunks,
                embedding=embeddings
            )
        )

    indexing_time = (
        time.perf_counter()
        - indexing_start
    )


    # --------------------------------------------------------
    # Store vector store in session state
    # --------------------------------------------------------

    st.session_state["vector_store"] = (
        vector_store
    )

    st.session_state["indexing_time"] = (
        indexing_time
    )

    st.session_state["loading_time"] = (
        loading_time
    )

    st.session_state["chunking_time"] = (
        chunking_time
    )


# ============================================================
# BLOCK 10 — KNOWLEDGE BASE STATUS
# ============================================================

all_documents = st.session_state[
    "all_documents"
]

all_chunks = st.session_state[
    "all_chunks"
]

vector_store = st.session_state[
    "vector_store"
]

page_statistics = st.session_state[
    "page_statistics"
]


st.subheader("📊 Knowledge Base")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "PDF Documents",
        len(uploaded_files)
    )

with col2:

    st.metric(
        "PDF Pages",
        len(all_documents)
    )

with col3:

    st.metric(
        "Indexed Chunks",
        len(all_chunks)
    )

with col4:

    st.metric(
        "Vector Index",
        "FAISS"
    )

st.caption(
    "Baseline RAG: all uploaded PDFs are combined into one "
    "semantic knowledge base."
)


# ============================================================
# BLOCK 11 — INDEXING PERFORMANCE
# ============================================================
# PURPOSE:
#   Make indexing performance visible.
#
# IMPORTANT:
#   These timings appear only when a new corpus is indexed.
# ============================================================

if "indexing_time" in st.session_state:

    with st.expander(
        "⚡ Indexing Performance"
    ):

        st.write(
            f"📄 PDF loading: "
            f"`{st.session_state['loading_time']:.2f}s`"
        )

        st.write(
            f"✂️ Chunking: "
            f"`{st.session_state['chunking_time']:.2f}s`"
        )

        st.write(
            f"🧠 Embeddings + FAISS: "
            f"`{st.session_state['indexing_time']:.2f}s`"
        )


# ============================================================
# BLOCK 12 — CHUNK PREVIEW
# ============================================================
# PURPOSE:
#   Allow inspection of the first few chunks.
# ============================================================

with st.expander(
    "🔍 Preview Generated Chunks"
):

    for index, chunk in enumerate(
        all_chunks[:3],
        start=1
    ):

        st.markdown(
            f"### Chunk {index}"
        )

        source = chunk.metadata.get(
            "source",
            "Unknown"
        )

        page_number = chunk.metadata.get(
            "page"
        )

        if page_number is not None:
            page_number += 1

        st.caption(
            f"📄 {source} | "
            f"Page {page_number if page_number is not None else 'Unknown'}"
        )

        st.write(
            chunk.page_content[:500]
        )


# ============================================================
# BLOCK 13 — SEMANTIC RETRIEVAL
# ============================================================
# PURPOSE:
#   Retrieve the top candidate chunks for a user question.
#
# BASELINE:
#   Top 4 candidate chunks.
#
# PERFORMANCE:
#   Retrieval itself is local FAISS search.
#   The expensive network operation happens when the question
#   embedding is generated by OpenAI.
# ============================================================

retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 4
    }
)

# ============================================================
# BLOCK 14 — QUESTION INPUT
# ============================================================

st.subheader(
    "💬 Ask Your Documents"
)

question = st.text_input(
    "Enter your question",
    placeholder=(
        "Example: What is the main idea "
        "of the Transformer architecture?"
    )
)


ask_button = st.button(
    "🔎 Ask",
    type="primary"
)


# ============================================================
# BLOCK 15 — RETRIEVAL + LLM GENERATION
# ============================================================

if ask_button and question.strip():

    clean_question = question.strip()

    total_start = time.perf_counter()


    # --------------------------------------------------------
    # STEP 1 — RETRIEVAL
    # --------------------------------------------------------

    retrieval_start = time.perf_counter()

    with st.spinner(
        "🔎 Searching the knowledge base..."
    ):

        retrieved_chunks = (
            retriever.invoke(
                clean_question
            )
        )

    retrieval_time = (
        time.perf_counter()
        - retrieval_start
    )


    st.success(
        f"Retrieved {len(retrieved_chunks)} candidate chunks."
    )


    # --------------------------------------------------------
    # STEP 2 — SHOW RETRIEVAL RESULTS
    # --------------------------------------------------------
    # This is useful during development because it allows us
    # to verify retrieval independently from generation.
    # --------------------------------------------------------

    with st.expander(
        "🔎 Retrieved Context (Top Candidates)"
    ):

        for index, chunk in enumerate(
            retrieved_chunks,
            start=1
        ):

            source = chunk.metadata.get(
                "source",
                "Unknown"
            )

            page_number = chunk.metadata.get(
                "page"
            )

            if page_number is not None:

                page_number = (
                    int(page_number) + 1
                )

            st.markdown(
                f"### Retrieved Chunk {index}"
            )

            st.caption(
                f"📄 {source} | "
                f"Page "
                f"{page_number if page_number is not None else 'Unknown'}"
            )

            st.write(
                chunk.page_content
            )


    # --------------------------------------------------------
    # STEP 3 — BUILD CONTEXT
    # --------------------------------------------------------

    context_parts = []

    for chunk in retrieved_chunks:

        context_parts.append(
            chunk.page_content
        )

    context = (
        "\n\n"
        "--- Retrieved Chunk ---"
        "\n\n"
        .join(context_parts)
    )


    # --------------------------------------------------------
    # STEP 4 — CREATE RAG PROMPT
    # --------------------------------------------------------

    rag_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a document-grounded RAG assistant.

Answer the user's question using ONLY the
information contained in the retrieved context.

Rules:

1. Do not invent facts.
2. Do not use outside knowledge.
3. If the retrieved context does not contain
   enough information, say so clearly.
4. Give a concise and useful answer.
5. If the context contains conflicting information,
   explicitly mention the conflict instead of choosing
   one source without evidence.
6. Do not create or guess source filenames,
   page numbers, or citations.
7. Base the answer only on the supplied context.

Retrieved Context:
{context}
"""
            ),
            (
                "human",
                "{question}"
            )
        ]
    )


    formatted_prompt = rag_prompt.invoke(
        {
            "context": context,
            "question": clean_question
        }
    )


    # --------------------------------------------------------
    # STEP 5 — LLM GENERATION
    # --------------------------------------------------------
    # PERFORMANCE DIAGNOSTIC:
    #
    # This timer specifically measures the OpenAI generation
    # call.
    #
    # If this number is high, the delay is NOT FAISS.
    # It is primarily the LLM/API round trip and generation.
    # --------------------------------------------------------

    llm_start = time.perf_counter()

    with st.spinner(
        "🤖 Generating grounded answer..."
    ):

        llm = get_llm()

        response = llm.invoke(
            formatted_prompt
        )

    llm_time = (
        time.perf_counter()
        - llm_start
    )


    # --------------------------------------------------------
    # STEP 6 — DISPLAY ANSWER
    # --------------------------------------------------------

    st.subheader(
        "🤖 Answer"
    )

    st.write(
        response.content
    )


    # ========================================================
    # BLOCK 16 — SOURCE CITATIONS
    # ========================================================
    # PURPOSE:
    #   Display the actual PDF source and page associated with
    #   retrieved chunks.
    #
    # IMPORTANT:
    #   Source citations come from Document metadata.
    #
    #   The LLM does NOT invent these citations.
    # ========================================================

    st.subheader(
        "📚 Sources"
    )

    displayed_sources = set()

    for chunk in retrieved_chunks:

        source_file = chunk.metadata.get(
            "source",
            "Unknown document"
        )

        page_number = chunk.metadata.get(
            "page"
        )

        if page_number is not None:

            page_number = (
                int(page_number) + 1
            )

        source_key = (
            source_file,
            page_number
        )

        # Prevent duplicate file/page citations.
        if source_key in displayed_sources:

            continue

        displayed_sources.add(
            source_key
        )

        if page_number is not None:

            st.write(
                f"📄 **{source_file}** — "
                f"Page **{page_number}**"
            )

        else:

            st.write(
                f"📄 **{source_file}**"
            )


    # ========================================================
    # BLOCK 17 — QUERY PERFORMANCE
    # ========================================================
    # PURPOSE:
    #   Make the performance characteristics of the RAG pipeline
    #   visible.
    #
    # This helps distinguish:
    #
    #   Retrieval latency
    #   vs
    #   LLM latency
    # ========================================================

    total_time = (
        time.perf_counter()
        - total_start
    )


    st.subheader(
        "⚡ Query Performance"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Retrieval",
            f"{retrieval_time:.2f}s"
        )

    with col2:

        st.metric(
            "LLM Generation",
            f"{llm_time:.2f}s"
        )

    with col3:

        st.metric(
            "Total Query",
            f"{total_time:.2f}s"
        )


# ============================================================
# BLOCK 18 — ARCHITECTURE SUMMARY
# ============================================================
# PURPOSE:
#   Show the complete baseline RAG architecture inside the app.
# ============================================================

with st.expander(
    "🏗️ RAG Architecture"
):

    st.code(
        """
Multiple PDFs
     ↓
PDF Page Loading
     ↓
Page Metadata
     ↓
Recursive Text Splitting
     ↓
OpenAI Embeddings
     ↓
FAISS Vector Store
     ↓
Semantic Retrieval
     ↓
Retrieved Context
     ↓
ChatOpenAI
     ↓
Grounded Answer
     ↓
PDF + Page Source Citations
        """,
        language="text"
    )

