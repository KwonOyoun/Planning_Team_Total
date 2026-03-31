import json

# ---------------------------------------------------------
# 1. HTML 템플릿 (3명 이상 확장을 위한 마커 포함)
# ---------------------------------------------------------
TEMPLATE_HTML = """
<center>
	<div class="title" style="font-family:'맑은 고딕'; font-size:12pt; font-weight:bold; margin-bottom:5px; text-align:left; width:98%; margin:0 auto;">□ 출장 개요</div>
	<table cellpadding="0" cellspacing="0" style="font-size:10pt;border-collapse:collapse;width:98%;margin:0px auto;table-layout:fixed;word-break:normal;">
		<colgroup>
		<col style="width:126px;" />
		<col style="width:290px;" />
		<col style="width:200px;" />
		<col style="width:200px;" />
		</colgroup>
		<tbody>
			<tr style="height:38px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">출장기간</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" colspan="3">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{TRIP_PERIOD}}</span>
				</td>
			</tr>
			<tr style="height:38px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">출장지</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" colspan="3">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{DESTINATION}}</span>
				</td>
			</tr>
			<tr>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed" rowspan="{{TRAVELER_ROWSPAN}}">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">출장자</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">소속</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">성함</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">직책/직위</span>
				</td>
			</tr>
            <!-- ROW_TEMPLATE_START -->
			<tr>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{DEPT}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{NAME}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{POSITION}}</span>
				</td>
			</tr>
            <!-- ROW_TEMPLATE_END -->
			<tr>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed" rowspan="2">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">외부 참석자</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
			</tr>
			<tr>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
			</tr>
			<tr style="height:38px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">출장목적</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; text-align:left;" colspan="3">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{TRIP_PURPOSE}}</span>
				</td>
			</tr>
			<tr style="height:135px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">세부내용<br>(외부 회의내용)</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; text-align:left; vertical-align:top;" colspan="3">
					<br>
				</td>
			</tr>
			<tr style="height:36px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">결론</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; text-align:left;" colspan="3">
                    <br>
				</td>
			</tr>
			<tr style="height:37px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">특이사항</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; text-align:left;" colspan="3">
                    <br>
				</td>
			</tr>
			<tr>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" colspan="4">
					<span style="font-family:'맑은 고딕'; font-size:9pt;"><i>※ 세부내용은 출장자들의 출장업무 및 외부 회의내용(안건별 참석자 각각의 의견 등)을 정확히 파악할 수 있도록 작성</i></span>
				</td>
			</tr>
		</tbody>
	</table>
	<br><br>

	<div class="title" style="font-family:'맑은 고딕'; font-size:12pt; font-weight:bold; margin-bottom:5px; text-align:left; width:98%; margin:0 auto;">□ 출장비 산출내역</div>
    <!-- EXPENSE_TEMPLATE_START -->
	<table cellpadding="0" cellspacing="0" style="font-size:10pt;border-collapse:collapse;width:96%;margin:0px auto;table-layout:fixed;word-break:normal;">
		<colgroup>
		<col style="width:126px;" />
		<col style="width:65px;" />
		<col style="width:215px;" />
		<col style="width:200px;" />
		<col style="width:200px;" />
		</colgroup>
		<tbody>
			<tr style="height:10px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed" rowspan="2">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">출장자</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center" colspan="2">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">소속</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">성함</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">직책/직위</span>
				</td>
			</tr>
			<tr style="height:15px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" colspan="2">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{DEPT}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{NAME}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{POSITION}}</span>
				</td>
			</tr>
			<tr style="height:10px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center" bgcolor="#ededed" rowspan="6">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">산출내역</span>
				</td>
				<td style="border:1px solid #000; padding:1px 10px; background-color:#f2f2f2;" align="center" colspan="2">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">항목</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">금액</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">비고</span>
				</td>
			</tr>
			<tr style="height:10px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">교통비</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_TRAFFIC_DETAIL}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="right">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_TRAFFIC_PRICE}}원</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">증빙서류 첨부</span>
				</td>
			</tr>
			<tr style="height:10px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">일비</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_DAILY_DETAIL}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="right">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_DAILY_PRICE}}원</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
			</tr>
			<tr style="height:10px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">식비</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_FOOD_DETAIL}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="right">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_FOOD_PRICE}}원</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
			</tr>
			<tr style="height:10px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">숙박비</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_HOTEL_DETAIL}}</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="right">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_HOTEL_PRICE}}원</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
			</tr>
			<tr style="height:35px;">
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px; background-color:#f2f2f2;" align="center" colspan="2">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">합계</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="right">
					<span style="font-family:'맑은 고딕'; font-size:10pt;">{{EXP_TOTAL}}원</span>
				</td>
				<td style="border:1px solid #000; font-size:11pt; padding:1px 10px;" align="center">
					<br>
				</td>
			</tr>
		</tbody>
	</table>
    <br>
    <!-- EXPENSE_TEMPLATE_END -->
</center>
"""

# ---------------------------------------------------------
# 2. 비용 산출 로직
# ---------------------------------------------------------

from datetime import datetime
import re

def calculate_days(period_str):
    try:
        # Expected format: "2026-01-20(Mon) ~ 2026-01-22(Wed)"
        # Regex to find dates YYYY-MM-DD
        dates = re.findall(r"(\d{4}-\d{2}-\d{2})", period_str)
        if len(dates) >= 2:
            start_date = datetime.strptime(dates[0], "%Y-%m-%d")
            end_date = datetime.strptime(dates[1], "%Y-%m-%d")
            diff = (end_date - start_date).days
            return diff + 1 if diff >= 0 else 1
        elif len(dates) == 1:
            return 1
    except Exception as e:
        print(f"[DEBUG] Date Parse Error: {e}")
    return 1

def calc_expenses(dest_str, region_str="", days=1):
    near_1 = ["광명", "고양", "과천", "구리", "군포", "김포", "부천", "성남", "수원", "시흥", "안산", "안양", "의왕", "인천", "하남"]
    near_2 = ["가평", "강화", "광주", "남양주", "동두천", "안성", "양주", "양평", "여주", "연천", "오산", "용인", "의정부", "이천", "파주", "평택", "포천", "화성"]
    
    dest_clean = dest_str.replace(" ", "")
    check_target = (region_str or "") + " " + dest_str
    
    # [수정 1] 교통비 상세: 목적지(dest_str) 대신 지역(region_str) 사용
    display_region = region_str if region_str else dest_str
    traffic = {"detail": f"서울↔{display_region}", "price": "실비"}

    daily_price_val = 0
    food_price_val = 0
    
    if "서울" in check_target or "서울" in dest_clean:
        daily_price_val = 20000
        food_price_val = 0
        traffic["detail"] = "서울 시내"
        traffic["price"] = "실비"
    elif any(city in check_target for city in near_1):
        daily_price_val = 25000
        food_price_val = 0
    elif any(city in check_target for city in near_2):
        daily_price_val = 30000
        food_price_val = 0
    else:
        daily_price_val = 20000
        food_price_val = 30000
    
    # [수정 3] 일수(days) 반영
    daily = {
        "detail": f"{days}일", 
        "price": f"{daily_price_val * days:,}"
    }
    food = {
        "detail": f"{days}일" if food_price_val > 0 else "제공", 
        "price": f"{food_price_val * days:,}"
    }
    hotel = {"detail": "", "price": ""}
    
    def parse_price(p):
        clean_p = str(p).replace(",", "").strip()
        if not clean_p or not clean_p.replace("-", "").isdigit(): return 0
        return int(clean_p)
        
    # [수정 2] 합계 금액 서식 수정 (콤마 적용)
    # traffic["price"] contains text "실비" sometimes, so ignore it for sum if not numeric
    sum_val = parse_price(daily["price"]) + parse_price(food["price"])
    # If traffic price was numeric (though currently '실비'), add it? usually it's reimbursed based on receipt. 
    # Current logic only sums daily + food consistent with previous code.
    
    total_str = f"{sum_val:,}" 

    return {
        "traffic": traffic,
        "daily": daily,
        "food": food,
        "hotel": hotel,
        "total": total_str
    }

# ---------------------------------------------------------
# 3. HTML 생성 로직 (Main)
# ---------------------------------------------------------
def generate_html(data, template_html=None):
    # 템플릿이 전달되지 않았다면 파일 상단의 기본 템플릿 사용
    if not template_html:
        template_html = TEMPLATE_HTML

    dept = data.get("dept", "")
    name = data.get("name", "")
    position = data.get("position", "")
    destination = data.get("destination", "")
    region = data.get("region", "")
    period = data.get("trip_period", "")
    trip_purpose = data.get("trip_purpose", "")

    print(f"[DEBUG] generate_html data keys: {list(data.keys())}")
    print(f"[DEBUG] generate_html name: {name}")

    # 리스트 정규화
    def ensure_list(val):
        if isinstance(val, list): return val
        return [val] if val else []

    name_list = ensure_list(name)
    count = len(name_list) # 인원 수 계산
    
    # 2026-01-20: 데이터가 없어도 테이블이 깨지지 않도록 최소 1개의 빈 행 보장
    if count == 0:
        count = 1
        name_list = [""]
        dept_list = [""]
        position_list = [""]
    else:
        dept_list = ensure_list(dept)
        if isinstance(dept, str) and dept: dept_list = [dept] * count
        elif len(dept_list) == 1: dept_list = dept_list * count
        
        position_list = ensure_list(position)
        if len(position_list) == 1: position_list = position_list * count

    # 1. 기본 정보 치환
    # [수정] 출장목적에서 날짜 접두사 제거 강화
    # 예: "[SWMD] 251110-11 식약처..." -> "식약처..."
    # 예: "260120 아랍헬스..." -> "아랍헬스..."
    clean_purpose = trip_purpose
    try:
        # 1. [] 괄호 및 내용 제거 (옵션)
        # 2. 날짜 패턴 (6자리 숫자 + 옵션(-숫자)) 제거
        # 3. 구분자 (공백, -, _) 제거
        clean_purpose = re.sub(r'^(?:\[.*?\]\s*)?\d{6}(?:-\d{1,6})?\s*[-_]?\s*', '', trip_purpose).strip()
    except Exception as e:
        print(f"[DEBUG] Trip Purpose Cleaning Error: {e}")

    html = template_html
    html = html.replace("{{TRIP_PERIOD}}", period)
    html = html.replace("{{DESTINATION}}", destination)
    html = html.replace("{{TRIP_PURPOSE}}", clean_purpose)

    # Calculate Days
    days = calculate_days(period)
    print(f"[DEBUG] Calculated days: {days} from period: {period}")

    # 2. 출장자 목록 (Row 반복)
    # [수정] 아래 마커 값이 채워져 있어야 정상 작동합니다!
    row_start_marker = "<!-- ROW_TEMPLATE_START -->"
    row_end_marker = "<!-- ROW_TEMPLATE_END -->"
    
    if row_start_marker in html and row_end_marker in html:
        s_idx = html.find(row_start_marker) + len(row_start_marker)
        e_idx = html.find(row_end_marker)
        row_tpl = html[s_idx:e_idx]
        
        # Strip potential whitespace or newlines to ensure clean repetition
        # But be careful not to strip internal indentation if it matters for readability
        
        rows_html = ""
        for i in range(count):
            r = row_tpl
            r = r.replace("{{DEPT}}", dept_list[i] if i < len(dept_list) else "")
            r = r.replace("{{NAME}}", name_list[i] if i < len(name_list) else "")
            r = r.replace("{{POSITION}}", position_list[i] if i < len(position_list) else "")
            rows_html += r
        
        pre = html[:html.find(row_start_marker)]
        post = html[html.find(row_end_marker) + len(row_end_marker):]
        html = pre + rows_html + post
        
        # ROWSPAN 계산 (출장자 헤더)
        # 1(헤더) + count(인원수)
        html = html.replace("{{TRAVELER_ROWSPAN}}", str(1 + count))

    # 3. 출장비 내역 (테이블 반복)
    # [수정] 여기도 마커 값이 채워져 있어야 합니다!
    exp_start_marker = "<!-- EXPENSE_TEMPLATE_START -->"
    exp_end_marker = "<!-- EXPENSE_TEMPLATE_END -->"
    
    if exp_start_marker in html and exp_end_marker in html:
        s_idx = html.find(exp_start_marker) + len(exp_start_marker)
        e_idx = html.find(exp_end_marker)
        exp_tpl = html[s_idx:e_idx]
        
        exps_html = ""
        for i in range(count):
            cur_name = name_list[i] if i < len(name_list) else ""
            cur_dept = dept_list[i] if i < len(dept_list) else ""
            cur_pos = position_list[i] if i < len(position_list) else ""
            
            # Pass calculated days
            exp_data = calc_expenses(destination, region, days)
            
            t = exp_tpl
            t = t.replace("{{DEPT}}", cur_dept)
            t = t.replace("{{NAME}}", cur_name)
            t = t.replace("{{POSITION}}", cur_pos)
            
            t = t.replace("{{EXP_TRAFFIC_DETAIL}}", exp_data['traffic']['detail'])
            t = t.replace("{{EXP_TRAFFIC_PRICE}}", exp_data['traffic']['price'])
            t = t.replace("{{EXP_DAILY_DETAIL}}", exp_data['daily']['detail'])
            t = t.replace("{{EXP_DAILY_PRICE}}", exp_data['daily']['price'])
            t = t.replace("{{EXP_FOOD_DETAIL}}", exp_data['food']['detail'])
            t = t.replace("{{EXP_FOOD_PRICE}}", exp_data['food']['price'])
            t = t.replace("{{EXP_HOTEL_DETAIL}}", exp_data['hotel']['detail'])
            t = t.replace("{{EXP_HOTEL_PRICE}}", exp_data['hotel']['price'])
            t = t.replace("{{EXP_TOTAL}}", exp_data['total'])
            
            exps_html += t + "<br/>"
        
        pre = html[:html.find(exp_start_marker)]
        post = html[html.find(exp_end_marker) + len(exp_end_marker):]
        html = pre + exps_html + post

    return html

def generate_fill_script(data):
    """
    (Legacy) Playwright가 브라우저에서 실행할 자바스크립트 코드를 문자열로 반환합니다.
    이 스크립트는 에디터(iframe) 내부의 DOM을 탐색하여 '출장 개요' 테이블의 빈칸을 채웁니다.
    """
    
    # 데이터가 없으면 빈 값 처리
    period = data.get("trip_period", "")
    destination = data.get("destination", "")
    dept = data.get("dept", "")
    name = data.get("name", "")
    position = data.get("position", "")
    trip_purpose = data.get("trip_purpose", "")
    region = data.get("region", "")

    # dept가 단일 문자열이고 name이 리스트인 경우, 인원 수만큼 dept 반복
    if isinstance(name, list) and len(name) > 1:
        if isinstance(dept, str) and dept:
            dept = [dept] * len(name)
        elif isinstance(dept, list) and len(dept) == 1:
            dept = dept * len(name)

    # 리스트로 전달하기 위해 변환 (단일 값도 리스트로)
    def ensure_list(val):
        if isinstance(val, list): return val
        return [val] if val else []

    dept_list = ensure_list(dept)
    name_list = ensure_list(name)
    position_list = ensure_list(position)

    expenses_list = []
    for _ in name_list:
        expenses_list.append(calc_expenses(destination, region))

    # JSON Serialize
    import json
    expenses_json = json.dumps(expenses_list, ensure_ascii=False)
    dept_json = json.dumps(dept_list, ensure_ascii=False)
    name_json = json.dumps(name_list, ensure_ascii=False)
    position_json = json.dumps(position_list, ensure_ascii=False)

    js_script = f"""
    () => {{
        try {{
            // Helper: Find 'Trip Overview' Table
            function findTargetTable(doc) {{
                var allTDs = doc.getElementsByTagName('td');
                var tableKeywords = ['출장 개요', '출장개요', '출장기간', '2025년', '00월'];
                for (var i = 0; i < allTDs.length; i++) {{
                    var text = allTDs[i].innerText.replace(/\\s/g, '');
                    for (var k = 0; k < tableKeywords.length; k++) {{
                        if (text.includes(tableKeywords[k].replace(/\\s/g, ''))) return allTDs[i].closest('table');
                    }}
                }}
                return null;
            }}
            
            // Helper: Find 'Expense Calculation' Tables (Multiple)
            function findExpenseTables(doc) {{
                var foundTables = [];
                var allTDs = doc.getElementsByTagName('td');
                // Keyword: '산출내역' inside a table, usually has '교통비' or '합계'
                for (var i = 0; i < allTDs.length; i++) {{
                    var text = allTDs[i].innerText.replace(/\\s/g, '');
                    // Check for "출장비산출내역" or similar unique headers
                    if (text.includes('출장비산출내역') || (text.includes('산출내역') && text.includes('교통비'))) {{
                        var tbl = allTDs[i].closest('table');
                        if (tbl && !foundTables.includes(tbl)) foundTables.push(tbl);
                    }}
                }}
                return foundTables;
            }}

            // Recursive Search Strategy
            function searchFramesRecursive(win, strategy) {{
                try {{
                    var doc = win.document;
                    var res = strategy(doc); 
                    if (res && (Array.isArray(res) ? res.length > 0 : res)) return res;
                    var frames = doc.getElementsByTagName('iframe');
                    for (var i = 0; i < frames.length; i++) {{
                        try {{
                            var childRes = searchFramesRecursive(frames[i].contentWindow, strategy);
                            if (childRes && (Array.isArray(childRes) ? childRes.length > 0 : childRes)) return childRes;
                        }} catch(e) {{}}
                    }}
                }} catch(e) {{}}
                return null;
            }}

            var topWin = document.getElementById('editorView_1') ? document.getElementById('editorView_1').contentWindow : window;

            // ------------------------------------------------------------
            // 1. Fill Trip Overview
            // ------------------------------------------------------------
            var overviewTable = searchFramesRecursive(topWin, findTargetTable);
            if (overviewTable) {{
                var cells = overviewTable.getElementsByTagName('td');
                function safeSetText(el, val) {{
                    if(!el || val===undefined) return;
                    var spans = el.getElementsByTagName('span');
                    if (spans.length>0) {{ spans[0].innerText=val; return; }}
                    var ps = el.getElementsByTagName('p');
                    if (ps.length>0) {{ ps[0].innerText=val; return; }}
                    el.innerText = val;
                }}
                function fillNext(k, v) {{
                    for(var i=0; i<cells.length; i++) {{
                        var t = cells[i].innerText.replace(/\\s/g, '');
                        if(t.includes(k)) {{
                            var n=cells[i].nextElementSibling; 
                            if(n) {{ safeSetText(n, v); return true; }}
                        }}
                    }}
                    return false;
                }}
                function fillMultiRows(keywords, values) {{
                    if (!values || values.length === 0) return false;
                    var headerCell = null;
                    for (var i = 0; i < cells.length; i++) {{
                         var t = cells[i].innerText.replace(/\\s/g, '');
                         for (var k = 0; k < keywords.length; k++) {{ if (t.includes(keywords[k])) {{ headerCell = cells[i]; break; }} }}
                         if (headerCell) break;
                    }}
                    if (!headerCell) return false;
                    var currentRow = headerCell.parentElement;
                    var colIndex = Array.from(currentRow.children).indexOf(headerCell);
                    var rowIter = currentRow.nextElementSibling;
                    for (var j = 0; j < values.length; j++) {{
                        if (!rowIter) break;
                        var diff = currentRow.children.length - rowIter.children.length;
                        var tIdx = colIndex;
                        if (diff > 0) tIdx = colIndex - diff;
                        if (tIdx >= 0 && rowIter.children[tIdx]) safeSetText(rowIter.children[tIdx], values[j]);
                        rowIter = rowIter.nextElementSibling;
                    }}
                    return true;
                }}
                
                var depts = {dept_json};
                var names = {name_json};
                var positions = {position_json};
                
                fillNext('출장기간', '{period}');
                fillNext('출장지', '{destination}');
                fillNext('출장목적', '{trip_purpose}');
                fillMultiRows(['소속'], depts);
                fillMultiRows(['성명', '성함'], names);
                fillMultiRows(['직책', '직위'], positions);
            }}

            // ------------------------------------------------------------
            // 2. Fill Expense Tables
            // ------------------------------------------------------------
            var expenses = {expenses_json};
            var expenseTables = searchFramesRecursive(topWin, findExpenseTables);
            
            if (expenseTables && expenseTables.length > 0) {{
                var count = Math.min({len(name_list)}, expenseTables.length);
                
                for (var i = 0; i < count; i++) {{
                    var tbl = expenseTables[i];
                    var exp = expenses[i];
                    var t_dept = {dept_json}[i] || '';
                    var t_name = {name_json}[i] || '';
                    var t_pos = {position_json}[i] || '';
                    
                    var e_cells = tbl.getElementsByTagName('td');
                    function eSet(el, val) {{
                        if(!el || val===undefined) return;
                        var spans = el.getElementsByTagName('span');
                        if (spans.length>0) {{ spans[0].innerText=val; return; }}
                        el.innerText = val;
                    }}
                    
                    // Fill Header Info
                    function fillHeaderVal(keywords, val) {{
                        for(var c=0; c<e_cells.length; c++) {{
                            var txt = e_cells[c].innerText.replace(/\\s/g,'');
                            for(var k of keywords) {{
                                if(txt.includes(k)) {{
                                    var row = e_cells[c].parentElement;
                                    var idx = Array.from(row.children).indexOf(e_cells[c]);
                                    var nextRow = row.nextElementSibling;
                                    if(nextRow) {{
                                        var diff = row.children.length - nextRow.children.length;
                                        var tIdx = idx; 
                                        if (diff > 0) tIdx = idx - diff;
                                        if (tIdx >= 0 && nextRow.children[tIdx]) {{
                                            eSet(nextRow.children[tIdx], val);
                                        }}
                                    }}
                                    return;
                                }}
                            }}
                        }}
                    }}
                    
                    fillHeaderVal(['소속'], t_dept);
                    fillHeaderVal(['성명','성함'], t_name);
                    fillHeaderVal(['직책','직위'], t_pos);
                    
                    // Fill Expense Row
                    function fillExpenseRow(label, detail, price) {{
                        for(var c=0; c<e_cells.length; c++) {{
                            if(e_cells[c].innerText.replace(/\\s/g,'').includes(label)) {{
                                var sib1 = e_cells[c].nextElementSibling;
                                if(sib1) {{
                                    eSet(sib1, detail);
                                    var sib2 = sib1.nextElementSibling;
                                    if(sib2) eSet(sib2, price);
                                }}
                                return;
                            }}
                        }}
                    }}
                    
                    fillExpenseRow('교통비', exp.traffic.detail, exp.traffic.price);
                    fillExpenseRow('일비', exp.daily.detail, exp.daily.price);
                    fillExpenseRow('식비', exp.food.detail, exp.food.price);
                    fillExpenseRow('숙박비', exp.hotel.detail, exp.hotel.price);
                    
                    // Total
                    function fillTotal(val) {{
                         for(var c=0; c<e_cells.length; c++) {{
                            if(e_cells[c].innerText.replace(/\\s/g,'').includes('합계')) {{
                                var sib1 = e_cells[c].nextElementSibling;
                                if(sib1) {{
                                    eSet(sib1, val);
                                }}
                                return;
                            }}
                         }}
                    }}
                     fillTotal(exp.total);
                }}
            }}
            
            return {{ success: true, message: "작성 완료 (개요 + 산출내역 V2)" }};
            
        }} catch (e) {{
            return {{ success: false, message: "JS Error: " + e.toString() }};
        }}
    }}
    """
    return js_script