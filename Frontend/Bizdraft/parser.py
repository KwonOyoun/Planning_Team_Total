# parser.py

import zipfile
import os
import xml.etree.ElementTree as ET
from .config import NS, TEMP_DIR
import re

def unzip_hwpx(path):
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

def parse_overview(overview_text):
    purpose = ""
    content = ""

    # 사업 목적
    purpose_match = re.search(r"■ 사업 목적\s*([\s\S]*?)■ 사업 내용", overview_text)
    if purpose_match:
        purpose = purpose_match.group(1).strip().lstrip("ㅇ").strip()

    # 사업 내용
    content_match = re.search(r"■ 사업 내용\s*([\s\S]*)", overview_text)
    if content_match:
        content = content_match.group(1).strip().lstrip("ㅇ").strip()

    return purpose, content

def parse_need(need_text):
    # (1), (2), (3) 세 구간으로 나누기
    blocks = re.split(r"\[\d\)", need_text)
    # blocks[0]은 빈 문자열, blocks[1], blocks[2], blocks[3]이 실제 내용

    a_block = blocks[1] if len(blocks) > 1 else ""
    b_block = blocks[2] if len(blocks) > 2 else ""
    c_block = blocks[3] if len(blocks) > 3 else ""

    def extract_three_items(block):
        # ㅇ 첫 문장
        m1 = re.search(r"ㅇ(.*?)(?:\n|$)", block)
        # - 근거
        m2 = re.search(r"-(.*?)(?:\n|$)", block)
        # * 실제현황/통계
        m3 = re.search(r"\*(.*?)(?:\n|$)", block)

        return (
            m1.group(1).strip() if m1 else "",
            m2.group(1).strip() if m2 else "",
            m3.group(1).strip() if m3 else "",
        )

    a1, a2, a3 = extract_three_items(a_block)
    b1, b2, b3 = extract_three_items(b_block)
    c1, c2, c3 = extract_three_items(c_block)

    return {
        "a1": a1, "a2": a2, "a3": a3,
        "b1": b1, "b2": b2, "b3": b3,
        "c1": c1, "c2": c2, "c3": c3
    }