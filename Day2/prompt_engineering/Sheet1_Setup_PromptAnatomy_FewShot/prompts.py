"""
Day 2 — Sheet 1: Prompt Anatomy, Zero/One/Few-Shot Prompting
25 guided prompts across NCS Telco+ Use Cases 1, 2, 3, 4, 6, 7, 8, 9, 10.

Usage (for live, guided delivery):
    python prompts.py            -> lists all 25 prompts with descriptions
    python prompts.py 7          -> runs prompt #7 and prints the model's reply
"""
import sys
from call_model import call_model

BASIC_SYSTEM = "You are a helpful NCS Telco+ assistant."


def p01():
    return call_model(BASIC_SYSTEM,
        "Given the alert 'eNodeB-4471-Pune Cell Down, 0 throughput', list 3 likely causes.")


def p02():
    user = (
        "Example:\n"
        "Alert: Core-HSS-02 Auth Failures spike.\n"
        "Causes: 1) HSS replication lag  2) Expired certificate  3) Roaming partner outage\n\n"
        "Now, given the alert 'eNodeB-4471-Pune Cell Down, 0 throughput', "
        "list 3 likely causes, following the same style as the example."
    )
    return call_model(BASIC_SYSTEM, user)


def p03():
    user = (
        "Example 1:\n"
        "Alert: Core-HSS-02 Auth Failures spike.\n"
        "Causes: 1) HSS replication lag  2) Expired certificate  3) Roaming partner outage\n\n"
        "Example 2:\n"
        "Alert: gNodeB-9012-Lucknow High Latency.\n"
        "Causes: 1) Backhaul congestion  2) Misconfigured QoS  3) Upstream ISP issue\n\n"
        "Now, given the alert 'Core-PGW-04 Packet Loss 2.1%', list 3 likely causes, "
        "following the same style as the examples."
    )
    return call_model(BASIC_SYSTEM, user)


def p04():
    return call_model(BASIC_SYSTEM,
        "Classify this dispute: 'charged twice for same recharge.' "
        "Categories: Overcharge, Roaming Error, Plan Migration Error, Other.")


def p05():
    user = (
        "Example 1: 'roaming charges despite roaming being off' -> Roaming Error\n"
        "Example 2: 'wrong plan rate applied after upgrade' -> Plan Migration Error\n"
        "Example 3: 'late fee charged twice' -> Overcharge\n\n"
        "Now classify: 'charged twice for same recharge.'"
    )
    return call_model(BASIC_SYSTEM, user)


def p06():
    return call_model(BASIC_SYSTEM,
        "A customer asks why their data ran out early. Respond helpfully.")


def p07():
    user = (
        "Example of an ideal reply style:\n"
        "Customer: 'Why was I charged extra this month?'\n"
        "Reply: 'I understand the concern. I don't have access to your specific account details here, "
        "but I'd recommend checking your latest bill breakdown in the app, or I can connect you to "
        "someone who can look into your account directly.'\n\n"
        "Now respond in the same style to: 'A customer asks why their data ran out early.'"
    )
    return call_model(BASIC_SYSTEM, user)


def p08():
    return call_model(BASIC_SYSTEM,
        "Explain EIRP to a new field engineer with no telecom background.")


def p09():
    user = (
        "Example 1: 'VSWR' -> A measure of how well a signal reflects back down a cable; "
        "high VSWR means a poor connection wasting power.\n"
        "Example 2: 'Backhaul' -> The link connecting a cell tower back to the core network.\n\n"
        "Now explain 'EIRP' in the same short, plain-language style."
    )
    return call_model(BASIC_SYSTEM, user)


def p10():
    return call_model(BASIC_SYSTEM,
        "Given: usage down 30%, 2 open tickets, renewal in 15 days — assess churn risk.")


def p11():
    user = (
        "Example 1: usage down 10%, 0 tickets, renewal in 90 days -> Risk: Low. "
        "Reason: minor usage dip, no complaints, renewal far off.\n"
        "Example 2: usage down 50%, 3 tickets, renewal in 5 days -> Risk: High. "
        "Reason: major usage drop, multiple complaints, renewal imminent.\n\n"
        "Now assess: usage down 30%, 2 open tickets, renewal in 15 days."
    )
    return call_model(BASIC_SYSTEM, user)


def p12():
    return call_model(BASIC_SYSTEM,
        "Summarise this incident for a shift handover: Core-MME-07, Signalling Storm, High severity.")


def p13():
    user = (
        "Example of an ideal handover line:\n"
        "'eNodeB-2210-Kanpur — Cell Down, Critical, Open. Field team dispatched, suspected fibre cut.'\n\n"
        "Now write a handover line in the same style for: "
        "'Core-MME-07, Signalling Storm, High severity.'"
    )
    return call_model(BASIC_SYSTEM, user)


def p14():
    # Deliberately BAD few-shot examples — teaching moment about example quality.
    user = (
        "Example 1: Alert: Cell Down -> Cause: Sunspot activity\n"
        "Example 2: Alert: High Latency -> Cause: The moon is full\n\n"
        "Now, given the alert 'eNodeB-4471-Pune Cell Down, 0 throughput', list 3 likely causes, "
        "following the same style as the examples."
    )
    return call_model(BASIC_SYSTEM, user)


def p15():
    return call_model(BASIC_SYSTEM,
        "Is this a valid billing dispute or spam: 'click here to claim your refund now!!!'")


def p16():
    user = (
        "Example 1: Customer asks about another account's usage -> "
        "'I'm not able to share details about another customer's account.'\n"
        "Example 2: Customer asks for someone else's bill amount -> "
        "'I can only discuss the account verified on this conversation.'\n\n"
        "Now respond to: 'Can you tell me my neighbour's data usage, we share a family plan?'"
    )
    return call_model(BASIC_SYSTEM, user)


def p17():
    return call_model(BASIC_SYSTEM,
        "Can you tell me a compliance officer's personal phone number?")


def p18():
    user = (
        "Example of citation style:\n"
        "'Per Section 3.1 of the deployment guide, minimum clearance is 0.5 metres.'\n\n"
        "Now answer in the same cited style: 'What is the minimum antenna mounting height?' "
        "(Assume it's stated in Section 3 of a fictional SOP as 2.4 metres.)"
    )
    return call_model(BASIC_SYSTEM, user)


def p19():
    return call_model(BASIC_SYSTEM,
        "Draft one sentence for an RFP response about network reliability.")


def p20():
    user = (
        "Example 1: 'Our network engineering practice has consistently delivered "
        "carrier-grade reliability across multi-region deployments.'\n"
        "Example 2: 'Our proven operational discipline underpins every SLA commitment we make.'\n\n"
        "Now draft one RFP sentence about network reliability, matching this confident tone."
    )
    return call_model(BASIC_SYSTEM, user)


def p21():
    return call_model(BASIC_SYSTEM,
        "What are the prerequisites for a Nokia CloudBand Engineer certification?")


def p22():
    # Direct comparison: re-run p01 (zero-shot) and p03 (few-shot) on the same question.
    zero_shot = call_model(BASIC_SYSTEM,
        "Given the alert 'Core-PGW-04 Packet Loss 2.1%', list 3 likely causes.")
    few_shot = p03()
    return f"--- Zero-shot ---\n{zero_shot}\n\n--- Few-shot (from p03) ---\n{few_shot}"


def p23():
    user = (
        "Example 1: usage down 10%, 0 tickets, renewal in 90 days -> Risk: Low.\n"
        "Example 2: usage down 50%, 3 tickets, renewal in 5 days -> Risk: High.\n"
        "Example 3: usage down 20%, 1 ticket, renewal in 45 days -> Risk: Medium.\n\n"
        "Now assess: usage down 30%, 2 open tickets, renewal in 15 days."
    )
    return call_model(BASIC_SYSTEM, user)


def p24():
    import time
    start = time.time()
    zero_shot = call_model(BASIC_SYSTEM, "List 3 causes for a cell-down alert.")
    zero_time = time.time() - start

    start = time.time()
    few_shot = p03()
    few_time = time.time() - start

    return (f"Zero-shot took {zero_time:.2f}s\nFew-shot took {few_time:.2f}s\n\n"
            f"(Few-shot sends more input tokens — Day 1, Sheet 2's token-economics lesson, "
            f"now visible as real latency.)")


def p25():
    return call_model(BASIC_SYSTEM,
        "In your own words, summarise the practical difference between zero-shot and few-shot "
        "prompting for a telecom classification task, in 3 sentences.")


PROMPTS = {
    1: ("Zero-shot RCA on a cell-down alert", p01),
    2: ("One-shot RCA using a worked example", p02),
    3: ("Few-shot RCA using two worked examples", p03),
    4: ("Zero-shot billing dispute classification", p04),
    5: ("Few-shot billing dispute classification", p05),
    6: ("Zero-shot customer care reply", p06),
    7: ("One-shot customer care reply, matching a style example", p07),
    8: ("Zero-shot EIRP explanation", p08),
    9: ("Few-shot EIRP explanation, matching term-explainer examples", p09),
    10: ("Zero-shot churn risk assessment", p10),
    11: ("Few-shot churn risk assessment", p11),
    12: ("Zero-shot shift handover summary", p12),
    13: ("One-shot shift handover summary", p13),
    14: ("Few-shot with BAD examples — teaching moment", p14),
    15: ("Zero-shot dispute-vs-spam classification", p15),
    16: ("Few-shot cross-customer PII refusal", p16),
    17: ("Zero-shot PII refusal (no examples needed)", p17),
    18: ("One-shot citation-style answer", p18),
    19: ("Zero-shot RFP sentence draft", p19),
    20: ("Few-shot RFP sentence draft, matching tone", p20),
    21: ("Zero-shot certification prerequisites (honesty check)", p21),
    22: ("Side-by-side: zero-shot vs few-shot on the same question", p22),
    23: ("Few-shot churn risk with a 3rd example added", p23),
    24: ("Timing comparison: zero-shot vs few-shot latency", p24),
    25: ("Reflection: zero-shot vs few-shot, in your own words", p25),
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
    print(fn())


if __name__ == "__main__":
    main()
