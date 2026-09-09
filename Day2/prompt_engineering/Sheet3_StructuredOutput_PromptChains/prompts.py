"""
Day 2 — Sheet 3: Structured Output & Prompt Chains with Citations
25 guided prompts. Uses chain.py (which reads the two starter PDFs in this folder)
plus direct call_model.py calls for standalone JSON/table exercises.

Usage:
    python prompts.py            -> lists all 25 prompts
    python prompts.py 4          -> runs prompt #4 (the full citation chain on the SOP)
"""
import sys
import json
from call_model import call_model
from chain import SYSTEM_PROMPT, step1_extract, step2_format, run_chain, sop_text, sla_text


def p01():
    return call_model(SYSTEM_PROMPT,
        'Return STRICT JSON: {"term": str, "definition": str}. Term: EIRP.')


def p02():
    return call_model(SYSTEM_PROMPT,
        'Return STRICT JSON: {"category": str, "confidence": "High/Medium/Low"} '
        "for: 'roaming charge despite roaming being off.'")


def p03():
    return call_model(SYSTEM_PROMPT,
        "Return as a markdown table with columns Incident | Severity | Status, "
        "for these 2 incidents: (1) eNodeB-4471-Pune Cell Down, Critical, Open. "
        "(2) Core-PGW-04 Packet Loss, Medium, Resolved.")


def p04():
    return run_chain(sop_text, "What is the maximum indoor EIRP for Band 78?")


def p05():
    return run_chain(sop_text, "What is the minimum antenna mounting height?")


def p06():
    # Negative test — this fact is not in the excerpt.
    return run_chain(sop_text, "What is the outdoor macro-cell EIRP limit?")


def p07():
    return run_chain(sla_text, "What is the guaranteed uptime percentage?")


def p08():
    return run_chain(sla_text, "What happens if uptime falls below the guarantee?")


def p09():
    # Negative test — this exact figure is not specified in the excerpt.
    return run_chain(sla_text, "What is the penalty if uptime falls below 95%?")


def p10():
    user = (
        f"Document:\n{sla_text}\n\n"
        'Return STRICT JSON: {"clause_number": str, "summary": str} for the exclusions clause.'
    )
    return call_model(SYSTEM_PROMPT, user)


def p11():
    return call_model(SYSTEM_PROMPT,
        'Return STRICT JSON: {"severity": str, "meaning": str, "example": str} '
        "for a Critical incident.")


def p12():
    return step1_extract(sop_text, "What should be checked before commissioning?")


def p13():
    fake_raw_finding = (
        "The document mentions somewhere that VSWR should be checked, "
        "roughly below 1.5:1, in the commissioning section, not 100% sure which page."
    )
    return step2_format(fake_raw_finding, "What VSWR reading is acceptable?")


def p14():
    return call_model(SYSTEM_PROMPT,
        'Return STRICT JSON: {"risk_level": str, "evidence": str, "action": str} '
        "for: usage down 30%, 2 tickets, renewal in 15 days.")


def p15():
    user = (
        f"Document:\n{sla_text}\n\n"
        "Summarise this contract as a table: Clause | Topic | Key Point."
    )
    return call_model(SYSTEM_PROMPT, user)


def p16():
    return run_chain(sop_text, "What should happen if VSWR reads above 1.5:1?")


def p17():
    # Deliberately vague — no schema given — to show JSON parsing can fail.
    raw = call_model(SYSTEM_PROMPT, "Give me some JSON about network incidents.")
    try:
        json.loads(raw)
        return f"Parsed OK (unexpected):\n{raw}"
    except json.JSONDecodeError as e:
        return f"json.loads() FAILED as expected: {e}\n\nRaw output:\n{raw}"


def p18():
    return call_model(SYSTEM_PROMPT,
        "Return as a markdown table: Ticket ID | Type | Amount, for 3 disputes you invent.")


def p19():
    return run_chain(sop_text, "What is the SOP's version number and effective date?")


def p20():
    return call_model(SYSTEM_PROMPT,
        'Return STRICT JSON: {"requirement": str, "one_sentence_response": str} '
        "for an RFP question about uptime guarantees.")


def p21():
    return run_chain(sla_text, "Who has audit rights and how often are reports due?")


def p22():
    # Run the same chain 3 times and print all 3 confidence fields for comparison.
    results = [run_chain(sop_text, "What is the maximum indoor EIRP for Band 78?") for _ in range(3)]
    return "\n\n---\n\n".join(results)


def p23():
    return call_model(SYSTEM_PROMPT,
        'Return STRICT JSON: {"open_incidents": [], "resolved_incidents": []} '
        "for 3 incidents you invent.")


def p24():
    # Stress test — completely outside the document.
    return run_chain(sla_text, "What is today's date?")


def p25():
    return call_model(SYSTEM_PROMPT,
        "In 2-3 sentences, which NCS Telco+ use case would benefit most from this exact "
        "2-step chain in production, and why?")


PROMPTS = {
    1: ("JSON: define a term (EIRP)", p01),
    2: ("JSON: classify a billing dispute", p02),
    3: ("Markdown table: 2 incidents", p03),
    4: ("Chain: EIRP question on the real SOP (positive test)", p04),
    5: ("Chain: antenna height question on the real SOP", p05),
    6: ("Chain: outdoor EIRP question (negative test — not covered)", p06),
    7: ("Chain: guaranteed uptime on the real SLA", p07),
    8: ("Chain: breach consequence on the real SLA", p08),
    9: ("Chain: below-95% penalty (negative test — not specified)", p09),
    10: ("JSON: exclusions clause extraction from SLA", p10),
    11: ("JSON: severity definition (no document needed)", p11),
    12: ("Step 1 only: raw extraction, before formatting", p12),
    13: ("Step 2 only: format a fabricated raw finding", p13),
    14: ("JSON: churn risk assessment", p14),
    15: ("Markdown table: full SLA summarised by clause", p15),
    16: ("Chain: VSWR question on the real SOP", p16),
    17: ("Error handling: vague JSON request that may fail to parse", p17),
    18: ("Markdown table: 3 invented billing disputes", p18),
    19: ("Chain: SOP metadata (version, effective date)", p19),
    20: ("JSON: RFP requirement + one-sentence response", p20),
    21: ("Chain: two-part question on the real SLA (audit rights)", p21),
    22: ("Consistency check: same chain question run 3 times", p22),
    23: ("JSON: nested lists (open/resolved incidents)", p23),
    24: ("Chain stress test: totally unrelated question", p24),
    25: ("Reflection: best production use case for this chain", p25),
}


def main():
    if len(sys.argv) < 2:
        print("Sheet 3 — 25 Prompts. Run any one with: python prompts.py <number>\n")
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
