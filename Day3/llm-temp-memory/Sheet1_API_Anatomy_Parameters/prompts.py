"""
Day 3 — Sheet 1: LLM API Anatomy, Parameters & Chat Completion Patterns
25 guided prompts covering multi-turn memory, temperature, max_tokens, stop sequences.

Usage:
    python prompts.py            -> lists all 25 prompts
    python prompts.py 3          -> runs prompt #3
"""
import sys
import time
from call_model import call_model, SYSTEM_PROMPT


class Conversation:
    def __init__(self, system_prompt):
        self.messages = [{"role": "system", "content": system_prompt}]

    def ask(self, user_text, **params):
        self.messages.append({"role": "user", "content": user_text})
        from call_model import client, MODEL
        response = client.chat.completions.create(model=MODEL, messages=self.messages, **params)
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply


def p01():
    convo = Conversation(SYSTEM_PROMPT)
    a1 = convo.ask("What is the guaranteed uptime in our SLA?")
    a2 = convo.ask("And the penalty if we miss it?")
    return f"Turn 1: {a1}\n\nTurn 2 (uses memory of turn 1): {a2}"


def p02():
    # Same follow-up question, but with NO conversation history — control comparison.
    return call_model(SYSTEM_PROMPT, "And the penalty if we miss it?")


def p03():
    results = [call_model(SYSTEM_PROMPT,
        "List 3 likely causes for a cell-down alert with 0 throughput.", temperature=0.0)
        for _ in range(3)]
    return "\n\n---\n\n".join(results)


def p04():
    results = [call_model(SYSTEM_PROMPT,
        "List 3 likely causes for a cell-down alert with 0 throughput.", temperature=0.9)
        for _ in range(3)]
    return "\n\n---\n\n".join(results)


def p05():
    results = [call_model(SYSTEM_PROMPT,
        "Draft one RFP sentence about network reliability.", temperature=0.9)
        for _ in range(3)]
    return "\n\n---\n\n".join(results)


def p06():
    results = [call_model(SYSTEM_PROMPT,
        "Classify this dispute: 'charged twice for same recharge.' "
        "Categories: Overcharge, Roaming Error, Plan Migration Error, Other.",
        temperature=0.0) for _ in range(3)]
    return "\n\n---\n\n".join(results)


def p07():
    return call_model(SYSTEM_PROMPT,
        "Write a full shift-handover summary for: Core-MME-07, Signalling Storm, High severity.",
        max_completion_tokens=20)


def p08():
    return call_model(SYSTEM_PROMPT,
        "Write a full shift-handover summary for: Core-MME-07, Signalling Storm, High severity.",
        max_completion_tokens=200)


def p09():
    return call_model(SYSTEM_PROMPT, "Explain EIRP to a new field engineer.", stop=["."])


def p10():
    convo = Conversation(SYSTEM_PROMPT)
    convo.ask("A customer's data pack ran out early — why might that happen?")
    return convo.ask("What plan am I on?")  # never stated — should not be guessed


def p11():
    low = call_model(SYSTEM_PROMPT,
        "Assess churn risk (state ONLY Low/Medium/High): usage down 30%, 2 tickets, renewal in 15 days.",
        temperature=0.0)
    high = call_model(SYSTEM_PROMPT,
        "Assess churn risk (state ONLY Low/Medium/High): usage down 30%, 2 tickets, renewal in 15 days.",
        temperature=0.9)
    return f"temperature=0.0: {low}\ntemperature=0.9: {high}"


def p12():
    convo = Conversation(SYSTEM_PROMPT)
    convo.ask("Alert: eNodeB-4471-Pune Cell Down, 0 throughput. What are 3 likely causes?")
    return convo.ask("Which of those is most likely, and why?")


def p13():
    convo = Conversation(SYSTEM_PROMPT)
    convo.ask("What's the guaranteed uptime in our SLA?")
    return convo.ask("What's your favourite football team?")


def p14():
    low_p = call_model(SYSTEM_PROMPT, "What is EIRP?", temperature=0.7, top_p=0.1)
    high_p = call_model(SYSTEM_PROMPT, "What is EIRP?", temperature=0.7, top_p=1.0)
    return f"top_p=0.1: {low_p}\n\ntop_p=1.0: {high_p}"


def p15():
    convo = Conversation(SYSTEM_PROMPT)
    convo.ask("What is the guaranteed uptime in our SLA?")
    convo.ask("And the penalty if we miss it?")
    convo.ask("What are the exclusions?")
    return convo.ask("Summarise everything we've discussed so far.")


def p16():
    return call_model(SYSTEM_PROMPT,
        "Draft a 100-word RFP response section about disaster recovery.", max_completion_tokens=40)


def p17():
    return call_model(SYSTEM_PROMPT,
        'Return JSON: {"category": str, "confidence": str} for: "charged twice for same recharge."',
        stop=["}"])


def p18():
    from call_model import client, MODEL
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "Additional note: always be extra concise."},
        {"role": "user", "content": "Explain EIRP briefly."},
    ]
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content


def p19():
    convo = Conversation(SYSTEM_PROMPT)
    facts = [
        "My data pack ran out early this month.",
        "This also happened last month.",
        "I'm on the family unlimited plan.",
        "I've called support twice already about this.",
        "I'm considering switching providers.",
        "What do you think is going on, and what should I do?",
    ]
    replies = [convo.ask(f) for f in facts]
    return replies[-1]


def p20():
    return call_model(SYSTEM_PROMPT,
        "List 3 likely causes for a cell-down alert.", temperature=0.0, max_completion_tokens=60)


def p21():
    convo = Conversation(SYSTEM_PROMPT)
    convo.ask("Customer fact 1: usage down 30% in 60 days.")
    convo.ask("Customer fact 2: 2 unresolved support tickets.")
    convo.ask("Customer fact 3: renewal due in 15 days.")
    return convo.ask("Given all 3 facts above, what is the overall churn risk?")


def p22():
    convo = Conversation(SYSTEM_PROMPT)
    before = len(str(convo.messages))
    for q in ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]:
        convo.ask(q)
    after = len(str(convo.messages))
    return f"Message history size before: {before} chars\nAfter 5 turns: {after} chars"


def p23():
    low = call_model(SYSTEM_PROMPT, "Explain EIRP.", temperature=0.2)
    high = call_model(SYSTEM_PROMPT, "Explain EIRP.", temperature=1.0)
    return f"temperature=0.2:\n{low}\n\ntemperature=1.0:\n{high}"


def p24():
    return call_model(SYSTEM_PROMPT,
        "Format this incident as ONE table row: Core-PGW-04 | Medium | Resolved.",
        stop=["\n"])


def p25():
    return call_model(SYSTEM_PROMPT,
        "In 2-3 sentences: which single parameter — temperature, max_tokens, or stop — "
        "would you reach for most often in production, and why?")


PROMPTS = {
    1: ("Multi-turn memory: uptime then penalty", p01),
    2: ("Same penalty question, NO memory (control)", p02),
    3: ("temperature=0.0, run 3x", p03),
    4: ("temperature=0.9, run 3x", p04),
    5: ("temperature=0.9 for creative RFP drafting", p05),
    6: ("temperature=0.0 for dispute classification", p06),
    7: ("max_tokens=20 (truncation)", p07),
    8: ("max_tokens=200 (compare to #7)", p08),
    9: ("stop=['.'] — cuts off after first sentence", p09),
    10: ("Multi-turn: asks about undisclosed info", p10),
    11: ("Risk LEVEL comparison: temp 0.0 vs 0.9", p11),
    12: ("Multi-turn RCA: causes then 'which is most likely'", p12),
    13: ("Multi-turn: scope rule holds mid-conversation", p13),
    14: ("top_p comparison at fixed temperature", p14),
    15: ("4-turn conversation ending in a summary request", p15),
    16: ("max_tokens too low for the requested content", p16),
    17: ("stop='}' on a JSON request", p17),
    18: ("Two system messages in one call", p18),
    19: ("6-turn conversation, facts spread across turns", p19),
    20: ("temperature=0.0 + max_tokens combined", p20),
    21: ("3 separate facts across turns, synthesis on 4th", p21),
    22: ("Message history size growth over 5 turns", p22),
    23: ("temperature 0.2 vs 1.0 on an explanation task", p23),
    24: ("stop='\\n' forces a single table row", p24),
    25: ("Reflection: most-used parameter", p25),
}


def main():
    if len(sys.argv) < 2:
        print("Sheet 1 — 25 Prompts. Run any one with: python prompts.py <number>\n")
        for n, (desc, _) in sorted(PROMPTS.items()):
            print(f"  {n:2d}. {desc}")
        return
    n = int(sys.argv[1])
    if n not in PROMPTS:
        print(f"No prompt #{n}. Valid range: 1-25.")
        return
    desc, fn = PROMPTS[n]
    print(f"--- Prompt #{n}: {desc} ---\n")
    start = time.time()
    print(fn())
    print(f"\n[took {time.time() - start:.1f}s]")


if __name__ == "__main__":
    main()
