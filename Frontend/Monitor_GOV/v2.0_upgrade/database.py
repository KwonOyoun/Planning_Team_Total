import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "monitor.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        # Notices table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notices (
                id TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                link TEXT,
                institution TEXT,
                date TEXT,
                end_date TEXT,
                score INTEGER,
                reasons TEXT, -- JSON string
                meta TEXT,    -- JSON string
                created_at TEXT,
                is_read INTEGER DEFAULT 0,
                is_hidden INTEGER DEFAULT 0
            )
        """)
        
        # Events table (for KHIDI edu etc)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                link TEXT,
                institution TEXT,
                date TEXT,
                meta TEXT, -- JSON string
                created_at TEXT
            )
        """)

        # Sync log to track last run times
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                task_name TEXT PRIMARY KEY,
                last_run TEXT,
                status TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def upsert_notice(self, item: Dict[str, Any]) -> bool:
        """
        Insert or ignore notice. Returns True if inserted (new), False if ignored (duplicate).
        Logic: ID collision means it's already there. We might want to update fields, but usually notices don't change much.
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        # Generate ID if not present (hash of link)
        if "id" not in item:
            import hashlib
            link = item.get("link") or item.get("title")
            item["id"] = hashlib.md5(link.encode()).hexdigest()

        try:
            cur.execute("""
                INSERT INTO notices (id, source, title, link, institution, date, end_date, score, reasons, meta, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["id"],
                item.get("source"),
                item.get("title"),
                item.get("link"),
                item.get("institution"),
                item.get("date"),
                item.get("end_date"),
                item.get("score", 0),
                json.dumps(item.get("reasons", []), ensure_ascii=False),
                json.dumps(item.get("meta", {}), ensure_ascii=False),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def upsert_event(self, item: Dict[str, Any]) -> bool:
        conn = self._get_conn()
        cur = conn.cursor()
        
        if "id" not in item:
            import hashlib
            link = item.get("link") or item.get("title")
            item["id"] = hashlib.md5(link.encode()).hexdigest()

        try:
            cur.execute("""
                INSERT INTO events (id, source, title, link, institution, date, meta, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["id"],
                item.get("source"),
                item.get("title"),
                item.get("link"),
                item.get("institution"),
                item.get("date"),
                json.dumps(item.get("meta", {}), ensure_ascii=False),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_notices(self, limit: int = 100, min_score: int = 0, query: str = None) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor()
        
        sql = "SELECT * FROM notices WHERE score >= ? AND is_hidden = 0"
        params = [min_score]
        
        if query:
            sql += " AND (title LIKE ? OR institution LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
            
        sql += " ORDER BY date DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            d = dict(row)
            d["reasons"] = json.loads(d["reasons"]) if d["reasons"] else []
            d["meta"] = json.loads(d["meta"]) if d["meta"] else {}
            results.append(d)
        conn.close()
        return results

    def get_stats(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM notices")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM notices WHERE created_at >= date('now')")
        today = cur.fetchone()[0]
        conn.close()
        return {"total_notices": total, "new_today": today}
