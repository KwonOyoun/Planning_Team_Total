
import sys
import os

# Add the directory to path so we can import content_generator
sys.path.append(r"d:\OYUN\2.Research\2.SOTA\3.open_source\77.PlanningTeam\Check_BTR\Check_BTR")

import content_generator

def verify():
    # Test Data: 'KTC' (Gunpo)
    data = {
        'trip_period': '2026-01-13(화) ~ 2026-01-13(화)',
        'destination': 'KTC',
        'dept': '기획1팀',
        'name': ['권오윤'],
        'position': ['주임연구원'],
        'region': '군포시',
        'trip_purpose': 'Test Purpose'
    }
    
    print("Generating script with data:", data)
    js_script = content_generator.generate_fill_script(data)
    
    # We expect 'KTC' with 'region'='군포시' to be Near I -> 25,000
    # The generated JS has a JSON blob with expenses. 
    # Let's check for the presence of the correct amount "25,000" in the string.
    
    if '"price": "25,000"' in js_script:
        print("SUCCESS: Found expected price '25,000'")
    elif '"price": "20,000"' in js_script:
        print("FAIL: Found default price '20,000' (Fix not working)")
    else:
        print("FAIL: Could not find price string in script.")
        
    print("-" * 20)
    # Print a snippet to be sure
    start_idx = js_script.find("expenses_json")
    if start_idx != -1:
        print("Snippet:", js_script[start_idx:start_idx+300])

if __name__ == "__main__":
    verify()
