from flask import Blueprint, render_template, jsonify, request, send_from_directory
import threading
import queue
import time
import socket
import os
from .automation_bot import GroupwareBot

Check_BTR_bp = Blueprint("Check_BTR", __name__, template_folder="templates")

command_queue = queue.Queue()

# [설정] 자동 로그인을 허용할 호스트명 (개발자 PC)
MY_HOST = "DESKTOP-RROO0P1" 

class BrowserThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.bot = None
        self.daemon = True
        self.running = True

    def run(self):
        print("Browser Thread Started")
        while self.running:
            try:
                try:
                    cmd_data = command_queue.get(timeout=1)
                    cmd, args, result_q = cmd_data
                    print(f"[DEBUG] [Thread] Dequeued command: {cmd}", flush=True)
                except queue.Empty:
                    if int(time.time()) % 10 == 0:
                        # print(f"[DEBUG] Thread Heartbeat... (Queue size: {command_queue.qsize()})", flush=True)
                        time.sleep(1)
                    continue

                res = None
                for attempt in range(2):
                    try:
                        if self.bot and not self.bot.is_connected():
                            print("⚠️ Browser disconnected. Resetting...")
                            try: self.bot.close()
                            except: pass
                            self.bot = None
                        
                        if not self.bot and cmd != "stop":
                            print("🚀 Initializing new Browser...")
                            self.bot = GroupwareBot(headless=False)
                            self.bot.start()

                        if cmd in ["get_trips", "open_doc", "draft", "check"]:
                            current_host = socket.gethostname()
                            auto_login = (current_host == MY_HOST)
                            
                            username = "koy" if auto_login else None
                            password = "dhdbs2354^^" if auto_login else None
                            
                            if not self.bot.login(username, password):
                                print("⚠️ Login required. Waiting for user action.")
                                res = {"status": "login_required", "message": "Please log in to Groupware"}
                                if result_q: result_q.put(res)
                                command_queue.task_done()
                                continue  

                        if cmd == "open_doc": res = self.bot.open_document(*args)
                        elif cmd == "draft": res = self.bot.draft_report(*args)
                        elif cmd == "check": res = self.bot.get_report_detail(*args)
                        elif cmd == "get_trips": res = self.bot.get_trip_list()
                        elif cmd == "stop":
                            if self.bot: self.bot.close()
                            self.running = False
                            res = True
                        
                        break

                    except Exception as e:
                        err_msg = str(e).lower()
                        is_fatal = "closed" in err_msg or "connection" in err_msg or "target page" in err_msg or "session" in err_msg
                        
                        if is_fatal and attempt == 0 and cmd != "stop":
                            print(f"⚠️ Browser connection lost ({e}). Restarting and retrying...")
                            if self.bot:
                                try: self.bot.close()
                                except: pass
                            self.bot = None
                            time.sleep(1)
                            continue 
                        
                        print(f"❌ Error executing {cmd}: {e}")
                        if cmd == "get_trips":
                            res = {"error": str(e)}
                        else:
                            res = (False, str(e))
                        break
                
                if result_q: result_q.put(res)
                command_queue.task_done()
            
            except Exception as e:
                print(f"Thread Loop Error: {e}")

def send_command(cmd, *args):
    q = queue.Queue()
    command_queue.put((cmd, args, q))
    try:
        res = q.get(timeout=300) 
        return res
    except queue.Empty:
        return None
    except Exception:
        return None

def start_browser_thread():
    thread = BrowserThread()
    thread.start()
    return thread

@Check_BTR_bp.route('/')
def index(): 
    return render_template('check_btr_index.html')

@Check_BTR_bp.route('/api/trips')
def get_trips():
    trips = send_command("get_trips")
    if isinstance(trips, dict):
        if trips.get("status") == "login_required": return jsonify(trips), 401
        if trips.get("error"): return jsonify(trips), 500
    return jsonify(trips) if trips is not None else (jsonify({"error": "Timeout"}), 500)

@Check_BTR_bp.route('/api/open', methods=['POST'])
def open_doc():
    doc_id = request.json.get("id")
    if not doc_id: return jsonify({"error": "ID required"}), 400
    res = send_command("open_doc", doc_id)
    if res is None: return jsonify({"error": "Timeout"}), 500
    success, msg = res
    return jsonify({"status": "success", "message": msg}) if success else (jsonify({"error": msg}), 500)

@Check_BTR_bp.route('/api/draft', methods=['POST'])
def draft():
    doc_id = request.json.get("id")
    res = send_command("draft", doc_id)
    if res is None: return jsonify({"error": "Timeout"}), 500
    success, msg = res
    return jsonify({"status": "success", "message": msg}) if success else (jsonify({"error": msg}), 500)

@Check_BTR_bp.route('/api/check_report', methods=['POST'])
def check():
    doc_id = request.json.get("id")
    res = send_command("check", doc_id)
    if res is None: return jsonify({"error": "Timeout"}), 500
    
    data, msg = res
    if data:
        issues = []
        if data['total_expense'] > 0 and data['attachment_count'] == 0:
            issues.append("ERROR: Expense claimed but no attachments!")
        return jsonify({"status": "success", "data": data, "issues": issues})
    else: return jsonify({"error": msg}), 500

@Check_BTR_bp.route('/api/stop')
def stop():
    send_command("stop")
    return jsonify({"status": "stopped"})
