"""
Report generation service: turns raw visit notes into polished,
professional reports using Gemini.

Unlike the RAG chatbot (Module 3), this doesn't need retrieval —
we already have all the facts we need (the visit log itself). This
is a simpler, more direct use of the AI: rewriting/structuring
text well, not answering open-ended questions.
"""

import google.generativeai as genai

from app.core.config import settings
from app.models.visit_log import VisitLog
from app.models.doctor import Doctor

genai.configure(api_key=settings.GEMINI_API_KEY)

_MODEL_NAME = "gemini-flash-lite-latest"


def generate_visit_report(visit: VisitLog, doctor: Doctor) -> str:
    """Turns one raw visit log into a polished, professional report paragraph."""
    products = ", ".join(visit.products_discussed) if visit.products_discussed else "None recorded"

    prompt = (
        "You are helping a pharmaceutical Medical Representative write a "
        "professional visit report for their manager. Rewrite the raw notes "
        "below into a clear, well-structured report (3-5 sentences). Use a "
        "professional tone. Do NOT invent any facts not present in the notes — "
        "only rephrase and organize what's given.\n\n"
        f"Doctor: {doctor.full_name} ({doctor.specialization or 'N/A'})\n"
        f"Visit date: {visit.visit_date}\n"
        f"Products discussed: {products}\n"
        f"Outcome: {visit.outcome or 'Not specified'}\n"
        f"Raw notes: {visit.raw_notes}\n\n"
        "Professional report:"
    )

    model = genai.GenerativeModel(_MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text


def generate_period_report(visits: list[tuple[VisitLog, Doctor]], period_label: str) -> str:
    """
    Summarizes MULTIPLE visits into one report — e.g. a weekly summary
    for a manager. Takes (visit, doctor) pairs so doctor names are
    available without a second database round-trip per visit.
    """
    if not visits:
        return f"No visits were recorded for {period_label}."

    visit_lines = []
    for visit, doctor in visits:
        products = ", ".join(visit.products_discussed) if visit.products_discussed else "none"
        visit_lines.append(
            f"- {visit.visit_date}: Dr. {doctor.full_name} ({doctor.specialization or 'N/A'}), "
            f"products: {products}, outcome: {visit.outcome or 'N/A'}, notes: {visit.raw_notes}"
        )
    visits_block = "\n".join(visit_lines)

    prompt = (
        "You are helping a pharmaceutical Medical Representative summarize "
        f"their visits for {period_label} into a report for their manager. "
        "Write a concise summary (one short paragraph) covering overall "
        "activity, then a brief bullet list of notable outcomes or follow-ups "
        "needed. Base this ONLY on the visit data provided — do not invent "
        "any details.\n\n"
        f"Visits:\n{visits_block}\n\n"
        "Summary report:"
    )

    model = genai.GenerativeModel(_MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text
