import os
import pdfplumber
import requests
from sqlalchemy import text
from app.model import Chunk
from app.db import engine, SessionLocal, Base
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent"
PDF_PATH = "/app/insurance-sample.pdf"

# pg vector enable
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()


Base.metadata.create_all(bind=engine)

def extract_chunks(pdf_path: str, max_words: int = 150):
    chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if not text:
                continue
            words = text.split()
            for i in range(0, len(words), max_words):
                chunks.append(" ".join(words[i:i + max_words]))
    return chunks



def embed_chunks(chunks):
    headers = {"Content-Type": "application/json"}
    embeddings = []
    for chunk in chunks:

        data = {
            "model": "models/embedding-001",
            "content": {"parts": [{"text": chunk}]},
            "task_type": "retrieval_document"
        }

        r = requests.post(f"{EMBED_URL}?key={GEMINI_API_KEY}", headers=headers, json=data)

        if r.status_code == 200:
            embeddings.append(r.json()["embedding"]["values"])

        else:
            embeddings.append([0.0] * 768)
    return embeddings

def store_chunks(chunks, embeddings):

    db = SessionLocal()

    for chunk, emb in zip(chunks, embeddings):
        db.add(Chunk(chunk=chunk, embedding=emb))


    db.commit()
    db.close()

def ingest_if_needed():

    if not os.path.exists("already_ingested.txt"):
        print("[Ingest] Chunking and embedding PDF...")
        chunks = extract_chunks(PDF_PATH)
        embeddings = embed_chunks(chunks)
        store_chunks(chunks, embeddings)

        
        with open("already_ingested.txt", "w") as f:
            f.write("done")
        print("[Ingest] Done.")

if __name__ == "__main__":
    ingest_if_needed()
