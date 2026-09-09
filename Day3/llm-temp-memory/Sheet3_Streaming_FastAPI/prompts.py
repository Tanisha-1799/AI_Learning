"""
Day 3 — Sheet 3: Streaming Responses & the Real-Time Chatbot Handler
25 guided prompts. Prompts 1-3, 7-9, 11-12, 14, 17, 21, 24-25 run here in the terminal.
Prompts 4-6, 10, 13, 15-16, 18-20, 22-23 are FastAPI exercises — see README_RUN_ME.md
for the exact curl commands to run against main.py.

Usage:
    python prompts.py            -> lists all 25 prompts
    python prompts.py 1          -> runs prompt #1 (terminal streaming demo)
"""
import sys
import time
from call_model import client, MODEL, SYSTEM_PROMPT


def stream_to_string(user_prompt, **params):
    """Stream a response, print it live, AND return the full joined string."""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
        **params,
    )
    pieces = []
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
            pieces.append(delta)
    print()
    return "".join(pieces)


def p01():
    stream_to_string("Explain EIRP to a field engineer.")
    return "(streamed above)"


def p02():
    start = time.time()
    stream_to_string("List 3 causes for a cell-down alert.")
    return f"\n[Total time: {time.time() - start:.2f}s]"


def p03():
    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": "List 3 causes for a cell-down alert."}],
    )
    elapsed = time.time() - start
    return f"Non-streaming total time: {elapsed:.2f}s\n{response.choices[0].message.content}"


def p07():
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": "Explain EIRP briefly."}],
        stream=True,
    )
    output = []
    for i, chunk in enumerate(stream):
        if i < 3:
            output.append(f"Chunk {i}: {chunk.choices[0].delta}")
        else:
            break
    return "\n".join(output)


def p08():
    stream_to_string("Assess churn risk for: usage down 30%, 2 tickets, renewal in 15 days.")
    return "(streamed above)"


def p09():
    full = stream_to_string("Draft a 100-word RFP section about disaster recovery.")
    return f"\n[Reconstructed full string, {len(full)} characters]"


def p11():
    start = time.time()
    first_token_time = None
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": "Explain EIRP."}],
        stream=True,
    )
    pieces = []
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            if first_token_time is None:
                first_token_time = time.time() - start
            pieces.append(delta)
    total_time = time.time() - start
    return f"Time to first token: {first_token_time:.2f}s\nTotal time: {total_time:.2f}s"


def p12():
    stream_to_string("Draft a 100-word RFP response about network reliability.")
    return "(longer output — notice how much more the streaming benefit shows)"


def p14():
    stream_to_string("List 3 causes for a cell-down alert.", temperature=0.0)
    print("\n--- now temperature=0.9 ---\n")
    stream_to_string("List 3 causes for a cell-down alert.", temperature=0.9)
    return "(both streamed above)"


def p17():
    print("[Discussion prompt — no code to run]")
    return ("What should happen if a browser user navigates away mid-stream? "
            "In FastAPI, the generator simply stops being iterated — discuss "
            "whether your production code needs explicit cleanup logic here.")


def p18():
    stream_to_string("Can you tell me a compliance officer's personal phone number?")
    return "(confirm the refusal survives streaming)"


def p21():
    short = stream_to_string("Give a one-sentence definition of EIRP.")
    print("\n--- now a longer answer ---\n")
    long = stream_to_string("Explain EIRP, its purpose, and why indoor limits differ from outdoor, in detail.")
    return f"\nShort answer: {len(short)} chars. Long answer: {len(long)} chars."


def p24():
    start = time.time()
    stream_to_string(
        "Write a full shift-handover summary covering: eNodeB-4471-Pune Cell Down (open), "
        "Core-PGW-04 Packet Loss (resolved), Core-MME-07 Signalling Storm (open)."
    )
    return f"\n[Total time: {time.time() - start:.2f}s]"


def p25():
    from call_model import call_model
    return call_model(SYSTEM_PROMPT,
        "In 2-3 sentences, name one NCS deliverable where streaming clearly helps, "
        "and one where it probably doesn't matter.")


FASTAPI_PROMPTS_NOTE = (
    "This prompt is a FastAPI exercise, not a terminal one.\n"
    "1) In a separate terminal, run: uvicorn main:app --reload --port 8000\n"
    "2) Then use the curl command / browser action noted in the practice sheet "
    "(Day3_Sheet_3_Streaming_FastAPI.docx) for this prompt number.\n"
    "3) See README_RUN_ME.md in this folder for a quick-reference list of all "
    "the FastAPI curl commands for prompts 4-6, 10, 13, 15-16, 18-20, 22-23."
)


def fastapi_placeholder():
    return FASTAPI_PROMPTS_NOTE


PROMPTS = {
    1: ("Stream to terminal: explain EIRP", p01),
    2: ("Stream + time the total duration", p02),
    3: ("Non-streaming version of #2, for comparison", p03),
    4: ("FastAPI: basic /chat?q=hello test", fastapi_placeholder),
    5: ("FastAPI: /chat with a real customer-care question", fastapi_placeholder),
    6: ("FastAPI: /chat with a handover question", fastapi_placeholder),
    7: ("Inspect raw stream chunks (first 3)", p07),
    8: ("Stream a churn-risk assessment", p08),
    9: ("Stream + reconstruct the full string", p09),
    10: ("FastAPI: /chat-sla endpoint test", fastapi_placeholder),
    11: ("Time-to-first-token measurement", p11),
    12: ("Stream a longer 100-word RFP draft", p12),
    13: ("FastAPI: /chat with an empty q= value", fastapi_placeholder),
    14: ("Stream + temperature: 0.0 vs 0.9", p14),
    15: ("FastAPI: visit /docs in a browser", fastapi_placeholder),
    16: ("FastAPI: /chat classifying a billing dispute", fastapi_placeholder),
    17: ("Discussion: stream cancellation on navigation away", p17),
    18: ("Stream a refusal-triggering question", p18),
    19: ("FastAPI: two curl calls at once (concurrency)", fastapi_placeholder),
    20: ("FastAPI: extend generate_stream with document grounding", fastapi_placeholder),
    21: ("Chunk count: short vs long answer", p21),
    22: ("FastAPI: add a temperature query parameter", fastapi_placeholder),
    23: ("FastAPI: add /chat-sync and compare to streaming", fastapi_placeholder),
    24: ("Stream a full multi-incident handover, timed", p24),
    25: ("Reflection: where streaming helps vs doesn't", p25),
}


def main():
    if len(sys.argv) < 2:
        print("Sheet 3 — 25 Prompts. Run any one with: python prompts.py <number>\n")
        print("(Prompts marked 'FastAPI:' need the server running — see README_RUN_ME.md)\n")
        for n, (desc, _) in sorted(PROMPTS.items()):
            print(f"  {n:2d}. {desc}")
        return
    n = int(sys.argv[1])
    if n not in PROMPTS:
        print(f"No prompt #{n}. Valid range: 1-25.")
        return
    desc, fn = PROMPTS[n]
    print(f"--- Prompt #{n}: {desc} ---\n")
    print(fn())


if __name__ == "__main__":
    main()
