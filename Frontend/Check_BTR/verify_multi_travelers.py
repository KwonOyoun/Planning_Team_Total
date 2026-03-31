
import sys
import os

# Add project path
project_path = r"d:\OYUN\2.Research\2.SOTA\3.open_source\77.PlanningTeam\Check_BTR\Check_BTR"
sys.path.append(project_path)

import content_generator

# Use REAL template
template_path = os.path.join(project_path, "report_template.html")
with open(template_path, "r", encoding="utf-8") as f:
    real_template = f.read()

# Test Data (3 Travelers)
test_data = {
    "trip_period": "2025.01.20 ~ 2025.01.22",
    "destination": "군포시",
    "region": "군포", # Should hit 25,000 Near I
    "dept": ["AI팀", "AI팀", "기획팀"],
    "name": ["홍길동", "김철수", "이영희"],
    "position": ["팀장", "선임", "사원"],
    "trip_purpose": "테스트"
}

print("Generating HTML...")
generated_html = content_generator.generate_html(test_data, real_template)

# Checks
print("-" * 50)
target_rowspan = 'rowspan="4"'
print(f"Rowspan Updated? (Expected 4): { target_rowspan in generated_html }") # 1 Header + 3 travelers
print(f"Contains 홍길동? { '홍길동' in generated_html }")
print(f"Contains 김철수? { '김철수' in generated_html }")
print(f"Contains 이영희? { '이영희' in generated_html }")

# Check if expense calc is correct (25,000 for daily)
if '25,000' in generated_html:
    print("Expense 25,000 found!")
else:
    print("Expense 25,000 NOT found (Check calc logic)")

# Save for manual inspection
out_path = os.path.join(project_path, "debug_multi_traveler_output.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(generated_html)
print(f"Saved to {out_path}")
