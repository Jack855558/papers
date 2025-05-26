import sqlite3
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

# ----- 1. Load paper metadata from SQLite -----
conn = sqlite3.connect('arxiv_papers.db')
cur  = conn.cursor()
cur.execute("SELECT id, title, summary FROM papers")
rows = cur.fetchall()
conn.close()

paper_ids    = [row[0] for row in rows]
paper_titles = [row[1] for row in rows]
paper_texts  = [row[2] for row in rows]

print(f"Loaded {len(paper_ids)} papers from SQLite.")

# ----- 2. Embed abstracts (if not already embedded) -----
model = SentenceTransformer("all-MiniLM-L6-v2")

# Check if we already saved embeddings—if not, generate & save
if os.path.exists("arxiv_embeddings.npy") and os.path.exists("arxiv_metadata.pkl"):
    print("Loading previously saved embeddings & metadata...")
    embeddings = np.load("arxiv_embeddings.npy")
    with open("arxiv_metadata.pkl", "rb") as f:
        saved = pickle.load(f)
    # (Optional consistency check: ensure saved IDs match current paper_ids)
    assert saved["ids"] == paper_ids
    assert saved["titles"] == paper_titles
else:
    print("Generating embeddings for all papers (this may take a while)...")
    embeddings = model.encode(paper_texts, batch_size=64, show_progress_bar=True).astype("float32")
    np.save("arxiv_embeddings.npy", embeddings)
    with open("arxiv_metadata.pkl", "wb") as f:
        pickle.dump({"ids": paper_ids, "titles": paper_titles}, f)

# ----- 3. Build or load FAISS index -----
index_file = "arxiv_index_flatl2.faiss"
dim = embeddings.shape[1]

if os.path.exists(index_file):
    print("Loading saved FAISS index from disk...")
    index = faiss.read_index(index_file)
else:
    print("Creating new FAISS index and adding embeddings...")
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, index_file)

print(f"Index now contains {index.ntotal} vectors.")

# ----- 4. Define a search function -----
def search_papers(query_str, top_k=5):
    q_emb = model.encode([query_str]).astype("float32")
    distances, indices = index.search(q_emb, top_k)
    hits = []
    for rank, idx in enumerate(indices[0]):
        pid   = paper_ids[idx]
        title = paper_titles[idx]
        dist  = distances[0][rank]
        hits.append((pid, title, float(dist)))
    return hits

# ----- 5. Run a few test queries -----
test_queries = [
    "neural network image classification",
    "quantum computing qubits",
    "climate change carbon dioxide",
    "graph theory algorithms"
]

for q in test_queries:
    print(f"\n=== Query: “{q}” ===")
    results = search_papers(q, top_k=5)
    for rank, (pid, title, dist) in enumerate(results, start=1):
        print(f"{rank}. {pid} | {title} | distance={dist:.4f}")
