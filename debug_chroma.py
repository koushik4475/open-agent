import chromadb
from pathlib import Path
import os

db_path = "./data/chroma_db"
os.makedirs(db_path, exist_ok=True)

print(f"Testing ChromaDB with path: {os.path.abspath(db_path)}")
try:
    client = chromadb.PersistentClient(path=db_path)
    print("PersistentClient created.")
    
    collection = client.get_or_create_collection(name="test_collection")
    print(f"Collection 'test_collection' retrieved/created. Count: {collection.count()}")
    
    collection.add(
        documents=["Hello world"],
        ids=["1"],
    )
    print("Added document to collection.")
    
    results = collection.query(query_texts=["hello"], n_results=1)
    print(f"Query results: {results}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
