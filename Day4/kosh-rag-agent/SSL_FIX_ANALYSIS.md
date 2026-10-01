# SSL Fix Analysis - kosh-rag-agent

## Issue Seen

`build_vectorstore.py` failed at embedding with OpenAI connection/TLS errors.
This is consistent with corporate SSL inspection and/or proxy routing gaps.

## What Was Changed

### 1) Added centralized network module

- Added `ssl_network.py`

It centralizes:
- CA bundle handling (`OPENAI_CA_BUNDLE`, `SSL_CERT_FILE`)
- Proxy handling (`OPENAI_PROXY`, `HTTPS_PROXY`, auto Windows proxy detect)
- Base URL support (`OPENAI_BASE_URL`)
- Retry/timeout controls (`OPENAI_MAX_RETRIES`, `OPENAI_TIMEOUT_SEC`)
- Optional Windows cert-store trust via `OPENAI_USE_SYSTEM_CERT_STORE`
- Optional local insecure mode (`ALLOW_INSECURE_SSL=true`)
- Richer error diagnostics with nested cause/context

### 2) build_vectorstore.py hardened

- Replaced per-file TLS logic with centralized module usage.
- Added network config summary print at startup.
- Added OpenAI preflight (`models.list`) to fail fast before embedding loop.
- Improved error output with full cause chain.

### 3) app.py aligned

- Replaced local TLS setup with centralized module.
- Uses same SSL/proxy/base URL/retry settings as build script.

### 4) dependency update

- Added `truststore` to `requirements.txt` for system certificate store support.

### 5) config/docs update

- Extended `.env.example` with all SSL/proxy/tuning variables.
- Updated README corporate TLS section.

## Files Updated

- `ssl_network.py` (new)
- `build_vectorstore.py`
- `app.py`
- `requirements.txt`
- `.env.example`
- `README.md`

## Run Checklist

1. `pip install -r requirements.txt`
2. Set env values (prefer secure path):
   - `OPENAI_CA_BUNDLE` or `OPENAI_USE_SYSTEM_CERT_STORE=true`
   - `OPENAI_PROXY` if needed
   - `OPENAI_BASE_URL` if needed
3. Run `python build_vectorstore.py`
4. Start app `uvicorn app:app --reload --port 8000`
5. Run `python agent.py`
