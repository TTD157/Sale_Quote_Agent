# ============================================================
# src/rag/indexer.py
# Handles the ONE-TIME setup phase of RAG:
# Load → Split → Embed → Store
# Run this script once whenever your documents change.
# ============================================================

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from core.llm import get_embeddings
from config.settings import CHROMA_DB_PATH, DOCUMENTS_PATH
import os


def build_index(collection_name: str = "default", documents_path: str = None):
    """
    Loads all .txt documents from the given path,
    splits them into chunks, embeds them, and stores
    them in ChromaDB under the given collection name.
    """
    docs_path = documents_path or DOCUMENTS_PATH

    # ── STEP 1: LOAD ────────────────────────────────────────
    all_docs = []
    for filename in os.listdir(docs_path):
        if filename.endswith(".txt"):
            filepath = os.path.join(docs_path, filename)
            loader = TextLoader(filepath, encoding="utf-8")
            all_docs.extend(loader.load())
            print(f"Loaded: {filename}")

    print(f"Total documents loaded: {len(all_docs)}")

    # ── STEP 2: SPLIT ───────────────────────────────────────
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(all_docs)
    print(f"Split into {len(chunks)} chunks")

    # ── STEP 3 & 4: EMBED + STORE ───────────────────────────
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=CHROMA_DB_PATH,
        collection_name=collection_name
    )
    print(f"Stored {len(chunks)} chunks in collection '{collection_name}'")
    print("Indexing complete!")

    return vectorstore


if __name__ == "__main__":
    # Run directly: python -m rag.indexer
    build_index()
