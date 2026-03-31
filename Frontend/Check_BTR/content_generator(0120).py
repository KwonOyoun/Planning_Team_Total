import json

# ---------------------------------------------------------
# 1. HTML 템플릿 (3명 이상 확장을 위한 마커 포함)
# ---------------------------------------------------------
TEMPLATE_HTML = """
<style>
    table { border-collapse: collapse; width: 100%; font-family: "Malgun Gothic", sans-serif; font-size: 10pt; }
    th, td { border: 1px solid #000; padding: 5px; }
    .header-bg { background-color: #f2f2f2; text-align: center; font-weight: bold; }
    .center { text-align: center; }
    .right { text-align: right; }
    .title { font-size: 14pt; font-weight: bold; margin-bottom: 10px; }
</style>

<div class="title">□ 출장 개요</div>
<table>
    <colgroup>
        <col style="width: 15%;">
        <col style="width: 25%;">
        <col style="width: 25%;">
        <col style="width: 35%;">
    </colgroup>
    <tr>
        <td class="header-bg">출장기간</td>
        <td colspan="3">{{TRIP_PERIOD}}</td>
    </tr>
    <tr>
        <td class="header-bg">출장지</td>
        <td colspan="3">{{DESTINATION}}</td>
    </tr>
    <tr>
        <td class="header-bg" rowspan="{{TRAVELER_ROWSPAN}}">출장자</td>
        <td class="header-bg">소속</td>
        <td class="header-bg">성함</td>
        <td class="header-bg">직책/직위</td>
    </tr>
    <tr>
        <td class="center">{{DEPT}}</td>
        <td class="center">{{NAME}}</td>
        <td class="center">{{POSITION}}</td>
    </tr>
    <tr>
        <td class="header-bg">외부 참석자</td>
        <td colspan="3">&nbsp;</td>
    </tr>
    <tr>
        <td class="header-bg">출장목적</td>
        <td colspan="3">{{TRIP_PURPOSE}}</td>
    </tr>
    <tr>
        <td class="header-bg">세부내용<br>(외부 회의내용)</td>
        <td colspan="3" style="height: 100px; vertical-align: top;">&nbsp;</td>
    </tr>
    <tr>
        <td class="header-bg">결론</td>
        <td colspan="3" style="height: 50px;"></td>
    </tr>
    <tr>
        <td class="header-bg">특이사항</td>
        <td colspan="3"></td>
    </tr>
</table>
<div style="font-size: 9pt; color: #666; margin-top: 5px;">
    ※ 세부내용은 출장자들의 출장업무 및 외부 회의내용(안건별 참석자 각각의 의견 등)을 정확히 파악할 수 있도록 작성
</div>
<br><br>

<div class="title">□ 출장비 산출내역</div>
<table>
    <colgroup>
        <col style="width: 15%;">
        <col style="width: 25%;">
        <col style="width: 25%;">
        <col style="width: 35%;">
    </colgroup>
    <tr>
        <td class="header-bg">출장자</td>
        <td class="center">{{DEPT}}</td>
        <td class="center">{{NAME}}</td>
        <td class="center">{{POSITION}}</td>
    </tr>
</table>
<table style="border-top: none;">
    <colgroup>
        <col style="width: 15%;">
        <col style="width: 25%;">
        <col style="width: 30%;">
        <col style="width: 30%;">
    </colgroup>
    <tr>
        <td class="header-bg" colspan="4">산출내역</td>
    </tr>
    <tr>
        <td class="header-bg">항목</td>
        <td class="header-bg">내역</td>
        <td class="header-bg">금액</td>
        <td class="header-bg">비고</td>
    </tr>
    <tr>
        <td class="header-bg">교통비</td>
        <td class="center">{{EXP_TRAFFIC_DETAIL}}</td>
        <td class="right">{{EXP_TRAFFIC_PRICE}} 원</td>
        <td class="center">증빙서류 첨부</td>
    </tr>
    <tr>
        <td class="header-bg">일비</td>
        <td class="center">{{EXP_DAILY_DETAIL}}</td>
        <td class="right">{{EXP_DAILY_PRICE}} 원</td>
        <td></td>
    </tr>
    <tr>
        <td class="header-bg">식비</td>
        <td class="center">{{EXP_FOOD_DETAIL}}</td>
        <td class="right">{{EXP_FOOD_PRICE}} 원</td>
        <td></td>
    </tr>
    <tr>
        <td class="header-bg">숙박비</td>
        <td class="center">{{EXP_HOTEL_DETAIL}}</td>
        <td class="right">{{EXP_HOTEL_PRICE}} 원</td>
        <td></td>
    </tr>
    <tr>
        <td class="header-bg">합계</td>
        <td colspan="2" class="right" style="font-weight: bold; background-color: #fffcf0;">{{EXP_TOTAL}} 원</td>
        <td></td>
    </tr>
</table>
<br>
"""

# ---------------------------------------------------------
# 2. 비용 산출 로직
# ---------------------------------------------------------
def calc_expenses(dest_str, region_str=""):
    near_1 = ["광명", "고양", "과천", "구리", "군포", "김포", "부천", "성남", "수원", "시흥", "안산", "안양", "의왕", "인천", "하남"]
    near_2 = ["가평", "강화", "광주", "남양주", "동두천", "안성", "양주", "양평", "여주", "연천", "오산", "용인", "의정부", "이천", "파주", "평택", "포천", "화성"]
    
    dest_clean = dest_str.replace(" ", "")
    check_target = (region_str or "") + " " + dest_str
    
    # [수정 1] 교통비 상세: 목적지(dest_str) 대신 지역(region_str) 사용
    display_region = region_str if region_str else dest_str
    traffic = {"detail": f"서울↔{display_region}", "price": "실비"}

    daily = {"detail": "1일", "price": "0"}
    food = {"detail": "1일", "price": "0"}
    hotel = {"detail": "", "price": ""}
    
    if "서울" in check_target or "서울" in dest_clean:
        daily["price"] = "20,000"
        food["price"] = "0"
        traffic["detail"] = "서울 시내"
        traffic["price"] = "실비"
    elif any(city in check_target for city in near_1):
        daily["price"] = "25,000"
        food["price"] = "0"
    elif any(city in check_target for city in near_2):
        daily["price"] = "30,000"
        food["price"] = "0"
    else:
        daily["price"] = "20,000"
        food["price"] = "30,000"
        
    def parse_price(p):
        clean_p = str(p).replace(",", "").strip()
        return int(clean_p) if clean_p.isdigit() else 0
        
    # [수정 2] 합계 금액 서식 수정 (콤마 적용)
    sum_val = parse_price(daily["price"]) + parse_price(food["price"])
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

    # 리스트 정규화
    def ensure_list(val):
        if isinstance(val, list): return val
        return [val] if val else []

    name_list = ensure_list(name)
    count = len(name_list) # 인원 수 계산
    
    dept_list = ensure_list(dept)
    if isinstance(dept, str) and dept: dept_list = [dept] * count
    elif len(dept_list) == 1: dept_list = dept_list * count
    
    position_list = ensure_list(position)
    if len(position_list) == 1: position_list = position_list * count

    # 1. 기본 정보 치환
    html = template_html
    html = html.replace("{{TRIP_PERIOD}}", period)
    html = html.replace("{{DESTINATION}}", destination)
    html = html.replace("{{TRIP_PURPOSE}}", trip_purpose)

    # 2. 출장자 목록 (Row 반복)
    # [수정] 아래 마커 값이 채워져 있어야 정상 작동합니다!
    row_start_marker = ""
    row_end_marker = ""
    
    if row_start_marker in html and row_end_marker in html:
        s_idx = html.find(row_start_marker) + len(row_start_marker)
        e_idx = html.find(row_end_marker)
        row_tpl = html[s_idx:e_idx]
        
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
        
        html = html.replace("{{TRAVELER_ROWSPAN}}", str(1 + count))

    # 3. 출장비 내역 (테이블 반복)
    # [수정] 여기도 마커 값이 채워져 있어야 합니다!
    exp_start_marker = ""
    exp_end_marker = ""
    
    if exp_start_marker in html and exp_end_marker in html:
        s_idx = html.find(exp_start_marker) + len(exp_start_marker)
        e_idx = html.find(exp_end_marker)
        exp_tpl = html[s_idx:e_idx]
        
        exps_html = ""
        for i in range(count):
            cur_name = name_list[i] if i < len(name_list) else ""
            cur_dept = dept_list[i] if i < len(dept_list) else ""
            cur_pos = position_list[i] if i < len(position_list) else ""
            
            exp_data = calc_expenses(destination, region)
            
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