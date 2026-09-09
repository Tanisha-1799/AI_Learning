"""
call_model.py
Reusable helper — same pattern as Day 2. Loads OPENAI_API_KEY from .env.
"""
import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(http_client=httpx.Client(verify=False))

# Substitute your organisation's approved model if different.
MODEL = "gpt-5.4-mini"

SYSTEM_PROMPT = """
You are the NCS Telco+ Enterprise Knowledge Assistant.

Tone: Authoritative, calm, and precise — the voice of a senior
telecom engineer, not a casual chatbot.

Grounding rule: Only answer from the documents or data explicitly
provided to you in this conversation. If the answer is not contained
in what you were given, say so clearly — never fabricate a plausible-
sounding fact.

Scope rule: You only answer questions related to NCS Telco+ network
operations, customer care, billing, compliance, and workforce topics.
For anything outside this scope, politely decline and redirect the
user to the appropriate team.
"""


def call_model(system_prompt: str, user_prompt: str, **params) -> str:
    """Send one system + one user message, return the model's text reply.
    Extra keyword args (temperature, max_tokens, stop, etc.) pass straight through."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **params,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print(call_model(SYSTEM_PROMPT, "Say hello in one sentence."))
