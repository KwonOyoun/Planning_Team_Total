from flask import Flask, send_from_directory
from Frontend.Bizdraft.routes import Bizdraft_bp
from Frontend.Meeting.routes import Meeting_bp
from Frontend.Check_BTR.routes import Check_BTR_bp, start_browser_thread
from Frontend.Monitor_GOV.notice_webapp.routes import Monitor_GOV_bp, start_monitor_thread


import re

# Blueprint가 등록되어 개별 라우팅을 담당합니다.

app = Flask(
    __name__,
    static_folder="Frontend",
    static_url_path=""
)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()

# 메인
@app.route("/")
def home():
    return send_from_directory("Frontend", "index.html")



# Blueprint 등록
app.register_blueprint(Bizdraft_bp, url_prefix="/Bizdraft")
app.register_blueprint(Meeting_bp, url_prefix="/Meeting")
app.register_blueprint(Check_BTR_bp, url_prefix="/Check_BTR")
app.register_blueprint(Monitor_GOV_bp, url_prefix="/Monitor_GOV")


if __name__ == "__main__":
    start_browser_thread()
    start_monitor_thread()

    # app.run(host="0.0.0.0", port=5050, debug=True)
    app.run(host="0.0.0.0", port=8888, debug=True)
