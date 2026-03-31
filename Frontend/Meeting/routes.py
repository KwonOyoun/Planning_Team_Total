from flask import Blueprint, send_from_directory, request, jsonify, send_file
import re
import os
import json

from .meeting_session import MeetingBrowserSession
from .tree_utils import expand_year_and_team
from .crawler import (
    get_meeting_list,
    open_meeting_by_index,
    crawl_detail_page_text
)
from .hwpx_generate import generate_hwpx_file, format_datetime_range_korean
from .openai_client import ask_gpt
from .prompt_templates import SORTING_TEMPLATE_PROMPT, WRITING_REPORT_PROMPT

Meeting_bp = Blueprint("Meeting", __name__)

LOGIN_URL = "https://gw.kothea.or.kr/#/login?logout=Y&lang=kr"
SESSION = None

def _open_and_parse(index, author):
    detail_page = open_meeting_by_index(SESSION, index)
    raw_text = crawl_detail_page_text(detail_page)
    prompt = SORTING_TEMPLATE_PROMPT.format(full_text=raw_text, author_hint=author)
    return ask_gpt(prompt)

def _login_and_prepare(username, password):
    page = SESSION.page

    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.wait_for_selector('#reqLoginId')
    page.locator('#reqLoginId:not([disabled])').fill(username)
    page.get_by_role("button", name=re.compile("다음|로그인")).click()

    page.wait_for_selector('#reqLoginPw')
    page.locator('#reqLoginPw').fill(password)
    page.get_by_role("button", name=re.compile("로그인")).click()

    page.wait_for_selector('#reqLoginId', state='detached', timeout=30000)
    page.wait_for_selector('#sideGnb', timeout=30000)

    # page.wait_for_function("() => !location.hash.includes('/login')")
    

    page.locator('#sideGnb li.module-item', has_text="전자결재(비영리)").first.click()

    # 🔑 마우스를 화면 빈 곳으로 이동 (hover 해제)
    page.mouse.move(10, 10)
    page.wait_for_timeout(200)

    page.locator('#UCA_UCA4000').click()
    page.locator('#UCA4030_UCA').click()

    for _ in range(40):
        for f in page.frames:
            if "ea" in (f.url or ""):
                SESSION.target_frame = f

                # ✅ 여기서 트리 클릭
                expand_year_and_team(SESSION.target_frame, 2025)

                return True
        page.wait_for_timeout(100)

    raise RuntimeError("iframe not found")

@Meeting_bp.route("/")
def index():
    return send_from_directory("Frontend/Meeting/Frontend", "index.html")

@Meeting_bp.route("/api/login", methods=["POST"])
def api_login():
    global SESSION
    data = request.json

    SESSION = MeetingBrowserSession(headless=True)

    # 🔑 핵심: Playwright 작업은 call() 안에서만
    SESSION.call(_login_and_prepare, data["username"], data["password"])

    meetings = SESSION.call(get_meeting_list, SESSION)

    return jsonify({
        "success": True,
        "meetings": meetings
    })

@Meeting_bp.route("/api/meetings", methods=["GET"])
def api_meetings():
    meetings = SESSION.call(get_meeting_list, SESSION)  # ✅ 반드시 call()
    return jsonify({
        "success": True,
        "meetings": meetings
    })

@Meeting_bp.route("/api/meetings/<int:index>", methods=["POST"])
def api_meeting_detail(index):
    data = request.json or {}
    author = data.get("author", "")

    parsed = SESSION.call(_open_and_parse, index, author)
    return jsonify({ "parsed": parsed })

@Meeting_bp.route("/api/generate_minutes_body", methods=["POST"])
def generate_minutes_body():
    try:
        data = request.json

        summaryText = data.get("summaryText", "")

        meeting_start = data.get("meetingStart", "")
        meeting_end = data.get("meetingEnd", "")

        print("회의 시작:", meeting_start)
        print("회의 종료:", meeting_end)

        meeting_datetime_text = ""
        if meeting_start and meeting_end:
            meeting_datetime_text = format_datetime_range_korean(
                meeting_start, meeting_end
            )
        

        # 🔹 GPT에게 줄 프롬프트 구성
        prompt = WRITING_REPORT_PROMPT.format(summary_text=summaryText)
        minutes_body = ask_gpt(prompt)

        return jsonify({
            "success": True,
            "minutesBody": minutes_body
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@Meeting_bp.route("/api/generate_hwpx", methods=["POST"])
def api_generate_hwpx():
    print("🔥 /api/generate_hwpx HIT")
    try:
        if request.is_json:
            data = request.json
        else:
            data = json.loads(request.form.get("payload", "{}"))

        meeting_data = {
            "projectName": data.get("projectName", ""),
            "meetingName": data.get("meetingName", ""),
            "meetingStart": data.get("meetingStart", ""),
            "meetingEnd": data.get("meetingEnd", ""),
            "meetingLocation": data.get("meetingLocation", ""),
            "participants": data.get("participants", []),
            "minutesBody": data.get("minutesBody", ""),
            "author": data.get("author", ""),
        }

        hwpx_path = generate_hwpx_file(meeting_data)

        return send_file(
            hwpx_path,
            as_attachment=True,
            download_name=os.path.basename(hwpx_path)
        )

    except Exception as e:
        return str(e), 500
    
@Meeting_bp.route("/close")
def close():
    global SESSION
    if SESSION:
        SESSION.close()
        SESSION = None
    return jsonify({"status": "closed"})
