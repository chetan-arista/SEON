"""SQLite persistence for local SEON accounts, sessions, and workspace data."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("SEON_DATA_DIR", Path(__file__).resolve().parent / "data"))
DB_PATH = DATA_DIR / "seon.sqlite3"


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def initialize() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
          display_name TEXT NOT NULL DEFAULT '', password_hash TEXT,
          role TEXT NOT NULL CHECK(role IN ('admin','company','client')),
          google_sub TEXT UNIQUE, disabled INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          expires_at TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY, kind TEXT NOT NULL, url TEXT NOT NULL,
          created_at TEXT NOT NULL, result_json TEXT NOT NULL,
          owner_id TEXT NOT NULL DEFAULT '' REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS findings (
          id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
          status TEXT NOT NULL CHECK(status IN ('Needs approval','Approved','Dismissed')),
          finding_json TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS blueprints (
          id TEXT PRIMARY KEY, created_at TEXT NOT NULL, brief_json TEXT NOT NULL,
          result_json TEXT NOT NULL, owner_id TEXT NOT NULL DEFAULT '' REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(run_id);
        CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at);
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        """)
        # Existing local MVP databases predate account ownership. Keep their
        # rows available to company/admin accounts without exposing to clients.
        for table in ("runs", "blueprints"):
            columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
            if "owner_id" not in columns:
                db.execute(f"ALTER TABLE {table} ADD COLUMN owner_id TEXT NOT NULL DEFAULT ''")
        db.execute("CREATE INDEX IF NOT EXISTS idx_runs_owner ON runs(owner_id, created_at)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_blueprints_owner ON blueprints(owner_id, created_at)")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_user(email: str, display_name: str, role: str, password_hash: str | None = None,
                google_sub: str | None = None) -> dict:
    user_id = str(uuid.uuid4())
    created = now()
    with connect() as db:
        db.execute("INSERT INTO users(id,email,display_name,password_hash,role,google_sub,created_at) VALUES(?,?,?,?,?,?,?)",
                   (user_id, email.strip().lower(), display_name.strip()[:160], password_hash, role, google_sub, created))
    return {"id": user_id, "email": email.strip().lower(), "display_name": display_name.strip()[:160], "role": role, "created_at": created}


def find_user_by_email(email: str) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE email=? COLLATE NOCASE", (email.strip(),)).fetchone()
    return dict(row) if row else None


def find_user_by_google_sub(subject: str) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE google_sub=?", (subject,)).fetchone()
    return dict(row) if row else None


def get_user(user_id: str) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def link_google_sub(user_id: str, subject: str) -> None:
    with connect() as db:
        db.execute("UPDATE users SET google_sub=? WHERE id=?", (subject, user_id))


def set_password(user_id: str, password_hash: str) -> None:
    with connect() as db:
        db.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))


def create_session(token_hash: str, user_id: str, expires_at: str) -> None:
    with connect() as db:
        db.execute("INSERT INTO sessions(token_hash,user_id,expires_at,created_at) VALUES(?,?,?,?)",
                   (token_hash, user_id, expires_at, now()))


def user_for_session(token_hash: str) -> dict | None:
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE expires_at < ?", (now(),))
        row = db.execute("SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.token_hash=? AND sessions.expires_at>=? AND users.disabled=0",
                         (token_hash, now())).fetchone()
    return dict(row) if row else None


def delete_session(token_hash: str) -> None:
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))


def list_users() -> list[dict]:
    with connect() as db:
        rows = db.execute("SELECT id,email,display_name,role,disabled,created_at,CASE WHEN google_sub IS NULL THEN 0 ELSE 1 END AS google_connected FROM users ORDER BY created_at").fetchall()
    return [dict(row) for row in rows]


def set_user_role(user_id: str, role: str) -> bool:
    with connect() as db:
        user = db.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return False
        if user["role"] == "admin" and role != "admin":
            admins = db.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND disabled=0").fetchone()[0]
            if admins <= 1:
                raise ValueError("The last active administrator cannot be demoted.")
        db.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    return True


def set_user_disabled(user_id: str, disabled: bool) -> bool:
    with connect() as db:
        user = db.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return False
        if user["role"] == "admin" and disabled:
            admins = db.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND disabled=0").fetchone()[0]
            if admins <= 1:
                raise ValueError("The last active administrator cannot be disabled.")
        db.execute("UPDATE users SET disabled=? WHERE id=?", (1 if disabled else 0, user_id))
        if disabled:
            db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    return True


def save_run(owner_id: str, kind: str, url: str, result: dict) -> str:
    run_id = str(uuid.uuid4())
    created_at = now()
    result["run_id"] = run_id
    result["created_at"] = created_at
    with connect() as db:
        db.execute("INSERT INTO runs(id,kind,url,created_at,result_json,owner_id) VALUES(?,?,?,?,?,?)",
                   (run_id, kind, url, created_at, json.dumps(result), owner_id))
        for item in result.get("findings", []):
            db.execute("INSERT INTO findings VALUES(?,?,?,?,?)", (item["id"], run_id, item.get("status", "Needs approval"), json.dumps(item), created_at))
    return run_id


def save_blueprint(owner_id: str, brief: dict, result: dict) -> str:
    blueprint_id = str(uuid.uuid4())
    created_at = now()
    result["blueprint_id"] = blueprint_id
    result["created_at"] = created_at
    with connect() as db:
        db.execute("INSERT INTO blueprints(id,created_at,brief_json,result_json,owner_id) VALUES(?,?,?,?,?)",
                   (blueprint_id, created_at, json.dumps(brief), json.dumps(result), owner_id))
    return blueprint_id


def _can_read(owner_id: str, user_id: str, role: str) -> bool:
    return role in {"admin", "company"} or owner_id == user_id


def list_runs(user_id: str, role: str, limit: int = 50) -> list[dict]:
    with connect() as db:
        if role in {"admin", "company"}:
            rows = db.execute("SELECT id,kind,url,created_at,result_json FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = db.execute("SELECT id,kind,url,created_at,result_json FROM runs WHERE owner_id=? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    out = []
    for row in rows:
        result = json.loads(row["result_json"])
        out.append({"id": row["id"], "kind": row["kind"], "url": row["url"], "created_at": row["created_at"], "finding_count": len(result.get("findings", [])), "score": result.get("health_score")})
    return out


def get_run(run_id: str, user_id: str, role: str) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT owner_id,result_json FROM runs WHERE id=?", (run_id,)).fetchone()
    return json.loads(row["result_json"]) if row and _can_read(row["owner_id"], user_id, role) else None


def get_blueprint(blueprint_id: str, user_id: str, role: str) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT owner_id,result_json FROM blueprints WHERE id=?", (blueprint_id,)).fetchone()
    return json.loads(row["result_json"]) if row and _can_read(row["owner_id"], user_id, role) else None


def update_finding(finding_id: str, status: str, user_id: str, role: str) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT findings.finding_json,findings.run_id,runs.owner_id FROM findings JOIN runs ON runs.id=findings.run_id WHERE findings.id=?", (finding_id,)).fetchone()
        if not row or not _can_read(row["owner_id"], user_id, role):
            return None
        finding = json.loads(row["finding_json"])
        finding["status"] = status
        updated = now()
        db.execute("UPDATE findings SET status=?,finding_json=?,updated_at=? WHERE id=?", (status, json.dumps(finding), updated, finding_id))
        run_row = db.execute("SELECT result_json FROM runs WHERE id=?", (row["run_id"],)).fetchone()
        result = json.loads(run_row["result_json"])
        result["findings"] = [finding if item["id"] == finding_id else item for item in result.get("findings", [])]
        db.execute("UPDATE runs SET result_json=? WHERE id=?", (json.dumps(result), row["run_id"]))
    return finding


def init_app() -> None:
    initialize()
