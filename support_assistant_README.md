## Support Assistant Architecture

The Support Assistant implements a Retrieval-Augmented Generation (RAG) pipeline consisting of four main stages: ingestion, embedding, retrieval, and generation.

### 1. Ingestion

The source corpus consists of eight Zepto policy documents stored as text files in the `support_assistant/docs/` directory (`doc_01.txt` through `doc_08.txt`).

The `load_documents()` function in `support_assistant.py` reads all `doc_*.txt` files. Because the documents are short, each document is treated as one chunk. Each chunk is assigned its document ID and source filename.

### 2. Embedding

The document chunks are embedded locally using the `all-MiniLM-L6-v2` model from the `sentence-transformers` library.

The `build_index()` function in `support_assistant.py` generates an embedding for each document chunk and stores the embeddings in the persistent ChromaDB collection named `zepto_support`.

The resulting ChromaDB database is stored locally in the `support_assistant/chroma_db/` directory.

### 3. Retrieval

When a customer asks a question, the `classify_intent` node in `graph.py` first determines whether the query is a `policy_question` or a `general_question`.

For a `policy_question`, the LangGraph flow routes the query to the `retrieve_and_answer` node. This node embeds the query using `all-MiniLM-L6-v2` and queries the `zepto_support` ChromaDB collection for the top three most similar chunks using cosine similarity.

The retrieved document chunks and their source IDs are then passed to the answer-generation stage.

For a `general_question`, the graph routes directly to the `direct_answer` node, so no ChromaDB retrieval is performed.

### 4. Generation

For a policy question in the default mock mode, the `retrieve_and_answer` node creates a deterministic answer from the most similar retrieved chunk. It uses the first approximately 200 characters of the top retrieved chunk to produce the answer.

For a general question in mock mode, the `direct_answer` node returns a fixed response indicating that the assistant currently answers Zepto policy questions.

The final response is validated using the `SupportResponse` Pydantic model, which contains `answer`, `sources`, and `confidence` fields.

The `prompts.py` structured prompt is used by the optional real-LLM generation path to provide the retrieved context and customer question to the LLM.

### MOCK_LLM behavior

The `MOCK_LLM` environment variable controls the LLM-dependent stages of the pipeline.

By default, when `MOCK_LLM` is unset or set to `1`, the system runs entirely in the deterministic mock mode used for grading. Intent classification uses the required keyword heuristic, policy questions use real embedding and ChromaDB retrieval followed by the deterministic canned answer, and general questions use the fixed canned response. No LLM API call is made.

When `MOCK_LLM=0`, the optional real-LLM path is enabled. Intent classification can use the LLM, and answer generation can use the structured prompt from `prompts.py` together with the retrieved context. Embedding and ChromaDB retrieval remain local and unchanged.

### End-to-end data flow

```text
Zepto policy documents
        │
        ▼
support_assistant/docs/
        │
        ▼
load_documents()
        │
        ▼
One chunk per document
        │
        ▼
all-MiniLM-L6-v2
        │
        ▼
ChromaDB: zepto_support
        │
        │
        │ Customer query
        ▼
classify_intent
        │
        ├── general_question ──► direct_answer
        │
        └── policy_question ──► retrieve_and_answer
                                      │
                                      ▼
                              Query embedding
                                      │
                                      ▼
                              Top-3 ChromaDB chunks
                                      │
                                      ▼
                              Answer generation
                                      │
                                      ▼
                              SupportResponse
                                      │
                                      ▼
                              FastAPI /ask



