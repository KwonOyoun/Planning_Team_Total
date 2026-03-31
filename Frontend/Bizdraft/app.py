from flask import Flask, send_from_directory, request, jsonify, send_file, request, abort
from .main import generate_proposal_and_hwpx, generate_titles_from_keywords
from .prompt_templates import (
    TITLE_GENERATION_PROMPT,
    OVERVIEW_PROMPT,
    NEED_PROMPT,
    SUGGESTION_PROMPT,
    OVERVIEW_ref_PROMPT,
    reference2_PROMPT,
    reference3_PROMPT,
    reference4_PROMPT
)

import os
import re
from .config import OUTPUT_DIR


app = Flask(
    __name__,
    static_folder="Frontend",      # 정적 파일 위치
    template_folder="Frontend"     # HTML 파일 위치
)

# ----------------------------
# 기본 프롬프트 제공 (초기 로딩용)
# ----------------------------
@app.route("/prompts/default", methods=["GET"])
def get_default_prompts():
    return jsonify({
        "title": TITLE_GENERATION_PROMPT,
        "overview": OVERVIEW_PROMPT,
        "need": NEED_PROMPT,
        "suggestion": SUGGESTION_PROMPT,
        "ref1": OVERVIEW_ref_PROMPT,      # 🔥 키 이름 통일
        "ref2": reference2_PROMPT,
        "ref3": reference3_PROMPT,
        "ref4": reference4_PROMPT,
    })

# ----------------------------
# 키워드 배열 받아서 제목 생성 API
# ----------------------------
@app.route("/api/keywords", methods=["POST"])
def api_keywords():
    data = request.get_json()

    keywords = data.get("keywords", [])
    prompts = data.get("prompts")   # 🔥 웹에서 수정된 프롬프트

    if not prompts or "title" not in prompts:
        return jsonify({"error": "prompts.title 이 필요합니다"}), 400

    input_keywords = ", ".join(keywords)

    # 🔥 수정된 프롬프트 사용
    titles_text = generate_titles_from_keywords(
        input_keywords,
        prompts
    )

    return jsonify({
        "titles": titles_text
    })


# ----------------------------
# 제목 선택 → 전체 제안서 생성
# ----------------------------
@app.route("/api/proposal", methods=["POST"])
def api_proposal():
    data = request.get_json()

    title = data.get("title", "")
    keywords_string = data.get("keywords", "")
    prompts = data.get("prompts")   # 🔥 웹에서 수정된 프롬프트

    if not prompts:
        return jsonify({"error": "prompts가 전달되지 않았습니다"}), 400

    proposal_html = generate_proposal_and_hwpx(
        title,
        keywords_string,
        prompts
    )

    return jsonify({
        "ok": True,
        "proposal_html": proposal_html
    })



# ----------------------------
# HWPX 다운로드
# ----------------------------
@app.route("/download-hwpx", methods=["GET"])
def download_hwpx():
    title = request.args.get("title")
    if not title:
        abort(400, "title parameter required")

    path = os.path.join(OUTPUT_DIR, f"{title}.hwpx")

    if not os.path.exists(path):
        abort(404, f"HWPX 파일이 존재하지 않습니다: {path}")

    return send_file(
        path,
        as_attachment=True,
        download_name=f"{title}.hwpx",
        mimetype="application/octet-stream"
    )


# ----------------------------
# PPTX 다운로드
# ----------------------------

@app.route("/download-pptx", methods=["GET"])
def download_pptx():
    title = request.args.get("title")
    if not title:
        abort(400, "title parameter required")

    path = os.path.join(OUTPUT_DIR, f"{title}.pptx")

    print("📦 DOWNLOAD PPTX:", path)

    if not os.path.exists(path):
        abort(404, f"PPTX 파일이 존재하지 않습니다: {path}")

    return send_file(
        path,
        as_attachment=True,
        download_name=f"{title}.pptx",
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )




# ----------------------------
# 프론트엔드 화면 제공
# ----------------------------
@app.route("/")
def index():
    return send_from_directory("Frontend", "index.html")


# JS, CSS, 이미지 등 모든 정적 파일 제공
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("Frontend", path)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
