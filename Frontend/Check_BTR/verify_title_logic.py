
import re

def _build_new_title(old_title: str) -> str:
    new_title = old_title.strip()
    
    # 1. Remove duration info e.g. (1회/8시간) or (6시간/1회)
    # Regex: `(digit+ space? (회|시간) / digit+ space? (회|시간))` inside parentheses at the end
    new_title = re.sub(r"\s*\(\d+\s*(?:회|시간)\s*/\s*\d+\s*(?:회|시간)\)$", "", new_title)
    
    # 2. Logic: "국내출장" -> "국내출장보고서"
    if new_title.endswith("국내출장"):
        new_title += "보고서"
    
    # 3. Handle cases where "국내출장" was missing (e.g. just "Meeting")
    # If it doesn't have "보고서" yet, try to make it "국내출장보고서"
    if "보고서" not in new_title:
        new_title = new_title.replace("신청서", "결과보고서").replace("계획서", "결과보고서").replace("품의서", "결과보고서")
        
        # Still no '보고서'? 
        if "보고서" not in new_title:
             # Check if it already has "국내출장" (handled by step 2, but maybe it was inside text?)
             if "국내출장" in new_title:
                 new_title += " 결과보고서" # Fallback if "국내출장" exists but not at end?
             else:
                 # User request: replace duration with "국내출장보고서" implies appending it
                 new_title += " 국내출장보고서"
             
    return new_title.strip()

test_cases = [
    (
        "[스마트디지털] 251218 스마트 디지털헬스케어 기업 대상 사업 설명회 국내출장(1회/8시간)",
        "[스마트디지털] 251218 스마트 디지털헬스케어 기업 대상 사업 설명회 국내출장보고서"
    ),
    (
        "[협회] 260113 식약처 AX-Sprint 300 사업 기획 회의(6시간/1회)",
        "[협회] 260113 식약처 AX-Sprint 300 사업 기획 회의 국내출장보고서"
    ),
    (
        "Simple Trip 국내출장",
        "Simple Trip 국내출장보고서"
    ),
    (
        "No Explicit Trip Type",
        "No Explicit Trip Type 국내출장보고서"
    ),
    (
        "Existing Report 국내출장보고서",
        "Existing Report 국내출장보고서"
    ),
    (
        "Mixed Order (3회 / 12시간)",
        "Mixed Order 국내출장보고서"
    )
]

print("Running Tests for _build_new_title (Advanced)...")
all_passed = True
for inp, expected in test_cases:
    result = _build_new_title(inp)
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
