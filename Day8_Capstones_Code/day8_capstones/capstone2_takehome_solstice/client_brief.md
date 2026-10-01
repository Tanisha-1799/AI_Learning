# Discovery Call Notes — Solstice Insurance (Claims Support)

**Prepared by:** Business Analyst, NCS Telco+ Advisory
**Meeting date:** 2 September 2026
**Attendees:** Head of Claims Operations, Head of Compliance, IT Lead (Solstice Insurance); Solutions Architect, BA (NCS Telco+)

## Background

Solstice Insurance runs a claims support desk handling roughly 1,800
customer and agent queries a week about claims processing, denial
reasons, and policy coverage. The desk currently relies on a mix of a
claims processing SOP, an internal FAQ, a spreadsheet log of denial
codes and reasons, and a JSON export of policy coverage tiers from
their underwriting system.

## Pain Points Raised in the Meeting

- Claims agents say denial-reason lookups are the single biggest time
  sink — the same handful of denial codes come up constantly, but
  agents still search a shared spreadsheet by hand.
- Compliance is unusually cautious here: Solstice operates under
  insurance-sector regulation, and Compliance stated plainly that an
  incorrect or unsupported answer about claims eligibility "is a
  regulatory incident, not just a bad customer experience."
- The denial log spreadsheet includes a free-text "customer_note"
  column — verbatim notes support agents type in from customer calls,
  UNREVIEWED before being logged. Compliance asked directly whether an
  AI system reading that column could be manipulated by something a
  customer said on a call.
- Several FAQ entries and denial reasons reference multiple distinct,
  unrelated scenarios in a single answer (e.g., "claims can be denied
  for pre-existing condition exclusions, late filing, OR policy lapse
  — each governed by a different clause") — agents want the SAME
  broad question to surface ALL relevant distinct reasons, not just the
  single closest match.
- The FAQ contains a named Claims Support Lead's direct contact details
  for escalations.
- Policy coverage tiers change relatively rarely (roughly twice a
  year), unlike Meridian's monthly HR policy cycle — but a mistaken
  answer about a customer's own coverage tier carries higher individual
  financial consequence than a mistaken HR answer typically would.

## What They're Asking For

An internal assistant for claims support agents (not directly
customer-facing, for now) covering the SOP, FAQ, denial log, and
coverage tiers, with the explicit expectation that Compliance will
review the system's answers on a sample basis before any customer-
facing rollout is considered. They were explicit that trustworthiness
and defensibility of every answer matters more here than speed of
rollout.

## Constraints Signalled in the Meeting

Compliance wants documented evidence of how PII and unreviewed
free-text customer input are handled before they will sign off on even
the internal pilot. IT Lead noted budget is available for a more
thorough build than a quick internal tool, given the regulatory
sensitivity.
