# ============================================================
# src/config/settings.py
# ONE place for all configuration values.
# Every other file imports from here — never from os.getenv() directly.
# This means if a variable name changes, you fix it in ONE place only.
# ============================================================

from dotenv import load_dotenv
import os

# Load .env file into environment
load_dotenv()

# ── AI Model Settings ────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_CHAT_MODEL = os.getenv("LLM_CHAT_MODEL")
LLM_EMBEDDING_MODEL = os.getenv("LLM_EMBEDDING_MODEL")

# ── Storage Settings ─────────────────────────────────────────
# Path to the ChromaDB vector database folder
CHROMA_DB_PATH = "./storage/chroma_db"

# Path to the folder containing source documents for RAG
DOCUMENTS_PATH = "./data/documents"
