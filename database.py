import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple
import datetime

DB_DIR = Path(__file__).parent / "database"
DB_PATH = DB_DIR / "diabetes.db"

def _get_connection():
    """Return a SQLite connection with row dict access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the required tables if they do not exist.
    Includes a `users` table for authentication and a `patients` table for records.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with _get_connection() as conn:
        cur = conn.cursor()
        # Users table (admin accounts)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Patients table as defined in the spec
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                visit_date DATE NOT NULL,
                pregnancies INTEGER,
                glucose REAL,
                blood_pressure REAL,
                skin_thickness REAL,
                insulin REAL,
                bmi REAL,
                diabetes_pedigree REAL,
                prediction TEXT,
                risk_percentage REAL,
                recommendation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

# ---------- User CRUD (only create for now) ----------
def create_user(username: str, password_hash: str) -> int:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        return cur.lastrowid

def get_user_by_username(username: str) -> Tuple[int, str] | None:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return (row["id"], row["password_hash"]) if row else None

# ---------- Patient CRUD ----------
def add_patient(record: Dict[str, Any]) -> int:
    """Insert a patient record. `record` keys must match column names (except id)."""
    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = list(record.values())
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"INSERT INTO patients ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        return cur.lastrowid

def get_patient_by_id(patient_id: str) -> Dict[str, Any] | None:
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def update_patient(patient_id: str, updates: Dict[str, Any]):
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [patient_id]
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE patients SET {set_clause} WHERE patient_id = ?", values)
        conn.commit()

def delete_patient(patient_id: str):
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
        conn.commit()

def search_patients(query: str) -> List[Dict[str, Any]]:
    """Simple search across patient_id, name, and phone (case‑insensitive)."""
    pattern = f"%{query}%"
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM patients
            WHERE patient_id LIKE ?
               OR name LIKE ?
               OR phone LIKE ?
            """,
            (pattern, pattern, pattern),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def get_dashboard_metrics() -> Dict[str, Any]:
    """Return aggregate metrics for the dashboard."""
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM patients")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM patients WHERE risk_percentage >= 71")
        high = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM patients WHERE risk_percentage <= 30")
        low = cur.fetchone()[0]
        cur.execute("SELECT AVG(risk_percentage) FROM patients")
        avg = cur.fetchone()[0] or 0
        # Recent predictions (last 5)
        cur.execute(
            """
            SELECT patient_id, name, risk_percentage, created_at
            FROM patients
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        recent = [dict(r) for r in cur.fetchall()]
        return {
            "total_patients": total,
            "high_risk": high,
            "low_risk": low,
            "average_risk": round(avg, 2),
            "recent_predictions": recent,
        }

# Initialise DB on import
init_db()
