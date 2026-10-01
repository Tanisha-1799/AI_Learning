# SSL Fix Analysis - Nyaya

## Reported Runtime Error

`/ask` returned HTTP 502 while app server was running.
Likely cause: OpenAI embedding call inside retrieval failed due to
TLS/certificate or network route/proxy constraints.

## Solution Applied

### 1) Added centralized module

- Added `ssl_network.py`

Centralizes:
- CA bundle handling (`OPENAI_CA_BUNDLE`, `SSL_CERT_FILE`)
- Proxy handling (`OPENAI_PROXY`, `HTTPS_PROXY`, auto Windows proxy detect)
- Base URL support (`OPENAI_BASE_URL`)
- Timeout/retry controls (`OPENAI_TIMEOUT_SEC`, `OPENAI_MAX_RETRIES`)
- OS trust-store support via `OPENAI_USE_SYSTEM_CERT_STORE`
- Debug diagnostics and troubleshooting guidance

### 2) build_vectorstore.py hardened

- Uses centralized SSL settings.
- Prints network config summary.
- Runs OpenAI preflight before embedding bulk upload.
- Prints detailed nested exception causes on failure.

### 3) app.py hardened

- Uses same centralized settings as build script.
- Applies timeout/retry/base-url consistently to OpenAI and embeddings.
- Keeps existing APIConnectionError -> 502 handling, now with stronger
  underlying network configuration.

### 4) Configuration and docs updated

- `requirements.txt` now includes `truststore`.
- `.env.example` extended with SSL/proxy/base-url/tuning variables.
- `.env` updated with defaults for timeout/retries/system-cert-store.
- README troubleshooting expanded.

## Files Updated

- `ssl_network.py` (new)
- `build_vectorstore.py`
- `app.py`
- `requirements.txt`
- `.env.example`
- `.env`
- `README.md`

## Next Validation Steps

1. `pip install -r requirements.txt`
2. Run `python build_vectorstore.py --strategy overlap`
3. Start API: `uvicorn app:app --reload --port 8000`
4. Retry the same `/ask` URL

If failure persists, capture and inspect printed `Network config summary`
and the full `Original error` cause chain for final proxy/CA adjustment.
