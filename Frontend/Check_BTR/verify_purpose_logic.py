import re

def _extract_purpose_from_title(title: str) -> str:
    # 1. Remove [ ... ]
    t = re.sub(r"\[[^\]]+\]", "", title)
    
    # 2. Remove YYMMDD (start of string or after space)
    # Support YYMMDD-DD or YYMMDD-YYMMDD ranges
    t = re.sub(r"\b\d{6}(?:-\d+)?\b", "", t)
    
    # 3. Remove '국내출장' ...
    if "국내출장" in t:
        t = t.split("국내출장")[0]
        
    return t.strip()

test_cases = [
    (
        "[스마트디지털] 260121-22 사이버보안 교육을 위한 국내출장보고서",
        "사이버보안 교육을 위한"
    ),
    (
        "[스마트디지털] 251218 스마트 디지털헬스케어 기업 대상 설명회 국내출장보고서",
        "스마트 디지털헬스케어 기업 대상 설명회"
    ),
    (
        "260121 단순 출장 국내출장",
        "단순 출장"
    ),
    (
        "260121-260122 기간 긴 출장 국내출장",
        "기간 긴 출장"
    )
]

print("Running Tests for _extract_purpose_from_title...")
all_passed = True
for inp, expected in test_cases:
    result = _extract_purpose_from_title(inp)
    print(f"\nInput   : {inp}")
    print(f"Result  : {result}")
    print(f"Expected: {expected}")
    
    if result == expected:
        print("✅ PASS")
    else:
        print("❌ FAIL")
        all_passed = False

if all_passed:
    print("\n🎉 All tests passed!")
else:
    print("\n⚠️ Some tests failed.")
