# SSL/TLS Error Analysis & Recovery Runbook (Saathi)

This runbook captures the exact failures and fixes we used for this project so the same issue can be resolved quickly in future.

## Scope

Applies to:
- `build_vectorstore.py`
- `app.py` (FastAPI backend)
- `agent.py` (client that calls `http://localhost:8000/ask`)

## Symptoms We Observed

### A) Build step fails with SSL certificate verification

Typical traceback includes:
- `httpcore.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] ... unable to get local issuer certificate`
- `httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] ...`
- `openai.APIConnectionError: Connection error.`

Where it appears:
- During embedding calls in `build_vectorstore.py`

### B) Agent gets HTTP 500 from local API

Typical error in `agent.py`:
- `requests.exceptions.HTTPError: 500 Server Error ... /ask?q=...`

Root behavior:
- `agent.py` can reach localhost, but `app.py` fails internally when calling OpenAI (same TLS/cert problem), so `/ask` returns server error.

## Root Cause

Corporate TLS interception / SSL inspection (or missing local trust chain) causes Python's TLS verification to fail when connecting to OpenAI endpoints.

This is a trust-store/certificate problem, not a vector store/chunking/retrieval logic bug.

## What We Patched in Code

### 1) `build_vectorstore.py`
- Added `create_openai_client()` with env-based TLS control:
  - `OPENAI_CA_BUNDLE` or `SSL_CERT_FILE` for trusted CA file
  - `ALLOW_INSECURE_SSL=true` for local-only bypass (unsafe)
- Added clear error output for connection/TLS failures.

### 2) `app.py`
- Added same TLS control logic for OpenAI client creation.
- Added explicit API exception handling in `/ask`:
  - returns `502` with actionable detail for TLS connection failures
  - returns upstream status for OpenAI API status errors

### 3) `agent.py`
- Added HTTP error handler that prints backend status and detail payload instead of only stacktrace.

## Decision Tree (Use This First)

1. If `build_vectorstore.py` shows `CERTIFICATE_VERIFY_FAILED`:
- Confirm this is TLS trust issue.
- Try secure CA-bundle fix first.
- Use insecure bypass only for temporary local testing.

2. If `agent.py` shows `500` from `/ask`:
- Check `app.py` terminal logs/details.
- Ensure TLS env vars are set in the **uvicorn terminal**, not only in the `agent.py` terminal.

3. If bypass works but secure mode fails:
- Network path is OK.
- Remaining issue is trust chain/proxy/CA configuration.

## Recommended Fix Order

### Step 1: Install dependencies

```powershell
pip install -r .\requirements.txt
```

Notes:
- PATH warnings for scripts like `setuptools-scm.exe` are usually harmless for this project runtime.

### Step 2: Validate direct TLS quickly

```powershell
python -c "import httpx; print(httpx.get('https://api.openai.com/v1/models', timeout=20).status_code)"
```

Interpretation:
- `401/403/...` = TLS worked, request reached server.
- SSL certificate verify error = trust chain still broken.

### Step 3 (Preferred): Configure trusted corporate CA

```powershell
$env:OPENAI_CA_BUNDLE = "C:\path\to\corp-root-ca.pem"
# optional compatibility vars
$env:SSL_CERT_FILE = "C:\path\to\corp-root-ca.pem"
$env:REQUESTS_CA_BUNDLE = "C:\path\to\corp-root-ca.pem"
$env:CURL_CA_BUNDLE = "C:\path\to\corp-root-ca.pem"
```

Then rerun build/backend.

### Step 4 (Temporary): Unsafe bypass for local testing only

```powershell
$env:ALLOW_INSECURE_SSL = "true"
```

Use only in controlled dev/testing. Do not use in production.

## Correct Run Sequence

### Rebuild vector store

```powershell
$env:ALLOW_INSECURE_SSL = "true"   # or use OPENAI_CA_BUNDLE preferred
python .\build_vectorstore.py
```

Expected: all policy files processed, final done summary.

### Start backend (critical: set env in this same terminal)

```powershell
$env:ALLOW_INSECURE_SSL = "true"   # or OPENAI_CA_BUNDLE preferred
python -m uvicorn app:app --reload --port 8000
```

### Run agent in second terminal

```powershell
python .\agent.py
```

## Common Pitfall

Setting `ALLOW_INSECURE_SSL` only in the `agent.py` terminal does **not** fix backend OpenAI failures. OpenAI calls happen inside `app.py`, so env vars must be present in the uvicorn process environment.

## Security Notes

- Best practice: use `OPENAI_CA_BUNDLE` with your corporate trusted CA.
- Avoid permanently running with `ALLOW_INSECURE_SSL=true`.
- Never disable verification in production.

## Quick Reuse Commands (Copy/Paste)

```powershell
# Terminal 1 (backend)
$env:ALLOW_INSECURE_SSL = "true"
python -m uvicorn app:app --reload --port 8000
```

```powershell
# Terminal 2 (client)
python .\agent.py
```

```powershell
# Secure preferred mode (replace with real CA path)
$env:OPENAI_CA_BUNDLE = "C:\path\to\corp-root-ca.pem"
python -m uvicorn app:app --reload --port 8000
```

## If Error Reappears

When asking for help, reference this file and share:
- exact command run
- full error snippet
- whether env vars were set in backend terminal
- whether bypass mode works

This is enough to distinguish TLS trust issues from API key/model/rate-limit issues quickly.
