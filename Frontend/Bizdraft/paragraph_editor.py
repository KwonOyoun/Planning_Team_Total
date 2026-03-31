# paragraph_editor.py

import xml.etree.ElementTree as ET
from .config import NS
import re

# ---------------------------------------------------
# 문단 생성
# ---------------------------------------------------
def create_paragraph(text, styleID, paraPrID, pid, charPrIDRef, bold_char="59"):
    """
    괄호() 안 텍스트만 Bold(run)로 생성하며,
    기존 create_paragraph의 모든 구조를 그대로 유지.
    """
    NS_HP = "{%s}" % NS['hp']
    p = ET.Element(f"{NS_HP}p")
    p.set("id", str(pid))
    p.set("paraPrIDRef", paraPrID)
    p.set("styleIDRef", styleID)
    p.set("pageBreak", "0")
    p.set("columnBreak", "0")
    p.set("merged", "0")

    # 괄호() 블록 기준 분할
    parts = re.split(r"(\([^)]*\))", text)

    for part in parts:
        if not part:
            continue

        # 괄호 안 → Bold
        if part.startswith("(") and part.endswith(")"):
            cp = bold_char
        else:
            cp = charPrIDRef  # 원래 스타일 유지

        run = ET.SubElement(p, f"{NS_HP}run")
        run.set("charPrIDRef", cp)

        t = ET.SubElement(run, f"{NS_HP}t")
        t.text = part

    return p


# ---------------------------------------------------
# "□ 필요성" 위치 찾기
# ---------------------------------------------------
def find_insert_index(paragraphs):
    for i, p in enumerate(paragraphs):
        if not p.tag.endswith("p"):
            continue

        for t in p.findall(".//{%s}t" % NS["hp"]):
            if t.text and "□ 필요성" in t.text:
                return i

    raise Exception("□ 필요성을 찾을 수 없습니다.")


# ---------------------------------------------------
# "2. 추진 배경 및 필요성" 위치 찾기
# ---------------------------------------------------
def find_insert_index_2(paragraphs):
    for i, p in enumerate(paragraphs):
        if not p.tag.endswith("p"):
            continue

        for t in p.findall(".//{%s}t" % NS["hp"]):
            if t.text and "2. 추진 배경 및 필요성" in t.text:
                return i

    raise Exception("'2. 추진 배경 및 필요성'을 찾을 수 없습니다.")


# ---------------------------------------------------
# "3. 사업 내용" 위치 찾기
# ---------------------------------------------------
def find_insert_index_3(paragraphs):
    for i, p in enumerate(paragraphs):
        if not p.tag.endswith("p"):
            continue

        for t in p.findall(".//{%s}t" % NS["hp"]):
            if t.text and "3. 사업 내용" in t.text:
                return i

    raise Exception("'3. 사업 내용'을 찾을 수 없습니다.")


# ---------------------------------------------------
# "4. 기대 효과" 위치 찾기
# ---------------------------------------------------
def find_insert_index_4(paragraphs):
    for i, p in enumerate(paragraphs):
        if not p.tag.endswith("p"):
            continue

        for t in p.findall(".//{%s}t" % NS["hp"]):
            if t.text and "4. 기대 효과" in t.text:
                return i

    raise Exception("'4. 기대 효과'을 찾을 수 없습니다.")


# ---------------------------------------------------
# "[목차] 3. 사업 내용" 위치 찾기
# ---------------------------------------------------
def find_insert_index_3_1(paragraphs):
    """
    템플릿 내 '3. 사업 내용'이 여러 번 등장할 경우
    → 가장 마지막(본문 시작)의 위치를 반환.
    """

    found = []

    for i, p in enumerate(paragraphs):
        if not p.tag.endswith("p"):
            continue

        for t in p.findall(".//{%s}t" % NS["hp"]):
            if t.text and "3. 사업 내용" in t.text:
                found.append(i)

    if not found:
        raise Exception("[목차] '3. 사업 내용'을 찾을 수 없습니다.")

    # 🔥 마지막 위치 반환
    return found[-1]


# ---------------------------------------------------
# 5. 기호와 텍스트 분리 저장
# ---------------------------------------------------
def split_symbol_and_text(text):
    symbols = []
    contents = []

    # 줄 단위로 분리
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for line in lines:
        # ㅇ, -, – 등 라벨 추출
        match = re.match(r"^(ㅇ|•|-|–)\s*(.*)", line)
        if match:
            symbol = match.group(1)
            content = match.group(2).strip()

            symbols.append(symbol)
            contents.append(content)

    return symbols, contents


# ---------------------------------------------------
# 필요성 항목 문단 추가(개요 이슈 생기면 여기)
# ---------------------------------------------------
def insert_need_paragraphs(root, insert_index, need_parts):

    TEXT_ITEMS = [
        (need_parts["a1"], "3", "43", "40"), # 개요 1
        (need_parts["a2"], "4", "45", "40"), # 개요 2
        (need_parts["a3"], "5", "46", "42"), # 개요 3
        (need_parts["b1"], "3", "43", "40"), # 개요 1
        (need_parts["b2"], "4", "45", "40"), # 개요 2
        (need_parts["b3"], "5", "46", "42"), # 개요 3
        (need_parts["c1"], "3", "43", "40"), # 개요 1
        (need_parts["c2"], "4", "45", "40"), # 개요 2
        (need_parts["c3"], "5", "46", "42"), # 개요 3
    ]

    offset = 1

    for idx, (txt, style, para, charPrID) in enumerate(TEXT_ITEMS):
        # 공백 줄(필요시 추가)
        if idx == 0:
            pid = 888000000 + idx * 100
            blank = create_paragraph("", "0", "41", pid, "43")
            root.insert(insert_index + offset, blank)
            offset += 1

        pid = 888000000 + idx
        new_p = create_paragraph(txt, style, para, pid, charPrID)
        root.insert(insert_index + offset, new_p)
        offset += 1


# ---------------------------------------------------
# 참고 문단 추가(개요 이슈 생기면 여기)
# ---------------------------------------------------
def insert_ref_paragraphs(root, insert_index, text):
    offset = 1
    ref_sources = []          # ← 출처 저장 리스트
    in_source_section = False # ← 출처 구간 여부

    # 줄 단위 분리
    lines = [l for l in text.split("\n") if l.strip()]

    for line in lines:
        clean = line.strip()

        # 🔥 출처 시작 감지
        if clean.startswith("출처"):
            in_source_section = True
            continue

        # 🔥 출처 구간이면 → 저장만 하고, 문단 삽입 중단
        if in_source_section:
            # "1. URL" 또는 "URL" 둘 다 처리
            m = re.match(r"^\d+\.\s*(.*)$", clean)
            if m:
                ref_sources.append(m.group(1).strip())
            else:
                ref_sources.append(clean)
            continue

        # -------------------------
        # 🔥 출처 이전 내용 구간 처리 (기존 코드 그대로)
        # -------------------------
        line = line.lstrip()  # 공백 제거
        match = re.match(r"^(ㅇ|-|\*)\s*(.*)", line)
        # match_index = re.match(r"^3\.\d+(?:\.\d+)*$", line.strip())

        if match:
            symbol = match.group(1)
            content = match.group(2).strip()

            # 스타일 구분
            if symbol == 'ㅇ':
                style = "3"
                para = "43"
                charPrID = "40"
                idx = 3
            elif symbol == '-':
                style = "4"
                para = "45"
                charPrID = "40"
                idx = 4
            elif symbol == '*':
                style = "5"
                para = "46"
                charPrID = "42"
                idx = 5

            # 공백 줄
            pid = 355000000 + (offset + insert_index) * (1000 + idx) + 1
            blank = create_paragraph("", "0", "41", pid, "43")
            root.insert(insert_index + offset, blank)
            offset += 1

            # 글 줄
            pid = 255000000 + (offset + insert_index) * (1000 + idx)
            new_p = create_paragraph(content, style, para, pid, charPrID)
            root.insert(insert_index + offset, new_p)
            offset += 1

        # # 목차
        # elif match_index:
        #     style = "0"
        #     para = "0"
        #     charPrID = "51"
        #     idx = 5

        #     # 공백 줄
        #     pid = 5500000000 + (offset + insert_index) * (1000 + idx) + 1
        #     blank = create_paragraph("", "0", "41", pid, "43")
        #     root.insert(insert_index + offset, blank)
        #     offset += 1

    # 최종적으로 출처 리스트 반환
    return ref_sources

# ---------------------------------------------------
# 제목 및 사업 개요 텍스트 수정
# ---------------------------------------------------
def modify_text_contents(root, title, purpose, content, suggestion):
    title_flag = True

    for elem in root.iter():
        if elem.text is None:
            continue

        # 제목 수정
        if "[제목]" in elem.text:

            if title_flag:
                elem.text = f"[신규] {title}"
                title_flag = False
            else:
                re_title = re.sub(r"\((R&D|비R&D)\)", "", title).strip()
                elem.text = re_title

        # 사업 개요
        if '사업목적 :' in elem.text:
            elem.text += purpose
        elif '사업기간 :' in elem.text:
            elem.text += "2026 ~ 2030년(5년)"
        elif '사업내용 :' in elem.text:
            elem.text += content

        # 건의사항
        if "사업에 국비 반영" in elem.text:
            re_title = re.sub(r"\((R&D|비R&D)\)", "", title).strip() # 제목에서 (R&D), (비R&D) 제거
            elem.text = suggestion + ' "' + re_title + '" ' + elem.text


def modify_text_contents_ref(root, title, overview, benef):

    for elem in root.iter():
        if elem.text is None:
            continue

        # 제목 수정
        if "[제목]" in elem.text:
            elem.text += title
        # 사업 개요
        elif '(사업개요) ' in elem.text:
            elem.text += overview
        elif '(사업기간) ' in elem.text:
            elem.text += "2026 ~ 2030년(5년)"
        elif '(수 혜 자) ' in elem.text:
            elem.text += benef


# ------------------------------------------------------------------------
# 목차 폰트 및 글자 크기 수정 함수들
# ------------------------------------------------------------------------





