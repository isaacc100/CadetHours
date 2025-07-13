import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

# Get a platform-safe path for the database
def get_db_file():
    if sys.platform == "win32":
        base_dir = Path(os.getenv("LOCALAPPDATA")) / "HourTracker"
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support" / "HourTracker"
    else:
        base_dir = Path.home() / ".hourtracker"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "hours.db"

DB_FILE = get_db_file()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        hours REAL NOT NULL,
        travel_time REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def add_entry(date, type_, hours, travel_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entries (date, type, hours, travel_time) VALUES (?, ?, ?, ?)",
                   (date, type_, hours, travel_time))
    conn.commit()
    conn.close()

def delete_entry(entry_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

def update_entry(entry_id, date, type_, hours, travel_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE entries
        SET date = ?, type = ?, hours = ?, travel_time = ?
        WHERE id = ?
    """, (date, type_, hours, travel_time, entry_id))
    conn.commit()
    conn.close()

def fetch_entries():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, type, hours, travel_time FROM entries ORDER BY date DESC")
    entries = cursor.fetchall()
    conn.close()
    return entries

def get_summary():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT type, SUM(hours) as total_hours, SUM(travel_time) as total_travel FROM entries GROUP BY type")
    summary = cursor.fetchall()

    cursor.execute("SELECT SUM(hours), SUM(travel_time) FROM entries")
    totals = cursor.fetchone()
    conn.close()
    return summary, totals

def reset_all_entries():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries")
    conn.commit()
    conn.close()
