# Kosh - NCS Telco+ Finance Knowledge Assistant

A Day 4 build-it-yourself RAG capstone using Finance policy documents.

## Architecture

1. build_vectorstore.py
- Reads policies in policies/*.txt
- Chunks and embeds text
- Stores vectors and metadata in ChromaDB collection: finance_docs

2. app.py
- FastAPI backend endpoint: /ask
- Embeds question, retrieves top chunks, asks LLM, returns grounded answer

3. agent.py
- Sends 5 hardcoded finance questions
- Prints retrieved chunk metadata and final answer

4. inspect_vectorstore.py (optional)
- Shows ChromaDB collection data
- Peeks directly into chroma.sqlite3 tables

## Setup

1. Create environment and install dependencies

Windows PowerShell:
- python -m venv venv
- .\venv\Scripts\Activate.ps1
- pip install -r requirements.txt

2. Create .env from .env.example and set your key

- OPENAI_API_KEY="your-key"

3. Build vector store

- python build_vectorstore.py

4. Start backend (Terminal 1)

- python -m uvicorn app:app --reload --port 8000

5. Run agent (Terminal 2)

- python agent.py

## Corporate SSL/TLS note

If you are on a corporate network with TLS inspection:
- Preferred: set OPENAI_CA_BUNDLE to your trusted CA PEM file.
- If your corporate root CA is installed in Windows trust store, keep
	OPENAI_USE_SYSTEM_CERT_STORE=true.
- If a proxy or enterprise gateway is required, set OPENAI_PROXY and/or
	OPENAI_BASE_URL.
- Temporary local workaround: set ALLOW_INSECURE_SSL=true.

Example PowerShell:
- $env:OPENAI_CA_BUNDLE = "C:\path\corp-root-ca.pem"
- $env:OPENAI_PROXY = "http://proxy-host:port"
- $env:OPENAI_BASE_URL = "https://your-gateway.example/v1"
- $env:OPENAI_TIMEOUT_SEC = "120"
- $env:OPENAI_MAX_RETRIES = "5"
- OR $env:ALLOW_INSECURE_SSL = "true"

This project now uses a centralized network module: `ssl_network.py`.
Both `build_vectorstore.py` and `app.py` read the same SSL/proxy settings.

## Finance policies in this project

- 01_expense_approval_policy.txt
- 02_procurement_policy.txt
- 03_invoice_processing_policy.txt
- 04_petty_cash_policy.txt
- 05_vendor_payment_terms_policy.txt
