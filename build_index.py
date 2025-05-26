import sqlite3, json, pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# 1) Read from SQLite
conn = sqlite3.connect("arxiv_papers.db")
cur  = conn.cursor()
cur.execute("SELECT id, title, summary, url FROM papers")
rows = cur.fetchall()
conn.close()

paper_ids    = [r[0] for r in rows]
paper_titles = [r[1] for r in rows]
paper_summaries = [r[2] for r in rows]
paper_urls   = [r[3] for r in rows]

# 2) Generate embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(paper_summaries, batch_size=64, show_progress_bar=True).astype("float32")

# 3) Build and save FAISS index
dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)
faiss.write_index(index, "papers.index")

# 4) Save metadata in the same order
metadata = []
for idx in range(len(paper_ids)):
    metadata.append({
        "id":       paper_ids[idx],
        "title":    paper_titles[idx],
        "abstract": paper_summaries[idx],
        "url":      paper_urls[idx]
    })
with open("paper_metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f)

print(f"Built FAISS index with {index.ntotal} vectors and saved to papers.index")
