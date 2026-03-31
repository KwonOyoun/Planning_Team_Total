from flask import Flask, render_template, jsonify, request
from automation_bot import GroupwareBot
import threading
import queue
import time

app = Flask(__name__)
command_queue = queue.Queue()

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
                try:
                    cmd_data = command_queue.get(timeout=1)
                    cmd, args, result_q = cmd_data
                except queue.Empty:
                    # 명령어가 없어도 연결 상태를 체크할 수 있음 (선택사항)
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
                            if not self.bot.login("koy", "dhdbs2354^^"):
                                raise Exception("Login failed or page unreachable")

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
                        res = (False, str(e)) if cmd != "get_trips" else None
                        break
                
                if result_q: result_q.put(res)
                command_queue.task_done()
            
            except Exception as e:
                print(f"Thread Loop Error: {e}")

def send_command(cmd, *args):
    q = queue.Queue()
    command_queue.put((cmd, args, q))
    try: return q.get(timeout=300)
    except: return None

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/trips')
def get_trips():
    trips = send_command("get_trips")
    return jsonify(trips) if trips is not None else (jsonify({"error": "Timeout"}), 500)

@app.route('/api/open', methods=['POST'])
def open_doc():
    doc_id = request.json.get("id")
    if not doc_id: return jsonify({"error": "ID required"}), 400
    print(f"Requesting open for ID: {doc_id}")
    success, msg = send_command("open_doc", doc_id)
    return jsonify({"status": "success", "message": msg}) if success else (jsonify({"error": msg}), 500)

@app.route('/api/draft', methods=['POST'])
def draft():
    doc_id = request.json.get("id")
    success, msg = send_command("draft", doc_id)
    return jsonify({"status": "success", "message": msg}) if success else (jsonify({"error": msg}), 500)

@app.route('/api/check_report', methods=['POST'])
def check():
    doc_id = request.json.get("id")
    data, msg = send_command("check", doc_id)
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
    app.run(debug=True, port=5001, use_reloader=False)