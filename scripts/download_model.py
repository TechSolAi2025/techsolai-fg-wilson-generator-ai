"""Explicit setup step; runtime never downloads models."""
from pathlib import Path
from sentence_transformers import SentenceTransformer
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    model=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2',cache_folder=str(ROOT/'data/models/download_cache'))
    model.save(str(ROOT/'data/models/all-MiniLM-L6-v2'))
    print('Local embedding model saved; rebuild the corpus to bind its hash.')
