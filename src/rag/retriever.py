# ============================================================
# src/rag/retriever.py
# Handles the RETRIEVAL phase of RAG:
# Search → Retrieve relevant chunks from ChromaDB
# Called every time the agent needs to look up information.
# ============================================================

from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from core.llm import get_embeddings
from config.settings import CHROMA_DB_PATH


def get_vectorstore(collection_name: str = "default"):
    """
    Connects to the existing ChromaDB database on disk.
    Does NOT rebuild it — just loads the already-indexed data.
    """
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=get_embeddings(),
        collection_name=collection_name
    )


def create_delivery_retriever_tool():
    """
    RAG tool that searches the delivery team roster.
    Node 2 uses this to find available resources matching the client's needs.
    """
    vectorstore = get_vectorstore("delivery_roster")

    @tool
    def search_delivery_capacity(query: str) -> str:
        """Search the delivery team roster for available people matching skills, roles, or seniority."""
        results = vectorstore.similarity_search(query, k=5)
        if not results:
            return "No matching resources found in the roster."
        return "\n\n".join([doc.page_content for doc in results])

    return search_delivery_capacity


def create_pricing_retriever_tool():
    """
    RAG tool that searches the pricing and policy documents.
    Node 4 uses this to apply correct rates and validate margins.
    """
    vectorstore = get_vectorstore("pricing_policy")

    @tool
    def search_pricing_policy(query: str) -> str:
        """Search pricing policy, rate cards, and discount rules."""
        results = vectorstore.similarity_search(query, k=4)
        if not results:
            return "No relevant pricing policy found."
        return "\n\n".join([doc.page_content for doc in results])

    return search_pricing_policy
