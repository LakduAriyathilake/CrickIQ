import os
import chromadb
from chromadb.utils import embedding_functions

# --- Step 1: Set up ChromaDB with a persistent local store ---
# This means the vector index is saved to disk in chroma_db/, not just in memory
client = chromadb.PersistentClient(path="./chroma_db")

# --- Step 2: Set up the embedding function ---
# This turns text into numerical vectors so ChromaDB can search by meaning, not just keywords
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# --- Step 3: Create (or get) a collection ---
# A "collection" in ChromaDB is like a table — a named group of related documents
collection = client.get_or_create_collection(
    name="cricket_knowledge",
    embedding_function=embedding_fn
)

# --- Step 4: Read every .txt file in knowledge_base/ and add it to the collection ---
knowledge_folder = "knowledge_base"

for filename in os.listdir(knowledge_folder):
    if filename.endswith(".txt"):
        filepath = os.path.join(knowledge_folder, filename)
        with open(filepath, "r") as f:
            text = f.read().strip()

        doc_id = filename.replace(".txt", "")  # e.g. "dls_method"

        collection.upsert(
            documents=[text],
            ids=[doc_id]
        )
        print(f"Loaded: {doc_id}")

print(f"\nTotal documents in collection: {collection.count()}")