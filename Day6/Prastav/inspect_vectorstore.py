"""Inspect persisted Prastav chunks and metadata in Chroma + SQLite."""
import sqlite3
import chromadb

print("=" * 64)
print("PART 1 - Through the ChromaDB API")
print("=" * 64)

client = chromadb.PersistentClient(path="./chroma_store")
collection = client.get_collection("prastav_documents")

print(f"\nCollection name : {collection.name}")
print(f"Total chunks    : {collection.count()}")

print("\nA sample of 5 stored chunks, with their metadata:")
sample = collection.peek(limit=5)
for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"]), start=1):
    print(f"\n  --- Chunk {i} ---")
    print(f"  metadata : {meta}")
    print(f"  text     : {doc[:100]}...")

print("\nCheck that doc_type, version, and effective_date appear in metadata.")

print("\n" + "=" * 64)
print("PART 2 - Directly inside chroma.sqlite3")
print("=" * 64)

db_path = "./chroma_store/chroma.sqlite3"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

print(f"\nReal tables found inside {db_path}:")
for table_name in tables:
    print(f"  - {table_name}")

print("\nPreviewing up to 3 rows from each table:")
for table_name in tables:
    print(f"\n  --- Table: {table_name} ---")
    try:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  columns: {columns}")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row}")
        if not rows:
            print("  (empty)")
    except Exception as exc:
        print(f"  (could not read this table: {exc})")

conn.close()

print("\n" + "=" * 64)
print("KEY TAKEAWAY")
print("=" * 64)
print(
    "Chunk text and metadata are persisted in SQLite-backed Chroma storage. "
    "Hybrid retrieval and reranking operate over these stored chunks."
)
