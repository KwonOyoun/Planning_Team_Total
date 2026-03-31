# hwpx_generate.py
import zipfile
import os
import re
import copy
import xml.etree.ElementTree as ET
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp_hwpx")

TEMPLATE_PATH = os.path.join(BASE_DIR, "template.hwpx")

NS = {
    "ns1": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
}

# ===============================
# HWPX 기본 처리
# ===============================
def unzip_hwpx(path):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    with zipfile.ZipFile(path, 'r') as z:
        z.extractall(TEMP_DIR)

def load_xml():
    tree = ET.parse(f"{TEMP_DIR}/Contents/section0.xml")
    return tree, tree.getroot()

def save_xml(tree):
    tree.write(f"{TEMP_DIR}/Contents/section0.xml", encoding="utf-8")

def zip_hwpx(output_path):
    with zipfile.ZipFile(output_path, 'w') as z:
        for folder, _, files in os.walk(TEMP_DIR):
            for file in files:
                full = os.path.join(folder, file)
                arc = os.path.relpath(full, TEMP_DIR)
                z.write(full, arc)

# ===============================
# 유틸
# ===============================
def format_datetime_korean(datetime_local: str) -> str:
    """
    '2025-12-23T13:30' → '2025년 12월 23일 13:30'
    """
    try:
        dt = datetime.strptime(datetime_local, "%Y-%m-%dT%H:%M")
        return f"{dt.year}년 {dt.month}월 {dt.day}일 {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return datetime_local

def find_tr_by_text(root, text):
    for tr in root.findall(".//ns1:tr", NS):
        for t in tr.findall(".//ns1:t", NS):
            if t.text == text:
                return tr
    return None

def find_parent_tbl(root, target_tr):
    for tbl in root.findall(".//ns1:tbl", NS):
        for tr in tbl.findall("ns1:tr", NS):
            if tr is target_tr:
                return tbl
    return None

def format_datetime_range_korean(start_local: str, end_local: str) -> str:
    """
    '2025-12-29T10:30', '2025-12-29T12:30'
    -> '2025년 12월 29일 10:30 ~ 12:30'
    """
    if not start_local or not end_local:
        return ""

    try:
        s = datetime.strptime(start_local, "%Y-%m-%dT%H:%M")
        e = datetime.strptime(end_local, "%Y-%m-%dT%H:%M")

        date_part = f"{s.year}년 {s.month}월 {s.day}일"
        start_time = f"{s.hour:02d}:{s.minute:02d}"
        end_time = f"{e.hour:02d}:{e.minute:02d}"

        return f"{date_part} {start_time} ~ {end_time}"
    except Exception:
        # 파싱 실패 시 원문이라도 반환(디버깅 용이)
        return f"{start_local} ~ {end_local}"


# ===============================
# 회의내용 멀티라인 안전 치환
# ===============================
def replace_minutes_body(root, minutesBody):
    lines = minutesBody.split("\n")

    for tr in root.findall(".//ns1:tr", NS):
        for tc in tr.findall("ns1:tc", NS):
            t = tc.find(".//ns1:t", NS)
            if t is not None and t.text == "[회의내용]":

                sublist = tc.find("ns1:subList", NS)
                p_list = sublist.findall("ns1:p", NS)

                # 기존 p 제거
                for p in p_list:
                    sublist.remove(p)

                # 새 문단 생성
                for line in lines:
                    # ✅ 하이픈 줄이면 들여쓰기 2칸
                    if line.lstrip().startswith("-"):
                        line = "  " + line.lstrip()

                    p = ET.SubElement(sublist, f"{{{NS['ns1']}}}p", {
                        "id": "0",
                        "paraPrIDRef": "25",
                        "styleIDRef": "0",
                        "pageBreak": "0",
                        "columnBreak": "0",
                        "merged": "0",
                    })
                    run = ET.SubElement(p, f"{{{NS['ns1']}}}run", {
                        "charPrIDRef": "14"
                    })
                    t2 = ET.SubElement(run, f"{{{NS['ns1']}}}t")
                    t2.text = line


                return

# ===============================
# 참석자 테이블 채우기
# ===============================
def fill_participants(root, participants):
    # 1. 내부 / 외부 분리
    inner = [p for p in participants if "범부처" in p["department"]]
    outer = [p for p in participants if p not in inner]

    base_inner_tr = find_tr_by_text(root, "내부 참석자")
    base_outer_tr = find_tr_by_text(root, "외부 참석자")

    if base_inner_tr is None or base_outer_tr is None:
        raise ValueError("내부/외부 참석자 기준 tr 없음")

    tbl = find_parent_tbl(root, base_inner_tr)
    tr_list = list(tbl)

    base_inner_idx = tr_list.index(base_inner_tr)
    # base_outer_idx = tr_list.index(base_outer_tr)

    # ===============================
    # 내부 참석자
    # ===============================
    inner_trs = []
    for i, p in enumerate(inner):
        tr = base_inner_tr if i == 0 else copy.deepcopy(base_inner_tr)
        tcs = tr.findall("ns1:tc", NS)

        tcs[0].find(".//ns1:t", NS).text = "내부 참석자" if i == 0 else ""
        tcs[1].find(".//ns1:t", NS).text = p["department"]
        tcs[2].find(".//ns1:t", NS).text = p["name"]
        tcs[3].find(".//ns1:t", NS).text = p["position"]

        inner_trs.append(tr)

    # rowSpan 설정
    if inner_trs:
        label_tc = inner_trs[0].find("ns1:tc", NS)
        label_tc.find("ns1:cellSpan", NS).set("rowSpan", str(len(inner_trs)))

        # 🔥 rowSpan 아래 행에서 colAddr=0 tc 제거
        for tr in inner_trs[1:]:
            tc0 = tr.findall("ns1:tc", NS)[0]
            tr.remove(tc0)

    # 기존 내부 tr 제거 후 삽입
    tbl.remove(base_inner_tr)
    for i, tr in enumerate(inner_trs):
        tbl.insert(base_inner_idx + i, tr)

    # ===============================
    # 외부 참석자
    # ===============================
    outer_insert_idx = base_inner_idx + len(inner_trs)
    tbl.remove(base_outer_tr)

    outer_trs = []
    for i, p in enumerate(outer):
        tr = copy.deepcopy(base_outer_tr)
        tcs = tr.findall("ns1:tc", NS)

        tcs[0].find(".//ns1:t", NS).text = "외부 참석자" if i == 0 else ""
        tcs[1].find(".//ns1:t", NS).text = p["department"]
        tcs[2].find(".//ns1:t", NS).text = p["name"]
        tcs[3].find(".//ns1:t", NS).text = p["position"]

        outer_trs.append(tr)

    if outer_trs:
        label_tc = outer_trs[0].find("ns1:tc", NS)
        label_tc.find("ns1:cellSpan", NS).set("rowSpan", str(len(outer_trs)))

        # 🔥 rowSpan 아래 행 정리
        for tr in outer_trs[1:]:
            tc0 = tr.findall("ns1:tc", NS)[0]
            tr.remove(tc0)

    for i, tr in enumerate(outer_trs):
        tbl.insert(outer_insert_idx + i, tr)

    # ===============================
    # rowAddr 재정렬
    # ===============================
    for r_idx, tr in enumerate(tbl.findall("ns1:tr", NS)):
        for tc in tr.findall("ns1:tc", NS):
            cell_addr = tc.find("ns1:cellAddr", NS)
            if cell_addr is not None:
                cell_addr.set("rowAddr", str(r_idx))

    # ===============================
    # 🔥 rowCnt 재설정 (필수)
    # ===============================
    tbl.set("rowCnt", str(len(tbl.findall("ns1:tr", NS))))



# ===============================
# 메인 적용 함수
# ===============================
def apply_meeting_minutes_to_section0(
    root,
    projectName,
    meetingName,
    meetingDate,
    meetingLocation,
    participants,
    minutesBody,
    author,
):
    replace_map = {
        "[사업명]": projectName,
        "[회의제목]": meetingName,
        "[회의일시]": meetingDate,
        "[회의장소]": meetingLocation,
        "[작성자]": author,
    }

    for t in root.findall(".//hp:t", NS):
        if t.text:
            for k, v in replace_map.items():
                if k in t.text:
                    t.text = t.text.replace(k, v)

    replace_minutes_body(root, minutesBody)
    fill_participants(root, participants)


def sanitize_filename(name: str) -> str:
    """
    파일명에 사용할 수 없는 문자 제거
    """
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()

def generate_hwpx_file(meeting_data):
    print("🔥 generate_hwpx_file CALLED")
    print("DATA:", meeting_data)
    # ---------------------------
    # 1️⃣ output 디렉토리 보장
    # ---------------------------
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    # ---------------------------
    # 2️⃣ 파일명용 날짜 → YYMMDD
    #    (meetingStart 우선, 없으면 meetingDate)
    # ---------------------------
    raw_start = meeting_data.get("meetingStart", "")  # ✅ 추가
    raw_end = meeting_data.get("meetingEnd", "")      # ✅ 추가
    raw_date = meeting_data.get("meetingDate", "")    # (구버전 호환)

    # 파일명 날짜는 시작시간 기준으로 뽑는 게 자연스러움
    date_source = raw_start or raw_date
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_source)

    if m:
        yy = m.group(1)[2:]
        mm = m.group(2)
        dd = m.group(3)
        date_prefix = f"{yy}{mm}{dd}"
    else:
        date_prefix = "000000"

    # ---------------------------
    # 3️⃣ 회의일시 → HWPX 표시용 포맷
    #    (start/end 있으면 범위 포맷, 없으면 단일 포맷)
    # ---------------------------
    if raw_start and raw_end:
        meeting_date_text = format_datetime_range_korean(raw_start, raw_end)
    else:
        meeting_date_text = format_datetime_korean(raw_date)

    # ---------------------------
    # 4️⃣ 회의명 정리
    # ---------------------------
    meeting_name = sanitize_filename(
        meeting_data.get("meetingName", "회의록")
    )

    # ---------------------------
    # 5️⃣ 최종 파일 경로
    # ---------------------------
    filename = f"{date_prefix} {meeting_name}.hwpx"
    output_path = os.path.join(output_dir, filename)

    # ---------------------------
    # 6️⃣ HWPX 생성
    # ---------------------------
    unzip_hwpx(TEMPLATE_PATH)
    tree, root = load_xml()

    apply_meeting_minutes_to_section0(
        root,
        meeting_data["projectName"],
        meeting_data["meetingName"],
        meeting_date_text,
        meeting_data["meetingLocation"],
        meeting_data["participants"],
        meeting_data["minutesBody"],
        meeting_data.get("author", ""),
    )

    print("HWPX 생성 완료!")

    print("ZIP OUTPUT PATH:", os.path.abspath(output_path))
    print("TEMP_DIR EXISTS:", os.path.exists(TEMP_DIR))
    print("TEMP_DIR FILES:", os.listdir(TEMP_DIR))

    save_xml(tree)
    zip_hwpx(output_path)

    return output_path

