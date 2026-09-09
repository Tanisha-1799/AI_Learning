"""
inspect_vectorstore.py

Kosh - Peek Inside the Finance Vector Store
===========================================
Optional inspection script to show chunk text and metadata in ChromaDB and
inside chroma.sqlite3.
"""
import sqlite3

import chromadb

COLLECTION_NAME = "finance_docs"

print("=" * 64)
print("PART 1 - ChromaDB API view")
print("=" * 64)

client = chromadb.PersistentClient(path="./chroma_store")
collection = client.get_collection(COLLECTION_NAME)

print(f"\nCollection name : {collection.name}")
print(f"Total chunks    : {collection.count()}")

print("\nSample of 3 stored chunks with metadata:")
sample = collection.peek(limit=3)
for index, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"]), start=1):
    print(f"\n  --- Chunk {index} ---")
    print(f"  metadata : {meta}")
    print(f"  text     : {doc[:120]}...")

print("\n" + "=" * 64)
print("PART 2 - Direct SQLite view")
print("=" * 64)

db_path = "./chroma_store/chroma.sqlite3"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

print(f"\nTables found in {db_path}:")
for table_name in tables:
    print(f"  - {table_name}")

print("\nPreviewing up to 3 rows per table:")
for table_name in tables:
    print(f"\n  --- Table: {table_name} ---")
    try:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  columns: {columns}")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        rows = cursor.fetchall()
        if not rows:
            print("  (empty)")
        for row in rows:
            print(f"  {row}")
    except Exception as exc:
        print(f"  (could not read this table: {exc})")

conn.close()
