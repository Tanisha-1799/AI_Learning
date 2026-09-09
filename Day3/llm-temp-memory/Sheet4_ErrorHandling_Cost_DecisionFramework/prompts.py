"""
Day 3 — Sheet 4: Error Handling, Cost Tracking & the Decision Framework
25 guided prompts. Production-hardening patterns for everything built so far.

Usage:
    python prompts.py            -> lists all 25 prompts
    python prompts.py 6          -> runs prompt #6 (decision framework example)
"""
import sys
import time
from call_model import call_model, client, MODEL, SYSTEM_PROMPT

try:
    from openai import RateLimitError, APIError
except ImportError:
    RateLimitError = APIError = Exception  # fallback so this file still loads for listing


# ---------------- A. Retry with exponential backoff ----------------

def call_model_with_retry(system_prompt, user_prompt, max_retries=4):
    for attempt in range(max_retries):
        try:
            return call_model(system_prompt, user_prompt)
        except RateLimitError:
            wait = 2 ** attempt
            print(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
        except APIError as e:
            wait = 2 ** attempt
            print(f"API error: {e}. Waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Max retries exceeded — giving up.")


# ---------------- B. Token counting and cost tracking ----------------

PRICE_PER_MILLION_INPUT = 0.15   # substitute your model's real published pricing
PRICE_PER_MILLION_OUTPUT = 0.60


def call_model_tracked(system_prompt, user_prompt, **params):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **params,
    )
    usage = response.usage
    cost = (
        (usage.prompt_tokens / 1_000_000) * PRICE_PER_MILLION_INPUT +
        (usage.completion_tokens / 1_000_000) * PRICE_PER_MILLION_OUTPUT
    )
    print(f"Tokens: {usage.prompt_tokens} in / {usage.completion_tokens} out | Est. cost: ${cost:.5f}")
    return response.choices[0].message.content, cost


# ---------------- C. Budget guardrail ----------------

class BudgetTracker:
    def __init__(self, daily_limit_usd=5.00):
        self.daily_limit = daily_limit_usd
        self.spent = 0.0

    def record(self, cost):
        self.spent += cost
        if self.spent > self.daily_limit:
            raise RuntimeError(f"Budget exceeded: ${self.spent:.2f} > ${self.daily_limit:.2f}")
        print(f"Running spend: ${self.spent:.4f} / ${self.daily_limit:.2f}")


# ---------------- D. Decision framework ----------------

def decide_approach(needs_external_facts, facts_change_often, is_stable_style_task):
    if not needs_external_facts:
        return "PROMPT"
    if facts_change_often:
        return "RETRIEVE (RAG)"
    if is_stable_style_task:
        return "FINE-TUNE"
    return "RETRIEVE (RAG)"  # default safe choice when unsure


# ---------------- 25 Prompts ----------------

def p01():
    _, cost = call_model_tracked(SYSTEM_PROMPT, "Explain EIRP.")
    return f"Estimated cost: ${cost:.5f}"


def p02():
    _, cost_full = call_model_tracked(SYSTEM_PROMPT, "Give a full detailed RCA for a cell-down alert.")
    _, cost_short = call_model_tracked(SYSTEM_PROMPT, "In one sentence, give the most likely RCA for a cell-down alert.")
    return f"Full answer cost: ${cost_full:.5f}\nShort answer cost: ${cost_short:.5f}"


def p03():
    budget = BudgetTracker(daily_limit_usd=5.00)
    budget.record(0.001)
    budget.record(0.002)
    budget.record(0.0015)
    return f"Total spent: ${budget.spent:.5f}"


def p04():
    budget = BudgetTracker(daily_limit_usd=0.001)
    try:
        budget.record(0.01)
        return "No error raised — unexpected!"
    except RuntimeError as e:
        return f"Guardrail fired correctly: {e}"


def p05():
    import call_model as cm
    original_model = cm.MODEL
    cm.MODEL = "not-a-real-model-xyz"
    try:
        return call_model_with_retry(SYSTEM_PROMPT, "Explain EIRP.", max_retries=2)
    except Exception as e:
        return f"Failed as expected after retries: {e}"
    finally:
        cm.MODEL = original_model


def p06():
    return decide_approach(needs_external_facts=True, facts_change_often=True, is_stable_style_task=False)


def p07():
    return decide_approach(needs_external_facts=False, facts_change_often=False, is_stable_style_task=False)


def p08():
    return decide_approach(needs_external_facts=True, facts_change_often=False, is_stable_style_task=True)


def p09():
    return decide_approach(needs_external_facts=True, facts_change_often=True, is_stable_style_task=False)


def p10():
    long_doc = "A" * 4000  # simulate a long document
    _, cost = call_model_tracked(SYSTEM_PROMPT, f"Summarise this: {long_doc}")
    return f"Cost with a long document pasted in: ${cost:.5f}"


def p11():
    def tracked_with_retry(system_prompt, user_prompt, max_retries=4):
        for attempt in range(max_retries):
            try:
                return call_model_tracked(system_prompt, user_prompt)
            except (RateLimitError, APIError):
                time.sleep(2 ** attempt)
        raise RuntimeError("Max retries exceeded.")
    reply, cost = tracked_with_retry(SYSTEM_PROMPT, "Explain EIRP.")
    return f"Cost: ${cost:.5f}\nReply: {reply[:100]}..."


def p12():
    budget = BudgetTracker(daily_limit_usd=100.00)
    total = 0.0
    for i in range(20):
        _, cost = call_model_tracked(SYSTEM_PROMPT, f"Classify dispute #{i}: charged twice for recharge.")
        budget.record(cost)
        total += cost
    monthly_estimate = (total / 20) * 20000  # extrapolate to 20,000 tickets
    return f"Cost for 20 calls: ${total:.4f}\nExtrapolated for 20,000 tickets: ${monthly_estimate:.2f}"


def p13():
    import call_model as cm
    original_key = cm.client.api_key
    cm.client.api_key = "invalid-key-xyz"
    try:
        call_model(SYSTEM_PROMPT, "Explain EIRP.")
        return "No error raised — unexpected!"
    except Exception as e:
        return f"Exception type: {type(e).__name__}\nShould this be retried? Discuss — likely NOT, it's a config error, not transient."
    finally:
        cm.client.api_key = original_key


def p14():
    return decide_approach(needs_external_facts=True, facts_change_often=True, is_stable_style_task=False)


def p15():
    return ("Compare current pricing for a smaller/cheaper model tier vs. your current MODEL "
            "at https://openai.com/api/pricing (or your provider's pricing page) — "
            "note the trade-off with accuracy from Day 1, Sheet 4.")


def p16():
    from prompts import call_model_tracked as tracked  # self-reference for clarity
    _, cost_plain = call_model_tracked(SYSTEM_PROMPT, "What document type, topic is this? [sop excerpt placeholder]")
    return f"Plain-prompt cost (compare to function-calling cost from Sheet 2): ${cost_plain:.5f}"


def p17():
    for attempt in range(4):
        print(f"Attempt {attempt + 1}: would wait {2 ** attempt}s")
    return "Confirmed: backoff doubles each attempt (1s, 2s, 4s, 8s)."


def p18():
    budget = BudgetTracker(daily_limit_usd=10.00)
    for i in range(3):
        _, cost = call_model_tracked(SYSTEM_PROMPT, f"Write shift-handover summary #{i}.")
        budget.record(cost)
    return f"Cumulative spend across 3 handovers: ${budget.spent:.5f}"


def p19():
    # facts_change_often AND is_stable_style_task both True — check priority order in the function
    return decide_approach(needs_external_facts=True, facts_change_often=True, is_stable_style_task=True)


def p20():
    from call_model import call_model as base_call
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    total_cost = 0.0
    budget = BudgetTracker(daily_limit_usd=10.00)
    for i in range(5):
        messages.append({"role": "user", "content": f"Turn {i}: tell me something about telecom."})
        response = client.chat.completions.create(model=MODEL, messages=messages)
        usage = response.usage
        cost = (usage.prompt_tokens / 1_000_000) * PRICE_PER_MILLION_INPUT + \
               (usage.completion_tokens / 1_000_000) * PRICE_PER_MILLION_OUTPUT
        budget.record(cost)
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
    return f"Total cost across 5 turns: ${budget.spent:.5f}"


def p21():
    try:
        call_model_with_retry(SYSTEM_PROMPT, "force a failure somehow", max_retries=1)
    except RuntimeError as e:
        return f"Clear failure message: {e}"


def p22():
    return decide_approach(needs_external_facts=True, facts_change_often=True, is_stable_style_task=False)


def p23():
    def robust_call(system_prompt, user_prompt, budget: BudgetTracker, max_retries=4):
        for attempt in range(max_retries):
            try:
                reply, cost = call_model_tracked(system_prompt, user_prompt)
                budget.record(cost)
                return reply
            except (RateLimitError, APIError):
                time.sleep(2 ** attempt)
        raise RuntimeError("Max retries exceeded.")
    budget = BudgetTracker(daily_limit_usd=5.00)
    return robust_call(SYSTEM_PROMPT, "Explain EIRP.", budget)


def p24():
    _, cost = call_model_tracked(SYSTEM_PROMPT, "Explain EIRP.")
    monthly = cost * 500 * 30
    return f"Per-call cost: ${cost:.5f}\nEstimated for 500 calls/day x 30 days: ${monthly:.2f}"


def p25():
    return call_model(SYSTEM_PROMPT,
        "In 2-3 sentences, which of retries, cost tracking, budget guardrails, or the "
        "decision framework would you implement FIRST in a real project, and why?")


PROMPTS = {
    1: ("Cost tracking: basic call", p01),
    2: ("Cost comparison: full vs. short answer", p02),
    3: ("Budget guardrail: accumulate spend", p03),
    4: ("Budget guardrail: trip the limit", p04),
    5: ("Retry logic: simulated failure with invalid model", p05),
    6: ("Decision framework: SLA Q&A -> RETRIEVE", p06),
    7: ("Decision framework: general writing -> PROMPT", p07),
    8: ("Decision framework: stable style task -> FINE-TUNE", p08),
    9: ("Decision framework: apply to Workforce Skilling Q&A", p09),
    10: ("Cost tracking: large document pasted in", p10),
    11: ("Retry + cost tracking combined", p11),
    12: ("Budget + extrapolation: 20 calls -> 20,000 tickets", p12),
    13: ("Error handling: invalid API key", p13),
    14: ("Decision framework: churn-risk scoring -> RETRIEVE", p14),
    15: ("(Manual) Compare model tier pricing", p15),
    16: ("Cost: plain prompt (compare to Sheet 2's function-call cost)", p16),
    17: ("Backoff timing confirmation (1s, 2s, 4s, 8s)", p17),
    18: ("Budget: cumulative spend across 3 calls", p18),
    19: ("Decision framework edge case: both flags true", p19),
    20: ("Cost tracking across a 5-turn conversation", p20),
    21: ("Max retries reached: clear failure message", p21),
    22: ("Decision framework: SLA fine-tune discussion", p22),
    23: ("Full production pattern: retry + cost + budget combined", p23),
    24: ("Monthly cost estimate: 500 calls/day", p24),
    25: ("Reflection: which pattern to implement first", p25),
}


def main():
    if len(sys.argv) < 2:
        print("Sheet 4 — 25 Prompts. Run any one with: python prompts.py <number>\n")
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
