"""
inspect_vectorstore.py

Saathi — Peek Inside the Vector Store
=======================================
Optional, but the single best way to demystify "vector database" for a room.

This script does two things:

  PART 1 — Uses the normal ChromaDB API to show the collection you built,
  a sample of stored chunks, and their metadata. This is the same metadata
  app.py uses to cite a policy in every answer.

  PART 2 — Opens the underlying chroma.sqlite3 file DIRECTLY with Python's
  built-in sqlite3 module (no ChromaDB involved) and lists whatever real
  tables Chroma actually created, then previews a few raw rows from each.
  This proves the "metadata bookkeeping" side of a vector database is
  ordinary SQLite — nothing mysterious.

Run this AFTER build_vectorstore.py:
    python inspect_vectorstore.py

Note: exact table names can vary slightly between ChromaDB versions — this
script discovers whatever tables actually exist on your machine rather than
assuming a fixed schema, so it stays accurate regardless of version.
"""
import sqlite3
import chromadb

print("=" * 64)
print("PART 1 — Through the ChromaDB API (the way your app.py sees it)")
print("=" * 64)

client = chromadb.PersistentClient(path="./chroma_store")
collection = client.get_collection("hr_policies")

print(f"\nCollection name : {collection.name}")
print(f"Total chunks    : {collection.count()}")

print("\nA sample of 3 stored chunks, with the metadata attached to each:")
sample = collection.peek(limit=3)
for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"]), start=1):
    print(f"\n  --- Chunk {i} ---")
    print(f"  metadata : {meta}")
    print(f"  text     : {doc[:120]}...")

print("\nThis 'metadata' dict — {{'source': ..., 'chunk_index': ...}} — is exactly")
print("what build_vectorstore.py attached to every chunk, and exactly what")
print("app.py reads back to tell you which policy an answer came from.")

print("\n" + "=" * 64)
print("PART 2 — Directly inside chroma.sqlite3 (no ChromaDB API involved)")
print("=" * 64)

db_path = "./chroma_store/chroma.sqlite3"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

print(f"\nReal tables found inside {db_path}:")
for t in tables:
    print(f"  - {t}")

print("\nPreviewing up to 3 rows from each table (column names + values):")
for t in tables:
    print(f"\n  --- Table: {t} ---")
    try:
        cursor.execute(f"PRAGMA table_info({t});")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  columns: {columns}")
        cursor.execute(f"SELECT * FROM {t} LIMIT 3;")
        rows = cursor.fetchall()
        if not rows:
            print("  (empty)")
        for row in rows:
            print(f"  {row}")
    except Exception as e:
        print(f"  (could not read this table: {e})")

conn.close()

print("\n" + "=" * 64)
print("KEY TAKEAWAY")
print("=" * 64)
print("""
ChromaDB stores your chunk TEXT and METADATA (source, chunk_index) as
ordinary rows in a real SQLite database — the file you just read from
directly above, no special driver needed. There's no magic in that part.

The VECTORS themselves (the actual embeddings) are handled differently:
they're indexed on disk in a structure built for fast nearest-neighbour
search (an HNSW index), stored in per-collection segment files alongside
the SQLite file — because finding "which of 31 vectors is closest to this
new one" is not a job plain SQL rows are built for (this is exactly the
SQL-vs-vector-database lesson from earlier in the programme).

So when app.py calls collection.query(...), here's what actually happens:
  1. ChromaDB searches its vector index for the closest embeddings
  2. it uses the matching internal ids to look up the real text + metadata
     for those chunks in the SQLite tables you just previewed above
  3. both are handed back to your Python code together

That's the entire mechanism behind "Saathi cited the Leave Policy" — a
numeric nearest-neighbour match, resolved back into a real filename via
an ordinary SQLite lookup.
""")
