import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="./chroma_db")

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="cricket_knowledge",
    embedding_function=embedding_fn
)

# Get ALL 5 documents ranked by similarity, not just the top 1
results = collection.query(
    query_texts=["What happens if a match gets rained out?"],
    n_results=5
)

for doc_id, distance in zip(results['ids'][0], results['distances'][0]):
    print(f"{doc_id}: {distance:.4f}")