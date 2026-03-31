# config.py
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise Exception("🚨 환경 변수 OPENAI_API_KEY가 설정되지 않았습니다!")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

if not GOOGLE_API_KEY:
    print("⚠ 환경 변수 GOOGLE_API_KEY가 없습니다. 구글 검색 기능이 제한될 수 있습니다.")

if not GOOGLE_CX:
    print("⚠ 환경 변수 GOOGLE_CX가 없습니다. 구글 검색 기능이 제한될 수 있습니다.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HWPX_PATH = os.path.join(BASE_DIR, "template", "template.hwpx")
PPTX_PATH = os.path.join(BASE_DIR, "template", "template.pptx")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp_hwpx")

NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
}
