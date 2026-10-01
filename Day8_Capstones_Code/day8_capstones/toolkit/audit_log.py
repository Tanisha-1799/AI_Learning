"""
toolkit/audit_log.py

Structured, queryable audit logging via SQLite. One row per request.
"""
import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = "./audit_log.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    question_redacted TEXT NOT NULL,
    retrieved_sources TEXT,
    retrieved_scores TEXT,
    confidence_level TEXT,
    refused INTEGER NOT NULL,
    injection_flagged INTEGER NOT NULL,
    injection_details TEXT,
    output_validation_passed INTEGER,
    output_validation_details TEXT,
    answer TEXT,
    cited_sources TEXT,
    latency_sec REAL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    model TEXT
);
"""


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    return conn


def log_request(
    question_redacted, retrieved_sources, retrieved_scores, confidence_level,
    refused, injection_flagged, injection_details, output_validation_passed,
    output_validation_details, answer, cited_sources, latency_sec,
    prompt_tokens, completion_tokens, model,
):
    conn = _connect()
    conn.execute(
        """INSERT INTO audit_log (
            timestamp, question_redacted, retrieved_sources, retrieved_scores,
            confidence_level, refused, injection_flagged, injection_details,
            output_validation_passed, output_validation_details,
            answer, cited_sources, latency_sec,
            prompt_tokens, completion_tokens, model
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(), question_redacted,
            json.dumps(retrieved_sources), json.dumps(retrieved_scores),
            confidence_level, int(refused), int(injection_flagged), injection_details,
            None if output_validation_passed is None else int(output_validation_passed),
            output_validation_details, answer, json.dumps(cited_sources), latency_sec,
            prompt_tokens, completion_tokens, model,
        ),
    )
    conn.commit()
    conn.close()
