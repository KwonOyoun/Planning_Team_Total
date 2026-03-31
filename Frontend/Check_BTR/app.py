from flask import Flask, render_template, jsonify, request
from automation_bot import GroupwareBot
import threading
import queue
import time

import socket

app = Flask(__name__)
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
                # 1초마다 명령어를 기다림
                # 1초마다 명령어를 기다림
                try:
                    cmd_data = command_queue.get(timeout=1)
                    cmd, args, result_q = cmd_data
                    print(f"[DEBUG] [Thread] Dequeued command: {cmd}", flush=True)
                except queue.Empty:
                    # Heartbeat logging (every ~10s)
                    if int(time.time()) % 10 == 0:
                        print(f"[DEBUG] Thread Heartbeat... (Queue size: {command_queue.qsize()})", flush=True)
                        time.sleep(1) # Prevent spamming in the same second
                    continue

                res = None
                # Command Retry Loop (Max 2 attempts)
                for attempt in range(2):
                    try:
                        # 1. Recovery Check: If bot exists but is disconnected, kill it
                        if self.bot and not self.bot.is_connected():
                            print("⚠️ Browser disconnected. Resetting...")
                            try: self.bot.close()
                            except: pass
                            self.bot = None
                        
                        # 2. Init if needed
                        if not self.bot and cmd != "stop":
                            print("🚀 Initializing new Browser...")
                            self.bot = GroupwareBot(headless=False)
                            self.bot.start()

                        # 3. Login/Nav check
                        if cmd in ["get_trips", "open_doc", "draft", "check"]:
                            # login returns True/False. If False, we might want to retry or just fail.
                            # For now, let's assume if it fails, it's a connection issue or similar.
                            
                            # [수정] 내 PC(MY_HOST)일 때만 자동 로그인 시도
                            current_host = socket.gethostname()
                            auto_login = (current_host == MY_HOST)
                            
                            username = "koy" if auto_login else None
                            password = "dhdbs2354^^" if auto_login else None
                            
                            if not self.bot.login(username, password):
                                # 로그인이 안 된 경우 (수동 로그인 대기)
                                # 에러를 발생시키는 대신, 프론트엔드에 약속된 신호를 보냄
                                print("⚠️ Login required. Waiting for user action.")
                                res = {"status": "login_required", "message": "Please log in to Groupware"}
                                # 커맨드 처리 루프 종료 (성공 처럼 취급하되 결과값에 상태 포함)
                                if result_q: result_q.put(res)
                                command_queue.task_done()
                                continue  # 다음 명령 대기 (현재 명령은 완료 처리됨)

                        # 4. Execute
                        if cmd == "open_doc": res = self.bot.open_document(*args)
                        elif cmd == "draft": res = self.bot.draft_report(*args)
                        elif cmd == "check": res = self.bot.get_report_detail(*args)
                        elif cmd == "get_trips": res = self.bot.get_trip_list()
                        elif cmd == "stop":
                            if self.bot: self.bot.close()
                            self.running = False
                            res = True
                        
                        # Success
                        break

                    except Exception as e:
                        err_msg = str(e).lower()
                        # Check for keywords indicating a closed/dead browser
                        is_fatal = "closed" in err_msg or "connection" in err_msg or "target page" in err_msg or "session" in err_msg
                        
                        if is_fatal and attempt == 0 and cmd != "stop":
                            print(f"⚠️ Browser connection lost ({e}). Restarting and retrying...")
                            if self.bot:
                                try: self.bot.close()
                                except: pass
                            self.bot = None
                            time.sleep(1) # Brief pause before restart
                            continue # Retry loop
                        
                        print(f"❌ Error executing {cmd}: {e}")
                        # [수정] get_trips 에러 시에도 상세 사유 반환
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
    print(f"[DEBUG] Enqueueing command: {cmd}")
    command_queue.put((cmd, args, q))
    try:
        print(f"[DEBUG] Waiting for result for {cmd}...")
        # [수정] 작업 시간 고려하여 Timeout 300초(5분) 설정
        res = q.get(timeout=300) 
        print(f"[DEBUG] Got result for {cmd}: {type(res)}")
        return res
    except queue.Empty:
        print(f"[DEBUG] Timeout waiting for {cmd} result!")
        return None
    except Exception as e:
        print(f"[DEBUG] Exception in send_command: {e}")
        return None

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/trips')
def get_trips():
    trips = send_command("get_trips")
    if isinstance(trips, dict):
        if trips.get("status") == "login_required": return jsonify(trips), 401
        if trips.get("error"): return jsonify(trips), 500
    return jsonify(trips) if trips is not None else (jsonify({"error": "Timeout"}), 500)

@app.route('/api/open', methods=['POST'])
def open_doc():
    doc_id = request.json.get("id")
    if not doc_id: return jsonify({"error": "ID required"}), 400
    print(f"Requesting open for ID: {doc_id}")
    res = send_command("open_doc", doc_id)
    if res is None: return jsonify({"error": "Timeout"}), 500
    success, msg = res
    return jsonify({"status": "success", "message": msg}) if success else (jsonify({"error": msg}), 500)

@app.route('/api/draft', methods=['POST'])
def draft():
    doc_id = request.json.get("id")
    res = send_command("draft", doc_id)
    if res is None: return jsonify({"error": "Timeout"}), 500
    success, msg = res
    return jsonify({"status": "success", "message": msg}) if success else (jsonify({"error": msg}), 500)

@app.route('/api/check_report', methods=['POST'])
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

@app.route('/api/stop')
def stop():
    send_command("stop")
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    BrowserThread().start()
    app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)