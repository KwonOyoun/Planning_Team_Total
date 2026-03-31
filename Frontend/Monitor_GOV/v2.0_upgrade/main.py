import os
import yaml
import logging
import requests
from pathlib import Path
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings globally (often needed for government sites)
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Local imports
from database import Database
from notifier.slack import SlackNotifier
from notifier.email import EmailNotifier
import filters.healthcare as healthcare

# Crawlers
from crawlers.g2b_api import fetch_g2b_notices
from crawlers.iris import fetch_iris_notices, fetch_notice_metadata_v2, fetch_body_and_attachment_text_by_id
from crawlers.khidi import fetch_khidi_notices
from crawlers.kiat import fetch_kiat_notices
from crawlers.keit_srome import fetch_keit_srome_notices
from crawlers.khidi_events import fetch_khidi_events

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class AppConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.path = config_path
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            logger.warning(f"Config file {self.path} not found. Using defaults.")
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get(self, key, default=None):
        return self.data.get(key, default)

def _iris_meta_from_link(link: str) -> dict:
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(link).query)
    ancm_id = (qs.get("ancmId") or [None])[0]
    return fetch_notice_metadata_v2(ancm_id, ancm_prg="ancmIng") if ancm_id else {}

def enrich_and_filter(notices, fetch_meta_func=None, fetch_extra_text_func=None, threshold=0):
    from concurrent.futures import ThreadPoolExecutor
    
    selected = []

    def process_item(n):
        meta = n.get("meta", {})
        if fetch_meta_func:
            try:
                meta = fetch_meta_func(n["link"]) or meta
            except Exception:
                pass

        extra_text = ""
        if fetch_extra_text_func:
            try:
                extra_text = fetch_extra_text_func(n["link"])
            except Exception:
                pass

        ok, score, reasons = healthcare.is_interesting_for_association(meta, extra_text, threshold=threshold)
        if ok:
            return {**n, "meta": meta, "score": score, "reasons": reasons}
        return None

    # Parallel enrichment
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(process_item, notices))
    
    selected = [r for r in results if r is not None]
    return selected

def run_collection(config_path: str = "config.yaml"):
    # 1. Init Config & DB
    conf = AppConfig(config_path)
    db = Database(conf.get("database", {}).get("path", "monitor.db"))
    
    # 2. Init Filters
    healthcare.init_config(conf.get("filters", {}).get("healthcare", {}))
    threshold = conf.get("filters", {}).get("healthcare", {}).get("threshold", 5)

    # 3. Init Notifiers
    notif_conf = conf.get("notifications", {})
    filt_conf = conf.get("filters", {}).get("healthcare", {})
    
    storage_threshold = filt_conf.get("storage_threshold", 0)
    notify_threshold = filt_conf.get("notify_threshold", 5)
    
    # SSL Bypass Check
    verify_ssl = conf.get("crawlers", {}).get("defaults", {}).get("verify_ssl", True)
    if not verify_ssl:
        logger.info("SSL Verification disabled globally.")
        orig_session_request = requests.Session.request
        def patched_session_request(self, method, url, **kwargs):
            kwargs.setdefault('verify', False)
            return orig_session_request(self, method, url, **kwargs)
        requests.Session.request = patched_session_request

        orig_requests_request = requests.request
        def patched_requests_request(method, url, **kwargs):
            kwargs.setdefault('verify', False)
            return orig_requests_request(method, url, **kwargs)
        requests.request = patched_req = patched_requests_request
        # Also patch helper methods
        requests.get = lambda url, **kwargs: requests.request("GET", url, **kwargs)
        requests.post = lambda url, **kwargs: requests.request("POST", url, **kwargs)
    
    slack = SlackNotifier(os.getenv(notif_conf.get("slack", {}).get("webhook_url_env", ""), ""))
    email = EmailNotifier(
        server=notif_conf.get("email", {}).get("smtp_server"),
        port=notif_conf.get("email", {}).get("smtp_port"),
        user=os.getenv(notif_conf.get("email", {}).get("sender_env", "")),
        password=os.getenv(notif_conf.get("email", {}).get("password_env", "")),
        recipients=notif_conf.get("email", {}).get("recipients", [])
    )
    
    slack_enabled = notif_conf.get("slack", {}).get("enabled", False)
    email_enabled = notif_conf.get("email", {}).get("enabled", False)

    import time
    from concurrent.futures import ThreadPoolExecutor

    start_time = time.time()
    logger.info("Starting collection (Parallel Mode)...")
    logger.info(f"Thresholds: Storage >= {storage_threshold}, Notify >= {notify_threshold}")

    # 4. Collect
    max_pages = conf.get("crawlers", {}).get("defaults", {}).get("max_pages", 3)
    
    def safe_fetch(source, fetch_func, **kwargs):
        try:
            items = fetch_func(**kwargs)
            logger.info(f"{source}: {len(items)} raw items")
            return source, [{"source": source, **n} for n in items]
        except Exception as e:
            logger.error(f"{source} Error: {e}")
            return source, []

    # Prepare tasks
    tasks = [
        ("IRIS", fetch_iris_notices, {"max_pages": max_pages}),
        ("KHIDI", fetch_khidi_notices, {"max_pages": max_pages}),
        ("KIAT", fetch_kiat_notices, {"max_pages": max_pages}),
        ("KEIT", fetch_keit_srome_notices, {"max_pages": 1}),
    ]
    
    # G2B 
    g2b_conf = conf.get("crawlers", {}).get("g2b", {})
    if os.getenv(g2b_conf.get("api_key_env", "G2B_API_KEY")):
        tasks.append(("G2B", fetch_g2b_notices, {
            "max_pages": max_pages,
            "rows": 50,
            "days": g2b_conf.get("days", 5),
            "query": g2b_conf.get("keywords")
        }))

    # Execute in Parallel
    all_raw = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_src = {executor.submit(safe_fetch, src, func, **kwargs): src for src, func, kwargs in tasks}
        for future in future_to_src:
            src, items = future.result()
            all_raw[src] = items

    # 5. Filter & Enrich
    total_new = 0
    total_notified = 0

    for source, items in all_raw.items():
        # Special handling for IRIS meta
        fetch_meta = _iris_meta_from_link if source == "IRIS" else None
        # Special handling for IRIS text (optional, expensive)
        fetch_text = None 
        
        # Use storage_threshold here to save everything we might want to see
        filtered = enrich_and_filter(items, fetch_meta_func=fetch_meta, fetch_extra_text_func=fetch_text, threshold=storage_threshold)
        logger.info(f"{source}: {len(filtered)} items (score >= {storage_threshold})")

        for item in filtered:
            is_new = db.upsert_notice(item)
            if is_new:
                total_new += 1
                if item['score'] >= 5: # Log high scores
                    logger.info(f"New High-Score Item: [{item['source']}] {item['title']} ({item['score']})")
                
                # Use notify_threshold for alerts
                if item['score'] >= notify_threshold:
                    if slack_enabled:
                         slack.send_notice(item)
                    if email_enabled:
                         email.send_notice(item)
                    total_notified += 1

    # 6. KHIDI Events (Parallelize this as well if needed, but it's small)
    events = [{"source":"KHIDI_EDU", **n} for n in fetch_khidi_events(max_pages=max_pages)]
    for e in events:
        db.upsert_event(e)
    logger.info(f"KHIDI Events: {len(events)} items processed")

    elapsed = time.time() - start_time
    logger.info(f"Collection Complete in {elapsed:.2f}s. New Notices: {total_new}, Notified: {total_notified}")
    return {"new": total_new, "notified": total_notified, "elapsed": elapsed}

if __name__ == "__main__":
    run_collection()
