import chromadb
from chromadb.utils import embedding_functions

# Persistent ChromaDB stored in /app/data
client = chromadb.PersistentClient(path="./data/chroma_db")
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = client.get_or_create_collection(
    name="chat_memory",
    embedding_function=embedding_func
)

def add_memory(text: str, metadata: dict):
    import uuid
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[str(uuid.uuid4())]
    )

def query_memory(query: str, user_email: str):
    # Search for past context relevant to the query for this specific user
    results = collection.query(
        query_texts=[query],
        where={"user_email": user_email},
        n_results=3
    )
    return results['documents']