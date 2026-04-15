# ============================================================
# src/core/llm.py
# ONE place to create the LLM and embeddings objects.
# Any file that needs the AI model just imports from here.
# If we ever switch models, we only change this ONE file.
# ============================================================

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from config.settings import GOOGLE_API_KEY, LLM_CHAT_MODEL, LLM_EMBEDDING_MODEL


def get_llm():
    """
    Returns the configured Gemini chat model.
    thinking_budget=0 disables thinking mode — required for tool compatibility.
    """
    return ChatGoogleGenerativeAI(
        model=LLM_CHAT_MODEL,
        google_api_key=GOOGLE_API_KEY,
        thinking_budget=0
    )


def get_embeddings():
    """
    Returns the configured embeddings model.
    Used by RAG to convert text chunks into vectors.
    """
    return GoogleGenerativeAIEmbeddings(
        model=LLM_EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY
    )
