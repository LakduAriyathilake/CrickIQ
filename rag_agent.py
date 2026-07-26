import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.get_or_create_collection(
    name="cricket_knowledge",
    embedding_function=embedding_fn
)

def answer_from_knowledge(question: str, n_results: int = 3) -> str:
    """Retrieve relevant docs, then ask the LLM to answer using only that context."""
    results = collection.query(query_texts=[question], n_results=n_results)
    retrieved_docs = results['documents'][0]

    context = "\n\n---\n\n".join(retrieved_docs)

    prompt = f"""You are a cricket rules expert. Answer the question using ONLY the
context provided below. If the context doesn't contain enough information to answer,
say so honestly rather than guessing.

Context:
{context}

Question: {question}

Answer:"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3  # slightly higher than SQL agent since this is explanatory text, not exact code
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    question = "What happens if a match gets rained out?"
    answer = answer_from_knowledge(question)
    print(answer)