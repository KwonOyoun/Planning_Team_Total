
import json

# Mocking the part of content_generator.py we want to test
def calc_expenses(dest_str, region_str=""):
    # 1. 지역 구분 정의
    near_1 = ["광명시", "고양시", "과천시", "구리시", "군포시", "김포시", "부천시", "성남시", "수원시", "시흥시", "안산시", "안양시", "의왕시", "인천시", "하남시"]
    near_2 = ["가평군", "강화군", "광주시", "남양주시", "동두천시", "안성시", "양주시", "양평군", "여주시", "연천군", "오산시", "용인시", "의정부시", "이천시", "파주시", "평택시", "포천시", "화성시"]
    
    # Simulate the issue: currently logic only looks at dest_str
    # We will modify this function in the actual file, but for reproduction we mirror the current state
    # Wait, to strictly reproduce via import is better, but since the file has no standalone export and is inside a function, 
    # I will copy the logic PRE-FIX to show it fails, then POST-FIX to show it works.
    # Actually, allow me to define the Current Logic as it exists in the file.
    
    # --- EXISTING LOGIC START ---
    dest_clean = dest_str.replace(" ", "")
    
    # Defaults
    traffic = {"detail": f"서울↔{dest_str}", "price": "실비"}
    daily = {"detail": "1일", "price": "0"}
    food = {"detail": "1일", "price": "0"}
    
    # The Issue: It checks dest_str only
    check_target = dest_str 
    
    if "서울시" in check_target or "서울시" in dest_clean:
        daily["price"] = "20,000"
        food["price"] = "0"
    elif any(city in check_target for city in near_1):
        daily["price"] = "25,000"
        food["price"] = "0"
    elif any(city in check_target for city in near_2):
        daily["price"] = "30,000"
        food["price"] = "0"
    else:
        daily["price"] = "20,000"
        food["price"] = "10,000"
        
    return daily["price"], food["price"]

def test_case(dest, region, expected_daily, expected_food):
    d, f = calc_expenses(dest, region)
    print(f"Input: Destination='{dest}', Region='{region}'")
    print(f"Result: Daily='{d}', Food='{f}'")
    print(f"Expected: Daily='{expected_daily}', Food='{expected_food}'")
    
    if d == expected_daily and f == expected_food:
        print("PASS")
    else:
        print("FAIL")
    print("-" * 20)

if __name__ == "__main__":
    print("Testing Current Logic (Should FAIL for KTC/Gunpo cases)")
    # Case 1: KTC (Gunpo) - Current logic sees 'KTC', doesn't find '군포시', falls back to else (20000/10000)
    # Expected: 25,000 (Near I), 0
    test_case("KTC", "군포시", "25,000", "0")
    
    # Case 2: Explicit Gunpo
    test_case("군포시", "군포시", "25,000", "0")
