import chromadb
from chromadb.config import Settings
from pathlib import Path
import os

db_path = "./data/chroma_db"
os.makedirs(db_path, exist_ok=True)

print(f"Testing ChromaDB with path: {os.path.abspath(db_path)}")
try:
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(
            anonymized_telemetry=False,
            is_persistent=True
        )
    )
    print("PersistentClient created with explicit settings.")
    
    collection = client.get_or_create_collection(name="test_collection_v2")
    print(f"Collection 'test_collection_v2' retrieved/created. Count: {collection.count()}")
    
    collection.add(
        documents=["Test document"],
        ids=["doc1"],
    )
    print("Added document.")
    
    results = collection.query(query_texts=["test"], n_results=1)
    print(f"Query results: {results}")
    print("SUCCESS")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
