"""
main.py — the FastAPI streaming chatbot backend (the official design-doc lab).

Run with:
    uvicorn main:app --reload --port 8000

Then, in a second terminal:
    curl "http://localhost:8000/chat?q=Explain+EIRP+to+a+field+engineer"

Or visit http://localhost:8000/docs for interactive API documentation.
"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from call_model import client, MODEL, SYSTEM_PROMPT

app = FastAPI(title="NCS Telco+ Streaming Chatbot Backend")


def generate_stream(user_prompt: str, temperature: float = 0.7):
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
        temperature=temperature,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


@app.get("/chat")
def chat(q: str, temperature: float = 0.7):
    """Streaming endpoint — the real-time chatbot UI backend pattern."""
    return StreamingResponse(generate_stream(q, temperature), media_type="text/plain")


@app.get("/chat-sla")
def chat_sla(q: str):
    """A second, more specific streaming endpoint — always grounds in SLA context."""
    grounded_prompt = f"Answer this in the context of a standard telecom SLA: {q}"
    return StreamingResponse(generate_stream(grounded_prompt), media_type="text/plain")


@app.get("/chat-sync")
def chat_sync(q: str):
    """Non-streaming fallback — returns the full answer at once, for comparison."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q},
        ],
    )
    return {"answer": response.choices[0].message.content}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
