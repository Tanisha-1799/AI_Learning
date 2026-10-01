"""
query_transform.py

Prastav — Query Transformation
==============================
Generates search-friendly variants before retrieval.
"""
import os

from openai import OpenAI
from ssl_network import load_network_settings, create_http_client

settings = load_network_settings()
openai_kwargs = {
    "http_client": create_http_client(settings),
    "max_retries": settings.max_retries,
}
if settings.base_url:
    openai_kwargs["base_url"] = settings.base_url

client = OpenAI(**openai_kwargs)
MODEL = "gpt-5.4-mini"  # substitute your organisation's approved model

TRANSFORM_SYSTEM_PROMPT = (
    "You rewrite search queries for an RFP response evidence retrieval "
    "system. Be concise. Return ONLY the rewritten query text, with no "
    "explanation, preamble, or quotation marks."
)


def rewrite_query(question: str) -> str:
    """Restate the question more precisely for retrieval purposes."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": TRANSFORM_SYSTEM_PROMPT},
            {"role": "user", "content": f"Rewrite this search query to be clearer and more specific, "
                                         f"using precise technical or policy terminology where helpful:\n{question}"},
        ],
    )
    return response.choices[0].message.content.strip()


def multi_query(question: str, n: int = 3) -> list[str]:
    """Generate n different phrasings of the same underlying question."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": TRANSFORM_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Generate {n} different phrasings of this question, each on its own line, "
                f"no numbering, exploring different wordings or angles a document might use "
                f"to express the same underlying fact:\n{question}"
            )},
        ],
    )
    variants = [line.strip() for line in response.choices[0].message.content.split("\n") if line.strip()]
    return [question] + variants  # always include the original


def step_back_query(question: str) -> tuple[str, str]:
    """Generate a more general 'step back' version of the question.
    Returns (step_back_question, original_question) so callers can
    retrieve for both and combine."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": TRANSFORM_SYSTEM_PROMPT},
            {"role": "user", "content": (
                "Generate a more GENERAL version of this question — the kind of "
                "broader question you'd need the general principle behind before "
                f"answering the specific case:\n{question}"
            )},
        ],
    )
    step_back = response.choices[0].message.content.strip()
    return step_back, question


TECHNIQUES = {
    "none": lambda q: [q],
    "rewrite": lambda q: [rewrite_query(q)],
    "multi_query": lambda q: multi_query(q),
    "step_back": lambda q: list(step_back_query(q)),
}


def transform_query(question: str, technique: str = "none") -> list[str]:
    """Single entry point. Always returns a LIST of queries to retrieve
    for — even 'none' and 'rewrite', which return a list of one, so
    every caller can treat the output uniformly."""
    if technique not in TECHNIQUES:
        raise ValueError(f"Unknown query transform technique: {technique}. "
                          f"Choose from: {list(TECHNIQUES.keys())}")
    return TECHNIQUES[technique](question)
