# config.py
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise Exception("🚨 환경 변수 OPENAI_API_KEY가 설정되지 않았습니다!")


HPWX_PATH = "template/template.hwpx"
TEMP_DIR = "temp_hwpx"
OUTPUT_PATH = "modified.hwpx"

NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
}
