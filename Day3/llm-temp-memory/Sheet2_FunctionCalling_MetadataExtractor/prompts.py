"""
Day 3 — Sheet 2: Function Calling & the Document Metadata Extractor
25 guided prompts. This is the official design-doc lab.

Usage:
    python prompts.py            -> lists all 25 prompts
    python prompts.py 1          -> runs prompt #1 (extract metadata from the real SOP)
"""
import sys
import json
import time
from call_model import call_model, client, MODEL, SYSTEM_PROMPT
from chain import sop_text, sla_text

# ---------------- Core tool schema (the design-doc lab) ----------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "extract_document_metadata",
            "description": "Extract structured metadata from a policy or SOP document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "e.g. SOP, SLA, Policy, Manual"},
                    "topic": {"type": "string"},
                    "key_entities": {"type": "array", "items": {"type": "string"}},
                    "effective_date": {"type": "string", "description": "YYYY-MM-DD if stated, else null"},
                },
                "required": ["document_type", "topic", "key_entities", "effective_date"],
            },
        },
    }
]

# Same schema, with an enum constraint on document_type (used in #11-12)
tools_enum = json.loads(json.dumps(tools))  # deep copy
tools_enum[0]["function"]["parameters"]["properties"]["document_type"]["enum"] = [
    "SOP", "SLA", "Policy", "Manual"
]

tool_dispute = [{
    "type": "function",
    "function": {
        "name": "classify_dispute",
        "description": "Classify a billing dispute message.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["Overcharge", "Roaming Error", "Plan Migration Error", "Other"]},
                "confidence": {"type": "string", "enum": ["High", "Medium", "Low"]},
                "needs_escalation": {"type": "boolean"},
            },
            "required": ["category", "confidence", "needs_escalation"],
        },
    },
}]

tool_incident = [{
    "type": "function",
    "function": {
        "name": "log_incident",
        "description": "Log a network incident from an alert description.",
        "parameters": {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                "network_element": {"type": "string"},
                "needs_dispatch": {"type": "boolean"},
            },
            "required": ["severity", "network_element", "needs_dispatch"],
        },
    },
}]

tool_handover = [{
    "type": "function",
    "function": {
        "name": "format_handover",
        "description": "Format incidents into a structured shift-handover report.",
        "parameters": {
            "type": "object",
            "properties": {
                "open_incidents": {"type": "array", "items": {"type": "string"}},
                "resolved_incidents": {"type": "array", "items": {"type": "string"}},
                "priority_action": {"type": "string"},
            },
            "required": ["open_incidents", "resolved_incidents", "priority_action"],
        },
    },
}]

tool_churn = [{
    "type": "function",
    "function": {
        "name": "assess_churn",
        "description": "Assess churn risk for a customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "recommended_action": {"type": "string"},
            },
            "required": ["risk_level", "evidence", "recommended_action"],
        },
    },
}]


def call_tool(user_prompt, tool_defs, tool_name, force=True):
    kwargs = {}
    if force:
        kwargs["tool_choice"] = {"type": "function", "function": {"name": tool_name}}
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        tools=tool_defs,
        **kwargs,
    )
    msg = response.choices[0].message
    if not msg.tool_calls:
        return f"(No tool called — model answered in plain text instead)\n{msg.content}"
    call = msg.tool_calls[0]
    return json.dumps(json.loads(call.function.arguments), indent=2)


def extract_metadata(document_text, tool_defs=tools):
    return call_tool(f"Extract metadata from this document:\n{document_text}", tool_defs, "extract_document_metadata")


# ---------------- 25 Prompts ----------------

def p01():
    return extract_metadata(sop_text)


def p02():
    return extract_metadata(sla_text)


def p03():
    result = json.loads(extract_metadata(sop_text))
    return f"type(key_entities) = {type(result['key_entities'])}\nvalue = {result['key_entities']}"


def p04():
    return extract_metadata("This is a very short internal memo with no date mentioned anywhere.")


def p05():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "What is 2 + 2?"},
        ],
        tools=tools,
        tool_choice="auto",
    )
    msg = response.choices[0].message
    if msg.tool_calls:
        return f"Tool was called (unexpected): {msg.tool_calls[0].function.arguments}"
    return f"No tool called (expected) — plain answer: {msg.content}"


def p06():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Return JSON: {{document_type, topic}}. Document:\n{sop_text}"},
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def p07():
    return "Schema defined as tool_dispute — see source. Run prompt #8 to call it."


def p08():
    return call_tool("charged twice for same recharge.", tool_dispute, "classify_dispute")


def p09():
    return "Schema defined as tool_incident — see source. Run prompt #10 to call it."


def p10():
    return call_tool("eNodeB-4471-Pune Cell Down, 0 throughput.", tool_incident, "log_incident")


def p11():
    return extract_metadata(sop_text, tool_defs=tools_enum)


def p12():
    return extract_metadata(sla_text, tool_defs=tools_enum)


def p13():
    combined_tools = tools + tool_dispute
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract metadata from this document:\n{sop_text}"},
        ],
        tools=combined_tools,
        tool_choice="auto",
    )
    msg = response.choices[0].message
    if msg.tool_calls:
        return f"Model chose tool: {msg.tool_calls[0].function.name}"
    return f"No tool called: {msg.content}"


def p14():
    return "Schema defined as tool_handover — see source. Run prompt #15 to call it."


def p15():
    incidents = "eNodeB-4471-Pune Cell Down (open); Core-PGW-04 Packet Loss (resolved)"
    return call_tool(f"Format a handover from: {incidents}", tool_handover, "format_handover")


def p16():
    # Remove "required" and test on very short text
    loose_tools = json.loads(json.dumps(tools))
    del loose_tools[0]["function"]["parameters"]["required"]
    return extract_metadata("Short memo, no clear topic or date.", tool_defs=loose_tools)


def p17():
    mixed = sop_text + "\n\n---\n\n" + sla_text
    return extract_metadata(mixed)


def p18():
    return "Schema defined as tool_churn — see source. Run prompt #19 to call it."


def p19():
    return call_tool(
        "usage down 30%, 2 tickets, renewal in 15 days", tool_churn, "assess_churn"
    )


def p20():
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": "Tell me about EIRP."}],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error (expected without the word 'JSON' in the prompt): {e}"


def p21():
    return "Design your own draft_rfp_section(requirement, response_text, confidence) schema here."


def p22():
    results = [extract_metadata(sop_text) for _ in range(3)]
    return "\n\n---\n\n".join(results)


def p23():
    r1 = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": f"Extract metadata from:\n{sop_text}"}],
        tools=tools, tool_choice={"type": "function", "function": {"name": "extract_document_metadata"}},
    )
    r2 = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": f"Return JSON: {{document_type, topic}}. Document:\n{sop_text}"}],
        response_format={"type": "json_object"},
    )
    return (f"Function calling: {r1.usage.total_tokens} total tokens\n"
            f"JSON mode: {r2.usage.total_tokens} total tokens")


def p24():
    sop_meta = extract_metadata(sop_text)
    sla_meta = extract_metadata(sla_text)
    return f"SOP:\n{sop_meta}\n\nSLA:\n{sla_meta}"


def p25():
    return call_model(SYSTEM_PROMPT,
        "In 2-3 sentences, name one NCS deliverable where a strict tool schema matters "
        "more than a loose JSON request, and why.")


PROMPTS = {
    1: ("Extract metadata: real SOP (positive test)", p01),
    2: ("Extract metadata: real SLA", p02),
    3: ("Field type check: key_entities is a real list", p03),
    4: ("Missing data: no date mentioned at all", p04),
    5: ("tool_choice='auto' on an unrelated question", p05),
    6: ("JSON mode alternative", p06),
    7: ("(Info) classify_dispute schema defined", p07),
    8: ("Call classify_dispute on a real dispute", p08),
    9: ("(Info) log_incident schema defined", p09),
    10: ("Call log_incident on a real alert", p10),
    11: ("Enum-constrained extraction: SOP", p11),
    12: ("Enum-constrained extraction: SLA", p12),
    13: ("Multiple tools available, auto-selection", p13),
    14: ("(Info) format_handover schema defined", p14),
    15: ("Call format_handover on 2 incidents", p15),
    16: ("No 'required' fields, short ambiguous text", p16),
    17: ("Mixed document: SOP + SLA pasted together", p17),
    18: ("(Info) assess_churn schema defined", p18),
    19: ("Call assess_churn on a real scenario", p19),
    20: ("JSON mode without the word 'JSON' in the prompt", p20),
    21: ("(Exercise) design draft_rfp_section yourself", p21),
    22: ("Consistency check: same extraction 3x", p22),
    23: ("Token cost: function calling vs JSON mode", p23),
    24: ("Full lab deliverable: both real documents", p24),
    25: ("Reflection: when strict schemas matter most", p25),
}


def main():
    if len(sys.argv) < 2:
        print("Sheet 2 — 25 Prompts. Run any one with: python prompts.py <number>\n")
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
