# Sheet 3 — FastAPI Exercises: Exact Commands

First, start the server (keep this terminal running):

```
uvicorn main:app --reload --port 8000
```

Then, in a **second** terminal, run these for the corresponding prompt numbers
from `prompts.py` / the practice sheet:

**#4 — basic test**
```
curl "http://localhost:8000/chat?q=hello"
```

**#5 — real customer-care question**
```
curl "http://localhost:8000/chat?q=Why+did+my+data+run+out+early"
```

**#6 — handover question**
```
curl "http://localhost:8000/chat?q=Summarise+this+incident+for+a+shift+handover:+Core-MME-07+Signalling+Storm"
```

**#10 — the /chat-sla endpoint**
```
curl "http://localhost:8000/chat-sla?q=What+is+the+guaranteed+uptime"
```

**#13 — empty query (error handling test)**
```
curl "http://localhost:8000/chat?q="
```

**#15 — interactive docs**
Open in a browser: http://localhost:8000/docs
Try the `/chat` endpoint directly from the Swagger UI.

**#16 — classify a billing dispute**
```
curl "http://localhost:8000/chat?q=Classify+this+dispute:+charged+twice+for+same+recharge"
```

**#19 — two clients at once (concurrency)**
Open two terminal windows and run the SAME command in both, at the same time:
```
curl "http://localhost:8000/chat?q=Explain+EIRP"
```
Watch whether both streams start immediately or one waits for the other.

**#20 — extend generate_stream with document grounding**
This one is a code exercise: edit `main.py` so `/chat-sla` reads `sla_text`
from Day 2 Sheet 3's `chain.py` and includes it in the prompt, instead of
just saying "in the context of a standard telecom SLA."

**#22 — add a temperature parameter**
Already implemented in `main.py` — try:
```
curl "http://localhost:8000/chat?q=Explain+EIRP&temperature=0.1"
curl "http://localhost:8000/chat?q=Explain+EIRP&temperature=0.9"
```
Compare the two responses.

**#23 — compare /chat-sync to streaming**
```
curl "http://localhost:8000/chat-sync?q=Explain+EIRP"
```
Compare the response shape (a single JSON object) and wait time to the
streaming `/chat` endpoint.
