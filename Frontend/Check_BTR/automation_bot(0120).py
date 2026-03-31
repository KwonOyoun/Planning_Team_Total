from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import unquote
import time
import re
import json
import draft_handler  # [추가] 분리된 핸들러 임포트

# 그룹웨어 메인 URL
GROUPWARE_URL = "https://gw.kothea.or.kr/#/UC/UCA/UCA0000?specialLnb=Y&moduleCode=UC&menuCode=UCA&pageCode=UCA4020"
API_KEYWORD = "ea033A01"
FULL_API_URL = "https://gw.kothea.or.kr/ea/ea033A01"

class GroupwareBot:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
        self.cached_headers = None

    def start(self):
        self.playwright = sync_playwright().start()
        # [수정] 윈도우 크기 2배 정도 (1800x1200)
        self.browser = self.playwright.chromium.launch(headless=self.headless, args=["--window-position=0,0", "--window-size=1800,1200"])
        self.page = self.browser.new_page(viewport={"width": 1800, "height": 1200})

    def is_connected(self):
        try:
            if not self.browser or not self.page: return False
            if not self.browser.is_connected(): return False
            if self.page.is_closed(): return False
            return True
        except: return False

    def login(self, username=None, password=None):
        # 1. 페이지 생존 확인 및 복구
        if not self.page or self.page.is_closed():
            print("⚠️ Page is closed. Creating new page...")
            try:
                # [수정] 복구 시에도 큰 화면 유지
                self.page = self.browser.new_page(viewport={"width": 1800, "height": 1200})
            except Exception as e:
                print(f"❌ Failed to create page: {e}. Restarting browser...")
                self.close()
                self.start()
        
        # 2. URL 체크 (페이지가 닫혀있으면 여기서 에러가 날 수 있으므로 try-except)
        try:
            if self.page.url == GROUPWARE_URL: return True
        except:
             # URL 접근 실패 시 페이지 재생성 시도
            print("⚠️ URL check failed (Page dead?). Recreating...")
            try:
                self.page = self.browser.new_page(viewport={"width": 1800, "height": 1200})
            except:
                self.close()
                self.start()

        print(f"Navigating to {GROUPWARE_URL}...")
        try:
            self.page.goto(GROUPWARE_URL)
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"⚠️ Navigation failed: {e}. Attempting full restart...")
            try:
                self.close()
                self.start()
                self.page.goto(GROUPWARE_URL)
                self.page.wait_for_load_state("networkidle")
            except Exception as e2:
                print(f"❌ Restart failed: {e2}")
                return False

        if "login" in self.page.url.lower() or self.page.locator("#reqLoginId").is_visible():
            if username and password:
                print("Auto-login...")
                try:
                    self.page.fill("#reqLoginId", username)
                    self.page.keyboard.press("Enter")
                    time.sleep(0.5)
                    self.page.wait_for_selector("#reqLoginPw", state="visible", timeout=3000)
                    self.page.fill("#reqLoginPw", password)
                    self.page.keyboard.press("Enter")
                    time.sleep(3)
                    return True
                except: return False
            else: return False
        return True

    def _capture_headers(self):
        print("⚡ Capturing headers...")
        try:
            with self.page.expect_request(lambda request: API_KEYWORD in request.url, timeout=10000) as first:
                btn = self.page.locator(".btn_search").first
                if btn.is_visible(): btn.click()
                else: self.page.reload()
            self.cached_headers = first.value.all_headers()
            return True
        except: return False

    def get_trip_list(self):
        if not self.cached_headers:
            if not self._capture_headers(): return []

        print("Fetching trip list via API...")
        payload = {
            "allDocSts": "", "c_aiokflag": "", "co_id": "1000", "fDocSts": "",
            "fromDate": "20250101", "toDate": "20261231",
            "menuAuthType": "USER", "multiDeptSeq": [], "multiKlUserName": [], "multiReceiveSendUsers": [],
            "multiRiEmpNames": [], "multiTxtDrafters": [], "multiaiUserNames": [],
            "nMenuID": "11003600", "page": "1", "pageCode": "UCA4020",
            "pageSize": "500", "periodPicker": "riRegDate", "readYn": "", "riKind": "",
            "sDocSts": "", "searchType": "", "selectFlag": "",
            "sfrDt": "20250101", "stoDt": "20261231",
            "sortField": "riRegDate", "sortType": "DESC", "topSort": "riRegDate"
        }

        try:
            response = self.page.request.post(FULL_API_URL, data=payload, headers=self.cached_headers)
            
            if response.status in [401, 403]:
                print("⚠️ Token expired. Refreshing...")
                if self._capture_headers():
                    response = self.page.request.post(FULL_API_URL, data=payload, headers=self.cached_headers)
                else: return []

            if not response.ok: return []

            raw_list = response.json().get("resultData", {}).get("list", [])
            print(f"Fetched {len(raw_list)} items.")

            applications = []
            reports = []

            for item in raw_list:
                doc_info = {
                    "id": item.get("diKeyCode"),
                    "date": item.get("diWriteDate", "").split(" ")[0],
                    "title": item.get("diTitle", ""),
                    "drafter": item.get("diEmpName", ""),
                    "type": item.get("tiName", "")
                }
                if any(x in doc_info['type'] for x in ["출장신청서", "계획서", "품의서"]):
                    applications.append(doc_info)
                elif any(x in doc_info['type'] for x in ["보고서", "결과보고"]):
                    reports.append(doc_info)

            def parse_info(t):
                proj = re.search(r'\[(.*?)\]', t)
                p_key = proj.group(1).strip() if proj else None
                content_after_proj = t[proj.end():] if proj else t
                date = re.search(r'\d{6}', content_after_proj)
                d_key = date.group(0) if date else None
                return p_key, d_key

            trips = []
            for app in applications:
                app_proj, app_date_key = parse_info(app['title'])
                
                if "국외" in app['title']:
                    trips.append({
                        "date": app['date'], "name": app['title'], "app_id": app['id'],
                        "status": "Overseas Trip", "report_status": "-", 
                        "report_title": "-", "report_id": ""
                    })
                    continue

                matched_report = None
                for rpt in reports:
                    rpt_proj, rpt_date_key = parse_info(rpt['title'])
                    if app_proj != rpt_proj: continue
                    
                    is_match = False
                    if app_date_key:
                        if app_date_key == rpt_date_key: is_match = True
                    else:
                        if app['drafter'] == rpt['drafter'] and rpt['date'] >= app['date']: is_match = True

                    if is_match:
                        matched_report = rpt
                        break
                
                trips.append({
                    "date": app['date'],
                    "name": app['title'],
                    "app_id": app['id'],
                    "status": "Trip Approved",
                    "report_status": "Submitted" if matched_report else "Missing",
                    "report_title": matched_report['title'] if matched_report else "",
                    "report_id": matched_report['id'] if matched_report else "",
                })
            
            trips.sort(key=lambda x: x["date"], reverse=True)
            return trips

        except Exception as e:
            print(f"Error: {e}")
            return []

    def open_document(self, doc_id):
        if not self.page: return False, "Browser not active"
        try:
            self.page.bring_to_front()
            direct_url = f"https://gw.kothea.or.kr/#/popup?MicroModuleCode=ea&diKeyCode={doc_id}&callComp=UCAP001"
            self.page.goto(direct_url)
            return True, "Opened"
        except Exception as e: return False, str(e)

    
    def get_application_details(self, doc_id):
        """
        Open the application document and scrape trip details.
        Returns a dictionary with keys: trip_period, destination, dept, name, position
        """
        if not self.page: return {}
        print(f"[AutomationBot] Fetching details for App ID: {doc_id}...")
        
        try:
            # Open document
            self.open_document(doc_id)
            
            # Wait for content
            try:
                self.page.wait_for_selector("text=출장기간", timeout=5000)
            except:
                print("[AutomationBot] '출장기간' text not found. Loading might have failed or format changed.")
                # We don't return empty yet, maybe other fields exist.

            # Scrape using BeautifulSoup
            soup = BeautifulSoup(self.page.content(), 'html.parser')
            details = {
                "trip_period": "",
                "destination": "",
                "dept": "",
                "name": "",
                "position": ""
            }

            # Helper for loose text matching
            def clean_text(text):
                return text.replace("\xa0", " ").strip()

            def find_value_by_label(keywords):
                for cell in soup.find_all(["th", "td"]):
                    txt = clean_text(cell.get_text())
                    if any(k in txt for k in keywords):
                        # Try Next Sibling
                        sib = cell.find_next_sibling(["td", "th"])
                        if sib: return clean_text(sib.get_text())
                return ""

            # 1. Trip Period (출장기간)
            details["trip_period"] = find_value_by_label(["출장기간", "출장 일정"])

            # 2. Destination (출장지)
            details["destination"] = find_value_by_label(["출장지", "방문처"])

            # 2.1 Region (지역) - for accurate expense calc
            details["region"] = find_value_by_label(["지역", "출장 지역"])

            # 3. Traveler Info (출장자)
            # The image shows "출장자" label, and the value is "임성준 선임연구원" (Name + Position/Rank)
            # It also shows separate tables for Name/Dept line at the top.
            # Let's try to grab "출장자" field first as it contains Name + Rank often.
            # 3. Traveler Info (출장자)
            traveler_str = find_value_by_label(["출장자"])
            names = []
            positions = []
            
            if traveler_str:
                # Format: "Name Position, Name Position"
                people = [p.strip() for p in traveler_str.split(',') if p.strip()]
                for person in people:
                    parts = person.split()
                    if len(parts) >= 1: names.append(parts[0])
                    if len(parts) >= 2: positions.append(" ".join(parts[1:]))
                    else: positions.append("") # Position might be empty
            
            if names:
                details["name"] = names
                details["position"] = positions
            
            # Fallback: Scrape individual fields if main scraping failed
            if not details["name"]:
                n = find_value_by_label(["성 명", "성명"])
                if n: details["name"] = [n]
            if not details["dept"]:
                details["dept"] = find_value_by_label(["기안부서", "소 속", "부서"])
            if not details["position"] and not positions:
                p = find_value_by_label(["직 책", "직책", "직 급", "직급"])
                if p: details["position"] = [p]

            print(f"[AutomationBot] Scraped info: {details}")
            return details

        except Exception as e:
            print(f"[AutomationBot] Error fetching details: {e}")
            return {}

    def draft_report(self, app_id):
        """
        [수정됨] 외부 모듈(draft_handler)을 호출하여 로직을 위임
        """
        if not self.page: return False, "Browser not active"
        
        # 1. Fetch Trip Details from the Application Document
        trip_data = self.get_application_details(app_id)
        
        # 2. 외부 파일에 있는 함수 실행 (브라우저 제어권 page 객체를 넘겨줌)
        # Pass trip_data to the handler
        return draft_handler.execute_drafting(self.page, app_id, trip_data)

    def get_report_detail(self, doc_id):
        success, msg = self.open_document(doc_id)
        if not success: return None, msg
        time.sleep(3)
        try:
            soup = BeautifulSoup(self.page.content(), 'html.parser')
            doc_name = soup.find(attrs={"name": "doc_name"}).get_text(strip=True) if soup.find(attrs={"name": "doc_name"}) else "Unknown"
            drafter = soup.find(attrs={"name": "DRAFT_USER_NM"}).get_text(strip=True) if soup.find(attrs={"name": "DRAFT_USER_NM"}) else "Unknown"
            
            total = 0
            for cell in soup.find_all(string=lambda t: "합계" in t if t else False):
                try:
                    for col in reversed(cell.find_parent("tr").find_all("td")):
                        txt = col.get_text(strip=True).replace(",", "").replace("원", "")
                        if txt.isdigit():
                            total += int(txt)
                            break
                except: continue
            
            return {
                "title": doc_name, "drafter": drafter, "total_expense": total,
                "attachment_count": len(soup.select(".fileUploader .list li")),
                "file_names": []
            }, "Success"
        except Exception as e: return None, str(e)

    def close(self):
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()