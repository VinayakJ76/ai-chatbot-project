import chromadb
from chromadb.utils import embedding_functions
import uuid

# Persistent Client stored in Docker Volume
client = chromadb.PersistentClient(path="./data/chroma_db")

# Using a lightweight local embedding model
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Collection acts as Long-Term Memory
ltm_collection = client.get_or_create_collection(
    name="semantic_memory",
    embedding_function=embedding_func
)

def add_to_ltm(text: str, metadata: dict):
    """Adds a memory vector to Long-Term Storage."""
    if not text.strip():
        return
    ltm_collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[str(uuid.uuid4())]
    )

def query_ltm(query: str, user_id: str, n_results: int = 3):
    """Searches Long-Term Memory for relevant past context."""
    results = ltm_collection.query(
        query_texts=[query],
        where={"user_id": user_id}, # Privacy filter
        n_results=n_results
    )
    
    if results and results['documents']:
        return results['documents'][0]
    return []