# notice_webapp/app.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from zoneinfo import ZoneInfo
from datetime import datetime

# Add parent dir to path to import modules
# Add parent dir to path to import modules
BASE = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE))

from database import Database
from main import run_collection, AppConfig

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config & DB
config_path = BASE / "config.yaml"
conf = AppConfig(str(config_path))
db_path = conf.get("database", {}).get("path", "monitor.db")
db = Database(str(BASE / db_path))

# Constants for Flask
APP_DIR = Path(__file__).resolve().parent
TEMPLATES = APP_DIR / "templates"
STATIC = APP_DIR / "static"

app = Flask(__name__, template_folder=str(TEMPLATES), static_folder=str(STATIC))
KST = ZoneInfo("Asia/Seoul")

# 상태 관리를 위한 전역 변수
is_collecting = False

# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    disp_min = int(request.args.get("screen_min", 0))
    q = request.args.get("q", "").strip()
    
    # DB에서 조회
    items = db.get_notices(limit=200, min_score=disp_min, query=(q if q else None))
    
    # Grouping (UI 호환성 유지)
    groups = {}
    for it in items:
        src = it.get("source", "OTHER").upper()
        if src not in groups:
            groups[src] = []
        groups[src].append(it)

    # Sort groups
    group_list = []
    order = ["IRIS", "KEIT", "KIAT", "KHIDI", "G2B", "OTHER"]
    
    for src in order:
        if src in groups:
            group_list.append({"source": src, "count": len(groups[src]), "items": groups[src]})
    
    for src, it_list in groups.items():
        if src not in order:
            group_list.append({"source": src, "count": len(it_list), "items": it_list})

    stats = db.get_stats()
    
    # Template compatibility
    filt_conf = conf.get("filters", {}).get("healthcare", {})
    storage_threshold = filt_conf.get("storage_threshold", 0)

    stats_compat = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # Dynamic
        "count_total": stats.get("total_notices", 0),
        "count_shown": len(items),
        "avg_score": round(sum(i.get("score", 0) for i in items) / len(items), 2) if items else 0.0,
        "file_threshold": storage_threshold,
        "is_refreshing": is_collecting,
    }

    return render_template("index.html", groups=group_list, stats=stats_compat, params={"screen_min": disp_min, "q": q})

@app.get("/api/notices")
def api_notices():
    q = request.args.get("q", "")
    items = db.get_notices(limit=200, query=(q if q else None))
    return jsonify({"count": len(items), "items": items})

@app.get("/edu")
def edu():
    disp_min = 0
    q = request.args.get("q", "").strip()
    
    # DB에서 조회 (events 테이블)
    # events table needs a get_events method or use generic query?
    # For now, let's implement get_events in database.py or raw query here? 
    # Better to add get_events to database.py
    # But to save time, I will use raw query logic via db._get_conn() or add method.
    # Actually, I should add get_events to database.py for consistency.
    # But I can't easily edit database.py now without context switch.
    # I'll check database.py content from Step 174. 
    # It has get_notices only.
    # I should add get_events to database.py first? or just do inline query in app.py?
    # Inline is faster.
    conn = db._get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    sql = "SELECT * FROM events ORDER BY date DESC, created_at DESC LIMIT 200"
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    
    items = []
    for r in rows:
        d = dict(r)
        d["meta"] = __import__("json").loads(d["meta"]) if d["meta"] else {}
        items.append(d)

    if q:
        q_lower = q.lower()
        items = [x for x in items if q_lower in str(x).lower()] # Simple search

    stats = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(items),
        "is_refreshing": is_collecting,
    }
    
    return render_template("events.html", items=items, stats=stats, params={"q": q})

@app.get("/api/events")
def api_events():
    conn = db._get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY date DESC LIMIT 200")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"count": len(rows), "items": rows})

@app.post("/refresh", endpoint="refresh_all")
def refresh_all():
    # Trigger job immediately
    scheduler.add_job(run_collection_job, 'date', run_date=datetime.now(), id='manual_refresh_all', replace_existing=True)
    return redirect(url_for("index"))

@app.post("/refresh/notices", endpoint="refresh_notices")
def refresh_notices():
    scheduler.add_job(run_collection_job, 'date', run_date=datetime.now(), id='manual_refresh_notices', replace_existing=True)
    return redirect(url_for("index"))

@app.post("/refresh/events", endpoint="refresh_events")
def refresh_events():
    scheduler.add_job(run_collection_job, 'date', run_date=datetime.now(), id='manual_refresh_events', replace_existing=True)
    return redirect(url_for("edu"))

# ──────────────────────────────────────────────────────────────────────────────
# KIAT Proxy (유지)
# ──────────────────────────────────────────────────────────────────────────────
import requests
import re

def _inject_mute_alerts(html: str) -> str:
    snippet = "<script>try{window.alert=function(){};}catch(e){}</script>"
    return re.sub(r"</head>", snippet + "</head>", html, 1, flags=re.I) if re.search(r"</head>", html, flags=re.I) else snippet + html

@app.get("/proxy/kiat/<contents_id>")
def proxy_kiat(contents_id):
    HOST      = "https://www.kiat.or.kr"
    LIST_PAGE = f"{HOST}/front/board/boardContentsListPage.do"
    VIEW_DO   = f"{HOST}/front/board/boardContentsView.do"
    BOARD_ID  = "90"
    MENU_ID   = "b159c9dac684471b87256f1e25404f5e"
    
    title = request.args.get("t", "")
    sess = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
    
    try:
        ref = f"{LIST_PAGE}?board_id={BOARD_ID}&MenuId={MENU_ID}"
        sess.get(LIST_PAGE, params={"board_id":BOARD_ID, "MenuId":MENU_ID}, headers={**headers}, timeout=10)
        
        payload = {
            "miv_pageNo": "1", "miv_pageSize": "15", "mode": "W", "contents_id": contents_id, 
            "board_id": BOARD_ID, "MenuId": MENU_ID, "state_filter": "W"
        }
        pr = sess.post(VIEW_DO, data=payload, headers={**headers, "Referer": ref}, timeout=15)
        html = pr.text
        
        # 정적 경로 보정
        html = re.sub(r'((?:href|src)=["\'])/(?!/)', r'\1https://www.kiat.or.kr/', html, flags=re.I)
        return Response(_inject_mute_alerts(html), mimetype="text/html")
    except Exception:
        return redirect(f"{LIST_PAGE}")

# ──────────────────────────────────────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────────────────────────────────────
scheduler = BackgroundScheduler(timezone=KST)

def run_collection_job():
    global is_collecting
    if is_collecting:
        logger.warning("Scheduler: Collection is already in progress. Skipping.")
        return

    is_collecting = True
    logger.info("Scheduler: Starting collection job...")
    try:
        run_collection(str(config_path))
    except Exception as e:
        logger.error(f"Scheduler Error: {e}")
    finally:
        is_collecting = False
        logger.info("Scheduler: Collection job finished.")

def start_scheduler():
    # 한 번 초기 수집 수행 (선택 사항, 이미 되었으므로 스케줄만)
    scheduler.add_job(run_collection_job, IntervalTrigger(minutes=30), id='collection_job', replace_existing=True)
    scheduler.start()

if __name__ == "__main__":
    start_scheduler()
    # Run server
    print(app.url_map)
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
