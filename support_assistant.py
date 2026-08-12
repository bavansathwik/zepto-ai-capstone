from pathlib import Path
import chromadb 
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Create a persistent ChromaDB client
client = chromadb.PersistentClient(path=str(CHROMA_DIR))

# Create or get the collection
collection = client.get_or_create_collection(
    name="zepto_support"
)


def load_documents():
    """Load all documents and create one chunk per document."""

    documents = []
    ids = []
    metadatas = []

    for file_path in sorted(DOCS_DIR.glob("doc_*.txt")):
        text = file_path.read_text(encoding="utf-8").strip()

        documents.append(text)
        ids.append(file_path.stem)
        metadatas.append({
            "source": file_path.name
        })

    return documents, ids, metadatas


def build_index():
    """Embed all document chunks and store them in ChromaDB."""

    documents, ids, metadatas = load_documents()

    # Generate embeddings
    embeddings = model.encode(documents).tolist()

    # Store documents and embeddings in ChromaDB
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print("Documents loaded:", len(documents))
    print("Embeddings stored:", len(embeddings))
    print("ChromaDB collection:", collection.name)
    print("Total items in collection:", collection.count())

if __name__ == "__main__":
    build_index()