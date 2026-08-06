"""
RAG service: the piece that ties retrieval + generation together.

This is the actual 'Retrieval Augmented Generation' pattern:
  1. RETRIEVE the most relevant facts from our own data (vectorstore.py)
  2. AUGMENT the AI's prompt by injecting those facts as context
  3. GENERATE an answer, instructed to use ONLY that context

This is what prevents hallucination — we're not asking Gemini
"what do you know about Paracetamol", we're asking "given THESE
exact facts about Paracetamol, answer this question."
"""

import google.generativeai as genai

from app.core.config import settings
from app.ai.vectorstore import search_relevant_products

genai.configure(api_key=settings.GEMINI_API_KEY)

_SYSTEM_INSTRUCTION = (
    "You are a medical product assistant helping pharmaceutical sales "
    "representatives. Answer the user's question using ONLY the product "
    "information provided in the context below. If the context does not "
    "contain enough information to answer confidently, say so clearly "
    "instead of guessing. Keep answers concise and practical for a sales "
    "conversation. Never invent dosages, side effects, or facts that are "
    "not present in the context."
)


def ask_medical_assistant(question: str) -> dict:
    """
    Returns a dict with the answer AND which products were used as
    sources — so the frontend can show "this answer was based on
    Product X and Product Y", building trust in the response.
    """
    matches = search_relevant_products(question, top_k=3)

    if not matches:
        return {
            "answer": (
                "I don't have any product information in the knowledge base yet. "
                "Ask a Product Manager or Admin to add products first."
            ),
            "sources": [],
        }

    context_block = "\n\n---\n\n".join(m["document"] for m in matches)

    prompt = (
        f"{_SYSTEM_INSTRUCTION}\n\n"
        f"CONTEXT:\n{context_block}\n\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER:"
    )

    model = genai.GenerativeModel("gemini-flash-lite-latest")
    response = model.generate_content(prompt)

    return {
        "answer": response.text,
        "sources": [m["brand_name"] for m in matches],
    }