# SSL Fix Analysis - Trust-Compliance-in-LLM-Apps

## Problem Observed

`build_vectorstore.py` failed at embedding stage with SSL/network errors.
The original stack showed certificate verification failures in corporate
network conditions. After introducing initial TLS handling, errors persisted
as generic `Connection error`, indicating network path configuration may also
be required (proxy/base URL/timeout), not just certificate trust.

## Root Cause Areas

1. TLS trust path mismatch under corporate SSL inspection.
2. Tokenizer/encoding fetch path can trigger external HTTPS calls.
3. No centralized network configuration meant inconsistent behavior between
   modules.
4. Missing proxy/gateway controls for environments that require them.

## Solution Implemented

### 1) Centralized module added

- Added: `ssl_network.py`

This module now owns all SSL/network logic:
- CA bundle loading (`OPENAI_CA_BUNDLE` / `SSL_CERT_FILE`)
- Optional local bypass (`ALLOW_INSECURE_SSL`)
- Proxy support (`OPENAI_PROXY`, `HTTPS_PROXY`)
- Base URL support (`OPENAI_BASE_URL`)
- Timeout/retry controls (`OPENAI_TIMEOUT_SEC`, `OPENAI_MAX_RETRIES`)
- Reusable diagnostics and troubleshooting guidance

### 2) build_vectorstore.py updated

- Replaced local TLS helper with centralized `ssl_network.py`.
- Added network configuration summary print before embedding.
- Added OpenAI preflight call (`models.list`) before bulk embedding to
  fail fast with actionable guidance.
- Passed timeout/retry and base URL into OpenAI + embeddings clients.
- Kept `check_embedding_ctx_length=False` to avoid tiktoken fetch path in
  restricted networks.

### 3) app.py updated

- Replaced local TLS helper with centralized `ssl_network.py`.
- Uses same settings as build phase (single source of truth).
- Applies timeout/retry/base URL to OpenAI and embeddings clients.
- Keeps existing graceful error handling for API connection/status failures.

### 4) loaders.py updated earlier

- Replaced deprecated `fitz` import with `pymupdf as fitz`.

### 5) README updated

- Added proxy/base-url/timeout/retry env variable guidance.
- Added explicit note describing `ssl_network.py` as the central module.

### 6) Second-phase hardening (after persistent "Connection error")

- Added Windows proxy auto-detection in `ssl_network.py` from Internet Settings
  when proxy env vars are absent.
- Added support for additional proxy env names (`HTTP_PROXY`, `ALL_PROXY`, etc.)
  and proxy URL normalization.
- Added deeper exception rendering (`describe_exception`) so preflight failures
  include nested causes/contexts instead of only generic "Connection error".
- Updated `build_vectorstore.py` to print the richer exception detail.
- Updated `.env` comments to clarify Windows auto-proxy behavior.

### 7) Third-phase hardening (after explicit CERTIFICATE_VERIFY_FAILED)

- Added `OPENAI_USE_SYSTEM_CERT_STORE` support in `ssl_network.py`.
- When no CA bundle is provided and insecure mode is off, the code now tries
  to use OS trust roots via `truststore.SSLContext(...)`.
- Added `truststore` to `requirements.txt`.
- Added `.env` default `OPENAI_USE_SYSTEM_CERT_STORE="true"`.
- Updated README guidance for system certificate store fallback.

## Files Updated

- `ssl_network.py` (new)
- `build_vectorstore.py`
- `app.py`
- `README.md`
- `loaders.py` (deprecation cleanup)

Second-phase updates:
- `ssl_network.py` (proxy auto-detection + detailed errors)
- `build_vectorstore.py` (detailed error reporting)
- `.env` (auto-proxy note)

Third-phase updates:
- `ssl_network.py` (OS certificate store support)
- `requirements.txt` (`truststore`)
- `.env` (`OPENAI_USE_SYSTEM_CERT_STORE`)
- `README.md` (new troubleshooting row)

## Environment Variables to Set

Preferred secure path:
- `OPENAI_API_KEY`
- `OPENAI_CA_BUNDLE` (corporate root CA PEM)
- `OPENAI_PROXY` (if required by network)
- `OPENAI_BASE_URL` (if using internal gateway)
- `OPENAI_TIMEOUT_SEC` (e.g., 90)
- `OPENAI_MAX_RETRIES` (e.g., 3)

Fallback local test path (unsafe):
- `ALLOW_INSECURE_SSL=true`

## Validation Steps

1. Set env vars in `.env`.
2. Run `python build_vectorstore.py`.
3. Confirm network summary is printed with expected values.
4. Start app: `uvicorn app:app --reload --port 8000`.
5. Run `python agent.py`.

## If It Still Fails

Use this triage order:
1. Verify `OPENAI_CA_BUNDLE` path exists and is readable.
2. Confirm whether your org requires explicit proxy and set `OPENAI_PROXY`.
3. If using enterprise OpenAI gateway, set `OPENAI_BASE_URL`.
4. Raise timeout/retries (`OPENAI_TIMEOUT_SEC=120`, `OPENAI_MAX_RETRIES=5`).
5. Temporary local-only check with `ALLOW_INSECURE_SSL=true` to isolate
   certificate vs route/proxy issues.

## Day6 Parity Check

Confirmed: Day6 projects used the same first-layer SSL hardening pattern:

- CA bundle wiring via `OPENAI_CA_BUNDLE` / `SSL_CERT_FILE`
- `ALLOW_INSECURE_SSL` fallback for local testing
- shared `http_client` passed to OpenAI and embeddings clients
- `check_embedding_ctx_length=False` to avoid tokenizer download path issues

Examples verified:

- `Day6/rag-advance-part2/build_vectorstore.py`
- `Day6/rag-advance-part2/app.py`
- `Day6/rag-advance-part2/query_transform.py`
- `Day6/Prastav/build_vectorstore.py`
- `Day6/Prastav/app.py`
- `Day6/Prastav/query_transform.py`

Difference in Day7 now:

Day7 includes additional second-layer network controls not present in Day6:

- proxy auto-detection and normalization
- explicit proxy/base-url settings
- timeout/retry tuning variables
- richer nested connection error diagnostics

Reason for this extension: the current Day7 failure progressed from
certificate verification errors to generic route-level `Connection error`,
which usually requires proxy/gateway routing controls in addition to CA trust.
