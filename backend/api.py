from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Allow your frontend origin (or “*” for everything, though that’s less secure)
origins = [
    "http://localhost:3000", 
    "https://jack855558.github.io/papers/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Define data model for input
class Query(BaseModel):
    prompt: str
    top_k: int = 5

# Load FAISS index, model, and me`t`adata
model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("papers.index")

# Make sure you saved and are loading metadata in the same order
with open("paper_metadata.json", "r") as f:
    metadata = json.load(f)

@app.post("/query/")
async def query_index(data: Query):
    # Convert query into embedding
    embedding = model.encode([data.prompt])
    
    # Search FAISS index
    D, I = index.search(np.array(embedding).astype("float32"), data.top_k)
    
    # Format results
    results = []
    for score, idx in zip(D[0], I[0]):
        paper = metadata[idx]
        results.append({
            "title": paper["title"],
            "abstract": paper["abstract"],
            "score": float(score),
            "url": paper.get("url")
        })

    return {"results": results}
