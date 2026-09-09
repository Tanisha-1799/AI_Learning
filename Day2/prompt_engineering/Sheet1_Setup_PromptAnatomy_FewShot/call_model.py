"""
call_model.py
Reusable helper for every prompt in this folder.
Loads OPENAI_API_KEY from .env — never hardcode it here.
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()  # automatically picks up OPENAI_API_KEY from the environment

# Substitute your organisation's approved model if different.
MODEL = "gpt-5.4-mini"


def call_model(system_prompt: str, user_prompt: str) -> str:
    """Send one system + one user message, return the model's text reply."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Quick smoke test — run this file directly to confirm your setup works.
    print(call_model("You are a helpful NCS Telco+ assistant.", "Say hello in one sentence."))
