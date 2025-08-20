import os

HF_TOKEN = os.getenv("HF_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DB_FAISS_PATH = "vectorestore/db_faiss"
DATA_PATH = "data2/"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

DATABASE_NAME = "rag_db"
COLLECTION_NAME = "rag_collection"