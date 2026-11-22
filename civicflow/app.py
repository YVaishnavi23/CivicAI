"""CivicFlow AI: FastAPI application (API + static frontend)."""
import json
import os
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel

import ai
import db
import matching
import scoring

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

STATUSES = ("Received", "Under Review", "In Progress", "Resolved")
LANGUAGES = ("en", "te", "hi")
MAX_PHOTO_BYTES = 3 * 1024 * 1024
TICKET_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    yield


app = FastAPI(title="CivicFlow AI", version="1.0", lifespan=lifespan)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_ticket_id() -> str:
    return "CF-" + "".join(secrets.choice(TICKET_ALPHABET) for _ in range(8))


def sniff_image(data: bytes) -> Optional[str]:
    """Identify the real image type from magic bytes (the client MIME type is not trusted)."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


# ---------- persistence helpers ----------

def related_count(conn, cluster_id: str) -> int:
    n = conn.execute("SELECT COUNT(*) FROM complaints WHERE cluster_id = ?", (cluster_id,)).fetchone()[0]
    return max(0, n - 1)


def rescore_cluster(conn, cluster_id: str) -> None:
    """Re-apply the related-reports factor to every member after a cluster changes size."""
    n = related_count(conn, cluster_id)
    for row in conn.execute("SELECT id, priority_reasons FROM complaints WHERE cluster_id = ?", (cluster_id,)).fetchall():
        reasons = scoring.set_related(json.loads(row["priority_reasons"]), n)
        score = scoring.total(reasons)
        conn.execute(
            "UPDATE complaints SET priority_reasons = ?, priority_score = ?, priority = ?, updated_at = ? WHERE id = ?",
            (json.dumps(reasons, ensure_ascii=False), score, scoring.label(score), now(), row["id"]),
        )


def create_complaint(description, location, language, image_path=None, is_demo=0, force_rules=False) -> dict:
    # Slow network call happens before the write transaction is opened.
    a = ai.assess(description, location, language, force_rules=force_rules)
    conn = db.connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cluster = matching.find_cluster(conn, a["category"], is_demo, location, description)
        for _ in range(5):
            ticket = new_ticket_id()
            if not conn.execute("SELECT 1 FROM complaints WHERE ticket_id = ?", (ticket,)).fetchone():
                break
        cluster_id = cluster or ticket
        n_related = conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE cluster_id = ?", (cluster_id,)
        ).fetchone()[0] if cluster else 0
        reasons = scoring.build_reasons(a["category"], a["severity"], a["safety_evidence"], a["duration_evidence"], n_related)
        score = scoring.total(reasons)
        stamp = now()
        conn.execute(
            """INSERT INTO complaints (ticket_id, description, original_language, location, category, severity,
               priority, priority_score, priority_reasons, department, recommendation, summary, status, cluster_id,
               ai_mode, image_path, is_demo, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ticket, description, language, location, a["category"], a["severity"], scoring.label(score), score,
             json.dumps(reasons, ensure_ascii=False), scoring.DEPARTMENTS[a["category"]], a["recommendation"],
             a["summary"], "Received", cluster_id, a["ai_mode"], image_path, is_demo, stamp, stamp),
        )
        if cluster:
            rescore_cluster(conn, cluster_id)  # earlier reports in the cluster gain the related-reports factor
        row = conn.execute("SELECT * FROM complaints WHERE ticket_id = ?", (ticket,)).fetchone()
        result = citizen_view(row, related_count(conn, cluster_id))
        conn.execute("COMMIT")
        return result
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


# ---------- serializers ----------

def citizen_view(row, n_related: int) -> dict:
    return {
        "ticket_id": row["ticket_id"],
        "description": row["description"],
        "location": row["location"],
        "language": row["original_language"],
        "category": row["category"],
        "status": row["status"],
        "priority": row["priority"],
        "department": row["department"],
        "recommendation": row["recommendation"],
        "related_count": n_related,
        "ai_mode": row["ai_mode"],
        "image_url": f"/uploads/{row['image_path']}" if row["image_path"] else None,
        "is_demo": bool(row["is_demo"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def admin_view(row, cluster_members: list) -> dict:
    view = citizen_view(row, max(0, len(cluster_members) - 1))
    view.update({
        "severity": row["severity"],
        "priority_score": row["priority_score"],
        "priority_reasons": json.loads(row["priority_reasons"]),
        "summary": row["summary"],
        "cluster_id": row["cluster_id"],
        "related_tickets": [t for t in cluster_members if t != row["ticket_id"]],
        "score_disclaimer": "Illustrative prototype heuristic, not an official government risk score.",
    })
    return view


# ---------- routes ----------

@app.get("/health")
def health():
    return {"status": "ok", "service": "CivicFlow AI"}


@app.get("/api/config")
def get_config():
    cfg = ai.config()
    return {
        "ai_configured": bool(cfg["key"]),
        "ai_mode": "llm" if cfg["key"] else "rules_fallback",
        "model": cfg["model"] if cfg["key"] else None,
        "max_photo_bytes": MAX_PHOTO_BYTES,
        "languages": list(LANGUAGES),
    }


@app.post("/api/complaints", status_code=201)
async def submit_complaint(
    description: str = Form(""),
    location: str = Form(""),
    language: str = Form("en"),
    photo: Optional[UploadFile] = File(None),
):
    description, location, language = description.strip(), location.strip(), language.strip().lower()
    if not 10 <= len(description) <= 2000:
        raise HTTPException(422, "Describe the issue in 10 to 2000 characters.")
    if not 3 <= len(location) <= 200:
        raise HTTPException(422, "Enter a location of 3 to 200 characters, such as a street and neighbourhood.")
    if language not in LANGUAGES:
        raise HTTPException(422, "Language must be one of: en, te, hi.")

    image_name = None
    if photo is not None and photo.filename:
        data = await photo.read(MAX_PHOTO_BYTES + 1)
        if len(data) > MAX_PHOTO_BYTES:
            raise HTTPException(413, "Photo is larger than 3 MB. Choose a smaller image.")
        kind = sniff_image(data)
        if kind is None or kind not in IMAGE_TYPES:
            raise HTTPException(415, "Unsupported photo type. Upload a JPG, PNG or WEBP image.")
        image_name = secrets.token_hex(16) + IMAGE_TYPES[kind]
        db.upload_dir().mkdir(parents=True, exist_ok=True)
        (db.upload_dir() / image_name).write_bytes(data)

    try:
        return create_complaint(description, location, language, image_path=image_name)
    except Exception:
        if image_name:
            (db.upload_dir() / image_name).unlink(missing_ok=True)
        raise


@app.get("/api/complaints/{ticket_id}")
def track_complaint(ticket_id: str):
    conn = db.connect()
    try:
        row = conn.execute("SELECT * FROM complaints WHERE ticket_id = ?", (ticket_id.strip().upper(),)).fetchone()
        if not row:
            raise HTTPException(404, "No report found with that reference ID. Check the ID and try again.")
        return citizen_view(row, related_count(conn, row["cluster_id"]))
    finally:
        conn.close()


@app.get("/api/admin/complaints")
def admin_queue(status: Optional[str] = None, priority: Optional[str] = None):
    if status and status not in STATUSES:
        raise HTTPException(422, f"status must be one of: {', '.join(STATUSES)}")
    if priority and priority not in ("High", "Medium", "Low"):
        raise HTTPException(422, "priority must be one of: High, Medium, Low")
    conn = db.connect()
    try:
        everything = conn.execute("SELECT ticket_id, cluster_id, status, priority FROM complaints").fetchall()
        clusters = {}
        for r in everything:
            clusters.setdefault(r["cluster_id"], []).append(r["ticket_id"])
        metrics = {
            "total": len(everything),
            "high_priority": sum(1 for r in everything if r["priority"] == "High"),
            "clusters": sum(1 for members in clusters.values() if len(members) > 1),
            "resolved": sum(1 for r in everything if r["status"] == "Resolved"),
        }
        sql, args = "SELECT * FROM complaints WHERE 1=1", []
        if status:
            sql += " AND status = ?"
            args.append(status)
        if priority:
            sql += " AND priority = ?"
            args.append(priority)
        sql += (" ORDER BY CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,"
                " created_at DESC, id DESC")
        rows = conn.execute(sql, args).fetchall()
        return {"metrics": metrics, "complaints": [admin_view(r, clusters[r["cluster_id"]]) for r in rows]}
    finally:
        conn.close()


class StatusUpdate(BaseModel):
    status: Literal["Received", "Under Review", "In Progress", "Resolved"]


@app.patch("/api/complaints/{ticket_id}/status")
def update_status(ticket_id: str, body: StatusUpdate):
    conn = db.connect()
    try:
        cur = conn.execute(
            "UPDATE complaints SET status = ?, updated_at = ? WHERE ticket_id = ?",
            (body.status, now(), ticket_id.strip().upper()),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "No report found with that reference ID.")
        row = conn.execute("SELECT * FROM complaints WHERE ticket_id = ?", (ticket_id.strip().upper(),)).fetchone()
        return citizen_view(row, related_count(conn, row["cluster_id"]))
    finally:
        conn.close()


DEMO_REPORTS = [
    ("Large, deep pothole at the school gate. Children cross here and two-wheelers swerve around it. "
     "It has been there for two weeks and it is dangerous.",
     "Road No. 12, near the school gate, Banjara Hills", "en"),
    ("Dangerous pothole at the school entrance. A scooter fell here yesterday and children walk past the hole "
     "every morning.",
     "Banjara Hills Road 12, school gate", "en"),
    ("Garbage is overflowing from the community dustbin and spilling onto the lane. It has not been collected for 4 days "
     "and the smell is spreading.",
     "Lane 3, opposite the bus stop, Jubilee Hills", "en"),
]


@app.post("/api/demo/seed")
def seed_demo():
    conn = db.connect()
    try:
        existing = conn.execute("SELECT COUNT(*) FROM complaints WHERE is_demo = 1").fetchone()[0]
    finally:
        conn.close()
    if existing:
        return {"seeded": False, "created": 0, "message": "Demo reports are already loaded."}
    created = [
        # demo data always uses the deterministic rules assessment so the scenario is reproducible
        create_complaint(d, loc, lang, is_demo=1, force_rules=True)["ticket_id"]
        for d, loc, lang in DEMO_REPORTS
    ]
    return {"seeded": True, "created": len(created), "tickets": created, "message": "Demo scenario loaded."}


@app.delete("/api/demo/clear")
def clear_demo():
    conn = db.connect()
    try:
        cur = conn.execute("DELETE FROM complaints WHERE is_demo = 1")
        return {"deleted": cur.rowcount}
    finally:
        conn.close()


@app.get("/uploads/{name}")
def get_upload(name: str):
    if not re.fullmatch(r"[a-f0-9]{32}\.(jpg|png|webp)", name):
        raise HTTPException(404, "Not found")
    path = db.upload_dir() / name
    if not path.is_file():
        raise HTTPException(404, "Not found")
    return FileResponse(path)


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
