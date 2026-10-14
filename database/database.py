"""
SQLite layer for StudyBuddy AI.

Tables
------
documents    — file metadata (id, filename, file_type, upload_time, file_size, extracted_text)
study_pack   — AI-generated content per document (FK → documents ON DELETE CASCADE)
history      — access tracking per document (opened_count, last_opened)
settings     — arbitrary key-value store

Schema migrations are handled automatically by init_db().
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "studybuddy.db"

# ── Connection ────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ── Schema creation ───────────────────────────────────────────────────────────

def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id             TEXT PRIMARY KEY,
            filename       TEXT NOT NULL,
            file_type      TEXT NOT NULL DEFAULT 'unknown',
            upload_time    TEXT NOT NULL,
            file_size      INTEGER DEFAULT 0,
            extracted_text TEXT
        );

        CREATE TABLE IF NOT EXISTS study_pack (
            document_id      TEXT PRIMARY KEY,
            summary_json     TEXT,
            explanation_json TEXT,
            quiz_json        TEXT,
            flashcards_json  TEXT,
            generated_time   TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS history (
            document_id  TEXT PRIMARY KEY,
            opened_count INTEGER DEFAULT 0,
            last_opened  TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_documents_upload_time ON documents(upload_time DESC);
        CREATE INDEX IF NOT EXISTS idx_history_last_opened   ON history(last_opened DESC);
    """)


# ── Legacy → new schema migration ─────────────────────────────────────────────

def _old_schema_detected(conn: sqlite3.Connection) -> bool:
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if "study_pack" in tables:
        return False
    if "documents" not in tables:
        return False
    cols = {r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
    return "summary" in cols or "explanation" in cols


def _coerce_summary(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return {"short_summary": raw, "bullet_points": [], "key_takeaways": []}
    return {"short_summary": "", "bullet_points": [], "key_takeaways": []}


def _coerce_explanation(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return {
            "simple_explanation": raw,
            "important_concepts": [],
            "real_life_examples": [],
            "exam_tips": [],
        }
    return {
        "simple_explanation": "",
        "important_concepts": [],
        "real_life_examples": [],
        "exam_tips": [],
    }


def _migrate_legacy(conn: sqlite3.Connection) -> None:
    """Move data from old single-table schema into new multi-table schema."""
    rows = conn.execute("""
        SELECT id, filename,
               COALESCE(upload_date, created_at, datetime('now')) AS upload_time,
               COALESCE(file_size, 0) AS file_size,
               extracted_text, summary, explanation, quiz, flashcards
        FROM documents
    """).fetchall()

    conn.execute("ALTER TABLE documents RENAME TO _legacy_documents")
    _create_schema(conn)

    for r in rows:
        r = dict(r)
        doc_id    = r["id"]
        file_type = r["filename"].rsplit(".", 1)[-1].lower() if "." in r["filename"] else "unknown"

        conn.execute("""
            INSERT OR IGNORE INTO documents
                (id, filename, file_type, upload_time, file_size, extracted_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doc_id, r["filename"], file_type, r["upload_time"], r["file_size"], r["extracted_text"]))

        try:
            quiz_data = json.loads(r["quiz"]) if r.get("quiz") else []
        except Exception:
            quiz_data = []
        try:
            fc_data = json.loads(r["flashcards"]) if r.get("flashcards") else []
        except Exception:
            fc_data = []

        conn.execute("""
            INSERT OR IGNORE INTO study_pack
                (document_id, summary_json, explanation_json, quiz_json, flashcards_json, generated_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            json.dumps(_coerce_summary(r.get("summary")),     ensure_ascii=False),
            json.dumps(_coerce_explanation(r.get("explanation")), ensure_ascii=False),
            json.dumps(quiz_data, ensure_ascii=False),
            json.dumps(fc_data,   ensure_ascii=False),
            r["upload_time"],
        ))

        conn.execute("""
            INSERT OR IGNORE INTO history (document_id, opened_count, last_opened)
            VALUES (?, 0, NULL)
        """, (doc_id,))

    conn.execute("DROP TABLE _legacy_documents")


# ── Public initialiser ────────────────────────────────────────────────────────

def init_db() -> None:
    conn = get_connection()
    try:
        if _old_schema_detected(conn):
            _migrate_legacy(conn)
        else:
            _create_schema(conn)
        conn.commit()
    finally:
        conn.close()


# ── Writes ────────────────────────────────────────────────────────────────────

def save_document(
    filename: str,
    file_size: int,
    extracted_text: str,
    summary,        # dict (new) or plain str (legacy fallback)
    explanation,    # dict (new) or plain str (legacy fallback)
    quiz: list,
    flashcards: list,
) -> str:
    doc_id    = str(uuid.uuid4())
    now       = datetime.now().isoformat()
    file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO documents (id, filename, file_type, upload_time, file_size, extracted_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doc_id, filename, file_type, now, file_size, extracted_text))

        conn.execute("""
            INSERT INTO study_pack
                (document_id, summary_json, explanation_json, quiz_json, flashcards_json, generated_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            json.dumps(_coerce_summary(summary),       ensure_ascii=False),
            json.dumps(_coerce_explanation(explanation), ensure_ascii=False),
            json.dumps(quiz       if isinstance(quiz, list)       else [], ensure_ascii=False),
            json.dumps(flashcards if isinstance(flashcards, list) else [], ensure_ascii=False),
            now,
        ))

        conn.execute("""
            INSERT OR IGNORE INTO history (document_id, opened_count, last_opened)
            VALUES (?, 0, NULL)
        """, (doc_id,))

        conn.commit()
    finally:
        conn.close()
    return doc_id


def update_history_opened(doc_id: str) -> None:
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO history (document_id, opened_count, last_opened) VALUES (?, 1, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                opened_count = opened_count + 1,
                last_opened  = excluded.last_opened
        """, (doc_id, now))
        conn.commit()
    finally:
        conn.close()


def delete_document(doc_id: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
    finally:
        conn.close()


def set_setting(key: str, value: str) -> None:
    conn = get_connection()
    try:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
    finally:
        conn.close()


# ── Reads ─────────────────────────────────────────────────────────────────────

def get_document(doc_id: str) -> dict | None:
    conn = get_connection()
    try:
        doc_row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not doc_row:
            return None

        doc = dict(doc_row)

        pack = conn.execute(
            "SELECT * FROM study_pack WHERE document_id = ?", (doc_id,)
        ).fetchone()
        if pack:
            p = dict(pack)
            doc["summary"]        = json.loads(p["summary_json"])     if p["summary_json"]     else {}
            doc["explanation"]    = json.loads(p["explanation_json"]) if p["explanation_json"] else {}
            doc["quiz"]           = json.loads(p["quiz_json"])        if p["quiz_json"]        else []
            doc["flashcards"]     = json.loads(p["flashcards_json"])  if p["flashcards_json"]  else []
            doc["generated_time"] = p["generated_time"]
        else:
            doc["summary"] = {}
            doc["explanation"] = {}
            doc["quiz"] = []
            doc["flashcards"] = []
            doc["generated_time"] = None

        hist = conn.execute(
            "SELECT opened_count, last_opened FROM history WHERE document_id = ?", (doc_id,)
        ).fetchone()
        doc["opened_count"] = hist["opened_count"] if hist else 0
        doc["last_opened"]  = hist["last_opened"]  if hist else None

        # Backward-compat aliases
        doc["created_at"]  = doc["upload_time"]
        doc["upload_date"] = doc["upload_time"]

        return doc
    finally:
        conn.close()


def get_all_documents() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT d.id, d.filename, d.file_type, d.upload_time, d.file_size,
                   COALESCE(h.opened_count, 0) AS opened_count,
                   h.last_opened
            FROM documents d
            LEFT JOIN history h ON h.document_id = d.id
            ORDER BY d.upload_time DESC
        """).fetchall()
    finally:
        conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["created_at"]  = d["upload_time"]
        d["upload_date"] = d["upload_time"]
        result.append(d)
    return result


def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def get_stats() -> dict:
    conn = get_connection()
    try:
        total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

        quiz_count = fc_count = summary_count = 0
        rows = conn.execute(
            "SELECT quiz_json, flashcards_json, summary_json FROM study_pack"
        ).fetchall()
    finally:
        conn.close()

    for r in rows:
        try:
            if r["quiz_json"]:
                quiz_count += len(json.loads(r["quiz_json"]))
        except Exception:
            pass
        try:
            if r["flashcards_json"]:
                fc_count += len(json.loads(r["flashcards_json"]))
        except Exception:
            pass
        if r["summary_json"]:
            summary_count += 1

    return {
        "documents":  total_docs,
        "quizzes":    quiz_count,
        "flashcards": fc_count,
        "summaries":  summary_count,
    }

def save_research_analysis(doc_id: str, analysis: dict) -> None:
    set_setting(
        f"research_analysis:{doc_id}",
        json.dumps(analysis, ensure_ascii=False),
    )


def get_research_analysis(doc_id: str) -> dict | None:
    raw = get_setting(f"research_analysis:{doc_id}")

    if not raw:
        return None

    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def save_visual_analysis(filename: str, analysis_type: str, analysis: str) -> str:
    """Save a visual analysis in the existing settings table."""
    visual_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    record = {
        "id": visual_id,
        "filename": filename,
        "analysis_type": analysis_type,
        "analysis": analysis,
        "created_at": now,
    }

    set_setting(
        f"visual_analysis:{visual_id}",
        json.dumps(record, ensure_ascii=False),
    )

    return visual_id


def get_all_visual_analyses() -> list[dict]:
    """Retrieve saved visual analyses, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT key, value FROM settings "
            "WHERE key LIKE 'visual_analysis:%'"
        ).fetchall()
    finally:
        conn.close()

    results = []
    for row in rows:
        try:
            record = json.loads(row["value"])
            if isinstance(record, dict):
                results.append(record)
        except (json.JSONDecodeError, TypeError):
            continue

    return sorted(
        results,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )


def delete_visual_analysis(visual_id: str) -> None:
    """Delete one saved visual analysis."""
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM settings WHERE key = ?",
            (f"visual_analysis:{visual_id}",),
        )
        conn.commit()
    finally:
        conn.close()
