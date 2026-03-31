import time
import os
import re
from datetime import datetime, timedelta

# 국내출장보고서 양식 ID
REPORT_FORM_ID = "1045"


# -----------------------------
# Debug helpers
# -----------------------------
def _debug_dump(page, tag: str):
    """
    Save a screenshot to help debug UI state (popup opened? field visible?).
    Files are saved in the current working directory.
    """
    try:
        page.screenshot(path=f"debug_{tag}.png", full_page=True)
        print(f"[DEBUG] Screenshot saved: debug_{tag}.png")
    except Exception as e:
        print(f"[DEBUG] screenshot failed ({tag}): {e}")


def _wait_any_popup(page, keywords=None, timeout_ms=9000):
    """
    Wait for any modal-like container (dialog/aria-modal/text match).
    Returns a Locator scoped to the popup container, or None.

    keywords: list[str] - if provided, prefer a container that includes one of these keywords.
    """
    keywords = keywords or []
    start = time.time()

    while (time.time() - start) * 1000 < timeout_ms:
        # Pattern 1: Explicit dialog roles or known classes + Keyword text
        # This is the safest way to distinguish popup from main page text.
        selectors = [
            "[role='dialog']",
            "div[aria-modal='true']",
            "div[class*='Dialog']", 
            "div[class*='popup']", 
            "div[class*='layer']",
            ".OBTDialog_dialogRoot__1Q--d" # Known class from previous logs
        ]
        
        for sel in selectors:
            candidates = page.locator(sel)
            count = candidates.count()
            for i in range(count):
                el = candidates.nth(i)
                if el.is_visible():
                    # If keywords provided, filter by text
                    if keywords:
                        try:
                            txt = el.inner_text() or ""
                            if any(k in txt for k in keywords):
                                return el
                        except:
                            continue
                    else:
                        return el

        time.sleep(0.5)

    return None


# -----------------------------
# Utility helpers
# -----------------------------
def _safe_text(s: str) -> str:
    return (s or "").strip()


def _click_center(locator) -> bool:
    """
    Some tree/grid UIs require clicking the row center rather than child span text.
    """
    try:
        box = locator.bounding_box()
        if box:
            locator.page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            return True
    except:
        pass
    try:
        locator.click(force=True)
        return True
    except:
        return False


def _fill_date_input(inp, value: str):
    """
    Robust replace for date inputs.
    """
    inp.click(force=True)
    try:
        inp.press("Control+A")
    except:
        pass
    inp.press("Backspace")
    inp.type(value, delay=30)
    inp.press("Enter")


def _extract_app_title(page) -> str:
    """
    Extract original (application) title from read page.
    """
    old_title = ""

    # 1) common input
    try:
        doc_input = page.locator("input[name='doc_name']").first
        if doc_input.count() > 0 and doc_input.is_visible():
            old_title = _safe_text(doc_input.input_value())
    except:
        pass

    # 2) element with name='doc_name'
    if not old_title:
        try:
            node = page.locator("[name='doc_name']").first
            if node.count() > 0:
                old_title = _safe_text(node.text_content())
        except:
            pass

    # 3) table row "제목"
    if not old_title:
        try:
            old_title = _safe_text(
                page.locator("xpath=//tr[.//th[contains(text(),'제목')]]//td").first.text_content()
            )
        except:
            pass

    return _safe_text(old_title)


def _build_new_title(old_title: str) -> str:
    new_title = old_title
    new_title = new_title.replace("신청서", "결과보고서").replace("계획서", "결과보고서").replace("품의서", "결과보고서")
    if "보고서" not in new_title:
        new_title = new_title.strip() + " 결과보고서"
    return new_title.strip()


def _title_keyword_fallback(old_title: str) -> str:
    """
    Fallback keyword if exact title search fails.
    - remove leading [ ... ]
    - compress whitespace
    - truncate length
    """
    t = old_title
    t = re.sub(r"^\s*\[[^\]]+\]\s*", "", t)  # remove leading [프로젝트]
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > 40:
        t = t[:40]
    return t


def _fill_text_input(inp, value: str):
    """
    Robust fill for stubborn React inputs using _valueTracker hack.
    """
    try:
        # 1. Standard interactions
        inp.click(force=True)
        time.sleep(0.3)
        inp.press("Control+A")
        inp.press("Backspace")
        time.sleep(0.2)
        inp.type(value, delay=50) 
        time.sleep(0.3)
        
        # 2. React Value Tracker Hack (Improved)
        inp.evaluate(f"""el => {{
            let valueToSet = '{value}';
            let proto = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
            if (proto && proto.set) {{
                proto.set.call(el, valueToSet);
            }} else {{
                el.value = valueToSet;
            }}
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}""")
        time.sleep(0.2)
        inp.press("Tab") # Blur
    except Exception as e:
        print(f"[Draft Handler] _fill_text_input error: {e}")
        try:
            inp.fill(value)
        except: pass

def _find_title_input_anywhere(page):
    selectors = [
        "input[placeholder*='제목을 입력']", # Most specific based on screenshot
        "input[name='doc_name']",
        "#doc_name",
        "input[title='제목']",
        "xpath=//tr[.//th[contains(normalize-space(.),'제목')]]//input",
        "xpath=//label[contains(.,'제목')]/following::input[1]",
        # Broader fallback
        "xpath=//tr[contains(.,'제목')]//input[not(@type='hidden')]",
        ".OBTList_listHeader__2j-p0 input" # Class seen in some screenshots
    ]
    
    # main page
    for sel in selectors:
        loc = page.locator(sel).first
        if loc.count() > 0:
            if loc.is_visible(): return loc
    
    for fr in page.frames:
        for sel in selectors:
            try:
                loc = fr.locator(sel).first
                if loc.count() > 0 and loc.is_visible(): return loc
            except: continue
    return None




# -----------------------------
# Main entry
# -----------------------------
def execute_drafting(page, app_id, trip_data=None):
    """
    Playwright Page 객체를 받아 보고서 작성을 수행하는 함수

    목표:
      1) 신청서 제목 추출
      2) 결과보고서 작성 화면으로 이동 후 제목 입력 (iframe 포함)
      3) 기록물철 선택 '출장' -> '반영' (팝업 DOM 패턴 다양성 대응)
      4) 참조문서 추가
         - 기간: 오늘-1년 ~ 오늘
         - 제목: 출장신청서 제목(원제)
    """
    print(f"[Draft Handler] Start processing App ID: {app_id}")

    try:
        # ============================================================
        # 1. 신청서 읽기
        # ============================================================
        read_url = f"https://gw.kothea.or.kr/#/popup?MicroModuleCode=ea&diKeyCode={app_id}&callComp=UCAP001"
        page.goto(read_url)
        page.wait_for_load_state("domcontentloaded")
        try:
            page.wait_for_selector("[name='doc_name'], input[name='doc_name']", timeout=8000)
        except:
            time.sleep(2)

        old_title = _extract_app_title(page)
        if not old_title:
            _debug_dump(page, "fail_extract_old_title")
            return False, "Could not extract original title."

        new_title = _build_new_title(old_title)
        print(f"[Draft Handler] Old title: {old_title}")
        print(f"[Draft Handler] New title: {new_title}")

        new_title = _build_new_title(old_title)
        print(f"[Draft Handler] Old title: {old_title}")
        print(f"[Draft Handler] New title: {new_title}")
        
        _debug_dump(page, "app_read_view")

        # ============================================================
        # 2. 작성 페이지 이동 (버튼 클릭 우선 시도)
        # ============================================================
        print("[Draft Handler] Attempting to find 'Write Result Report' button...")
        
        # 버튼 찾기 시도 (결과보고, 복사 등)
        report_btn = page.locator("button:has-text('결과보고'), a:has-text('결과보고'), button:has-text('결과보고서'), a:has-text('결과보고서')").first
        
        button_clicked = False
        if report_btn.count() > 0 and report_btn.is_visible():
            print("[Draft Handler] Found 'Result Report' button! Clicking...")
            try:
                report_btn.click()
                button_clicked = True
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2.0)
            except Exception as e:
                print(f"[Draft Handler] Failed to click button: {e}")
        
        if not button_clicked:
            print(f"[Draft Handler] Button not found. Falling back to direct URL with ID {REPORT_FORM_ID}...")
            write_url = f"https://gw.kothea.or.kr/#/popup?MicroModuleCode=ea&callComp=UCAP001&tiKeyCode={REPORT_FORM_ID}"
            page.goto(write_url)
        
        # Common wait
        page.wait_for_load_state("domcontentloaded")
        print("[Draft Handler] Waiting for write page to load...")
        time.sleep(3.0) # Increased wait for stability

        _debug_dump(page, "before_title_fill")

        title_filled = False
        target_input = None
        
        # Retry loop for title input
        for attempt in range(5):
            target_input = _find_title_input_anywhere(page)
            if target_input:
                try:
                    if target_input.is_visible() and target_input.is_enabled():
                        break
                except:
                    target_input = None
            print(f"[Draft Handler] Waiting for title input... (attempt {attempt+1}/5)")
            time.sleep(1.0)

        print(f"[DEBUG] title_input found? {bool(target_input)}")

        if target_input:
            try:
                # Scroll to view if possible
                try: target_input.scroll_into_view_if_needed()
                except: pass
                
                print(f"[Draft Handler] Typing new title: {new_title[:20]}...")
                _fill_text_input(target_input, new_title)
                # blur to trigger UI update
                target_input.press("Tab")
                title_filled = True
                print("[DEBUG] title filled (input).")
            except Exception as e:
                print(f"[DEBUG] title fill failed (input): {e}")

        # contenteditable fallback
        if not title_filled:
            try:
                ce = page.locator("[contenteditable='true']").first
                if ce.count() > 0 and ce.is_visible():
                    ce.click(force=True)
                    page.keyboard.press("Control+A")
                    page.keyboard.type(new_title, delay=20)
                    page.keyboard.press("Tab")
                    title_filled = True
                    print("[DEBUG] title filled (contenteditable).")
            except Exception as e:
                print(f"[DEBUG] title fill failed (contenteditable): {e}")

        _debug_dump(page, "after_title_fill")

        # ============================================================
        # 3. 기록물철 선택 (트리 탐색 방식: 2026 -> 기획1팀 -> 출장)
        # ============================================================
        print("[Draft Handler] Selecting Record Folder (Tree Navigation)...")

        try:
            # 1. 기록물철 팝업 열기
            folder_btn = page.locator(
                "xpath=//tr[.//th[contains(text(),'기록물철')]]//button | "
                "//tr[.//th[contains(text(),'기록물철')]]//a | "
                "//th[contains(.,'기록물철')]/following-sibling::td//button | "
                "//th[contains(.,'기록물철')]/following-sibling::td//a"
            ).first

            folder_btn.wait_for(state="visible", timeout=8000)
            folder_btn.click(force=True)
            
            # 팝업 대기
            folder_popup = _wait_any_popup(page, ["기록물철선택", "기록물철 선택"], timeout_ms=10000)
            if not folder_popup:
                folder_popup = _wait_any_popup(page, [], timeout_ms=3000)
            
            if not folder_popup:
                 raise Exception("Record folder popup not detected.")

            print("[Draft Handler] Record Folder Popup Found.")
            time.sleep(1.0) # 트리 로딩 대기

            # ---------------------------------------------------------
            # [수정] 검색 대신 계층 구조를 따라 클릭 (2026 -> 기획1팀 -> 출장)
            # ---------------------------------------------------------
            
            # 목표 설정
            target_year = "2026"
            target_team = "기획1팀"
            target_folder = "출장"

            def _expand_node(popup, node_text, child_text=None):
                """
                텍스트를 찾아 클릭하고 오른쪽 화살표키를 눌러 트리를 펼치는 함수.
                이미 펼쳐져 있는지(child_text가 보이는지) 확인하여 불필요한 클릭(닫김) 방지.
                최후의 수단으로 토글 아이콘 클릭 시도.
                """
                print(f"[Draft Handler] Finding tree node: {node_text}...")
                
                # 1. 자식 노드가 이미 보이는지 확인 (펼쳐져 있는 상태)
                if child_text:
                    child_node = popup.locator(f"xpath=.//*[contains(text(), '{child_text}')]").first
                    if child_node.count() > 0 and child_node.is_visible():
                        print(f"[Draft Handler] Child node '{child_text}' acts as visible. Skipping expand of '{node_text}'.")
                        return True

                # 2. 노드 찾기
                node = popup.locator(f"xpath=.//*[contains(text(), '{node_text}')]").first
                try: node.scroll_into_view_if_needed()
                except: pass
                
                if node.count() > 0 and node.is_visible():
                    # 3. 클릭 및 확장 시도
                    print(f"[Draft Handler] Clicking/Expanding '{node_text}'...")
                    node.click(force=True)
                    time.sleep(0.3)
                    page.keyboard.press("ArrowRight") 
                    
                    # 4. 확인 및 재시도
                    if child_text:
                        # Wait a bit for animation/fetch
                        try:
                            popup.locator(f"xpath=.//*[contains(text(), '{child_text}')]").first.wait_for(state="visible", timeout=2000)
                            return True
                        except:
                            print(f"[Draft Handler] Child '{child_text}' not appeared after ArrowRight. Retrying...")

                        # 4-1. Double Click Text
                        print(f"[Draft Handler] Double-clicking '{node_text}'...")
                        node.dblclick(force=True)
                        try:
                            popup.locator(f"xpath=.//*[contains(text(), '{child_text}')]").first.wait_for(state="visible", timeout=2000)
                            return True
                        except:
                             pass
                             
                        # 4-2. Click Preceding Siblings (Icon/Toggle)
                        # Try to click the item immediately before the text (usually folder icon) 
                        # and the one before that (usually toggle arrow)
                        print("[Draft Handler] Trying to click preceding siblings (Folder Icon / Toggle)...")
                        try:
                             # Immediate predecessor (Folder Icon?)
                             prev1 = node.locator("xpath=preceding-sibling::*[1]")
                             if prev1.count() > 0:
                                 prev1.click(force=True)
                                 # Checking...
                                 time.sleep(0.5)
                                 if popup.locator(f"xpath=.//*[contains(text(), '{child_text}')]").first.is_visible():
                                     return True
                                     
                             # Second predecessor (Toggle Arrow?)
                             prev2 = node.locator("xpath=preceding-sibling::*[2]")
                             if prev2.count() > 0:
                                 prev2.click(force=True)
                                 time.sleep(0.5)
                                 if popup.locator(f"xpath=.//*[contains(text(), '{child_text}')]").first.is_visible():
                                     return True
                        except Exception as e:
                            print(f"[Draft Handler] Sibling click failed: {e}")

                    # Final check
                    if child_text:
                         if popup.locator(f"xpath=.//*[contains(text(), '{child_text}')]").first.is_visible():
                             return True
                         else:
                             print(f"[Draft Handler] Failed to expand '{node_text}'. Child '{child_text}' not visible.")
                             return False
                    return True
                else:
                    print(f"[Draft Handler] Tree node '{node_text}' not found.")
                    return False

            # 1) '2026' 찾아서 펼치기 (자식: 기획1팀)
            # [OPTIMIZATION] If '출장' is already visible, skip tree expansion.
            print(f"[Draft Handler] Optimistic check for '{target_folder}'...")
            found_optimistic_node = None
            
            target_nodes = folder_popup.locator(f"xpath=.//*[contains(text(), '{target_folder}')]")
            count = target_nodes.count()
            
            # Find the FIRST visible node (Top-down order)
            for i in range(count):
                node = target_nodes.nth(i)
                if node.is_visible():
                    found_optimistic_node = node
                    print(f"[Draft Handler] Found visible '{target_folder}' at index {i}. (Optimization)")
                    break
            
            # Helper to perform selection click
            def _select_final_node(node):
                 print(f"[Draft Handler] Clicking '{target_folder}'...")
                 node.click(force=True)
                 time.sleep(0.5)
                 print(f"[Draft Handler] Double-clicking '{target_folder}' to ensure selection...")
                 node.dblclick(force=True)
                 time.sleep(0.5)

            if found_optimistic_node:
                 _select_final_node(found_optimistic_node)
            else:
                # Standard Tree Expansion fallback
                if _expand_node(folder_popup, target_year, target_team):
                    if _expand_node(folder_popup, target_team, target_folder):
                        print(f"[Draft Handler] Finding final folder: {target_folder}...")
                        
                        # Re-locate after expansion
                        target_nodes = folder_popup.locator(f"xpath=.//*[contains(text(), '{target_folder}')]")
                        count = target_nodes.count()
                        
                        final_node = None
                        # Again, prefer the FIRST visible one
                        for i in range(count):
                            node = target_nodes.nth(i)
                            if node.is_visible():
                                final_node = node
                                print(f"[Draft Handler] Found visible '{target_folder}' at index {i} after expansion.")
                                break
                        
                        if final_node:
                            final_node.scroll_into_view_if_needed()
                            _select_final_node(final_node)
                            print(f"[Draft Handler] Selected '{target_folder}'.")
                        else:
                            print(f"[Draft Handler] Folder '{target_folder}' not found (no visible nodes).")
                    else:
                        print(f"[Draft Handler] Team '{target_team}' not found under {target_year}.")
                else:
                     print(f"[Draft Handler] Year '{target_year}' not found.")

            # ---------------------------------------------------------
            
            # (4) '반영' 버튼 클릭
            print("[Draft Handler] clicking apply button...")
            
            # [CHECK] If popup is already closed (e.g. by double-click), skip Reflect.
            time.sleep(0.5) # Allow UI to process the double-click close
            if not folder_popup.is_visible():
                print("[Draft Handler] Popup closed (likely by double-click). Assuming selection applied.")
            else:
                apply_btn = folder_popup.locator("button:has-text('반영'), button.OBTButton_confirm__2K7c1, .popup_footer button.btn_confirm").last
                
                # Dismiss potential alert loop
                def _handle_alert(dialog):
                    print(f"[Draft Handler] Unexpected alert: {dialog.message}")
                    try: dialog.accept()
                    except: pass
                
                page.once("dialog", _handle_alert)

                try:
                    if apply_btn.count() > 0 and apply_btn.is_visible():
                        apply_btn.click(force=True)
                        print("[Draft Handler] Clicked 'Reflect' button.")
                    else:
                        # Try finding by text if selectors fail
                        txt_btn = folder_popup.locator("text='반영'")
                        if txt_btn.count() > 0 and txt_btn.is_visible():
                             txt_btn.click(force=True)
                             print("[Draft Handler] Clicked 'Reflect' by text.")
                        else:
                             print("[Draft Handler] 'Reflect' button not found (or popup closing).")

                except Exception as e:
                    print(f"[Draft Handler] Reflect click issue (might be closed): {e}")

            time.sleep(1.0)
            _debug_dump(page, "after_folder_apply")

            print("[Draft Handler] Applied Record Folder.")

        except Exception as e:
            print(f"[Draft Handler] Folder error: {e}")
            _debug_dump(page, "folder_error_state")

        # ============================================================
        # 4. 참조문서 추가
        #    기간: 오늘-1년 ~ 오늘
        #    제목: 신청서 제목
        # ============================================================
        print("[Draft Handler] Adding Reference Document...")

        try:
            # Fix: Invalid XPath mixing. Separation is cleaner.
            ref_btn_xpath = (
                "//tr[.//th[contains(text(),'참조문서')]]//button[contains(.,'선택')] | "
                "//th[contains(.,'참조문서')]/following-sibling::td//button[contains(.,'선택')]"
            )
            ref_select_btn = page.locator(f"xpath={ref_btn_xpath}")
            
            if ref_select_btn.count() == 0:
                # Fallback
                ref_select_btn = page.locator("button").filter(has_text="선택").last

            print(f"[DEBUG] ref_select_btn count={ref_select_btn.count()}")
            ref_select_btn.wait_for(state="visible", timeout=8000)

            _debug_dump(page, "before_ref_click")
            ref_select_btn.first.click(force=True) 

            time.sleep(0.6)
            _debug_dump(page, "after_ref_click")

            popup = _wait_any_popup(page, ["참조문서"], timeout_ms=10000)
            print(f"[Draft Handler] Initializing... (Version: {datetime.now().strftime('%H:%M:%S')})")
            


            if not popup:
                raise Exception("Reference popup not detected (click failed or DOM mismatch).")

            print("[Draft Handler] Reference Popup Identified.")

            # [A] 기간 설정: 오늘-1년 ~ 오늘
            today = datetime.now().date()
            start = today - timedelta(days=365)
            start_date = start.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")

            date_inputs = popup.locator(".OBTDatePickerRebuild_inputYMD__PtxMy, input[class*='DatePicker'][type='text']")
            if date_inputs.count() >= 2:
                inp_start = date_inputs.nth(0)
                inp_end = date_inputs.nth(1)

                if inp_start.is_visible():
                    _fill_date_input(inp_start, start_date)
                    time.sleep(0.2)

                if inp_end.is_visible():
                    _fill_date_input(inp_end, end_date)
                    time.sleep(0.3)
            else:
                print("[Draft Handler] Date inputs not found (count < 2).")

            # [B] 제목 검색
            title_input = popup.locator("#diTitle input").first
            if title_input.count() == 0:
                title_input = popup.locator("xpath=.//th[contains(text(),'제목')]/following-sibling::td//input").first
            if title_input.count() == 0:
                # 마지막 fallback: 텍스트 input (date 제외)
                title_input = popup.locator(
                    "xpath=.//input[@type='text' and not(contains(@class,'OBTDatePickerRebuild_inputYMD'))]"
                ).first

            search_btn = popup.locator(
                "button.OBTConditionPanel_searchButton__2cpwg, button:has(img[src*='search']), button:has-text('검색')"
            ).first
            # [Result Verification]
            # Since Canvas grid might not have DOM rows/checkboxes, we rely on Canvas presence or just proceed.
            def _has_results():
                # 1. Check DOM rows
                rows = popup.locator(".grid_body .row, .OBTListGrid_dataRow__3q3J-, tr[class*='row'], tr:not(:first-child)")
                if rows.count() > 0: return True
                # 2. Check checkboxes
                if popup.locator("input[type='checkbox']").count() > 1: return True
                # 3. Check Canvas presence (assume results if grid exists)
                if popup.locator("canvas").count() > 0: return True
                return False

            # 1차: old_title 전체
            if title_input.count() > 0 and title_input.is_visible():
                print(f"[Draft Handler] Typing popup search title: {old_title[:10]}...")
                _fill_text_input(title_input, old_title)
                title_input.press("Enter")
                time.sleep(1.0)
                
                if search_btn.count() > 0 and search_btn.is_visible():
                    search_btn.click(force=True)
                    print("[Draft Handler] Clicked search.")
                    time.sleep(2.5) 

            # 결과 확인
            has_res = _has_results()
            print(f"[Draft Handler] Results found? {has_res}")

            # 결과 없으면 fallback 키워드로 재검색
            if not has_res:
                kw = _title_keyword_fallback(old_title)
                print(f"[Draft Handler] Retrying with keyword: {kw}")
                if kw and title_input.count() > 0 and title_input.is_visible():
                    _fill_text_input(title_input, kw)
                    title_input.press("Enter")
                    time.sleep(1.0)
                    if search_btn.count() > 0 and search_btn.is_visible():
                        search_btn.click(force=True)
                        time.sleep(2.5) # Wait for grid load
            
            # [C] 결과 체크 및 추가
            print("[Draft Handler] Checking results/Adding document...")
            time.sleep(1.0)
            
            success_add = False
            
            # -------------------------------------------------------------------
            # Strategy 3: Canvas Grid Interaction (User-specific)
            # -------------------------------------------------------------------
            print("[Draft Handler] Attempting Canvas Grid Strategy...")
            try:
                canvas_grid = popup.locator("canvas").first
                if canvas_grid.count() > 0 and canvas_grid.is_visible():
                    print("[Draft Handler] Canvas grid found. Interacting with coordinates...")
                    
                    # 1. Click 'First Row' Area
                    # Assuming Header is ~30-40px. First row center is likely ~45px from top.
                    # We click to Select, then Hover to trigger button.
                    
                    # Try clicking
                    canvas_grid.click(position={"x": 100, "y": 45}, force=True)
                    time.sleep(0.5)
                    
                    # Try hovering
                    canvas_grid.hover(position={"x": 100, "y": 45}, force=True)
                    time.sleep(0.5)
                    
                    # 2. Look for the specific Hover Button (User provided)
                    # Selector: .OBTListGrid_hoverActionButtonRoot__2AMHf button
                    hover_btn_selectors = [
                         ".OBTListGrid_hoverActionButtonRoot__2AMHf button",
                         ".OBTListGrid_hoverActionButtonRoot__2AMHf img",
                         "div[class*='hoverActionButtonRoot'] button",
                         "button:has(img[src*='ic_docu_add'])" 
                    ]
                    
                    hover_btn = None
                    for sel in hover_btn_selectors:
                        cand = popup.locator(sel)
                        # The button might be outside the popup container in DOM tree (Portal), 
                        # so checking page-wide might be safer, but popup.locator scopes it.
                        # If it's a portal properly implemented, it might be at body level.
                        # Let's try popup scoped first, then page scoped.
                        if cand.count() > 0 and cand.first.is_visible():
                            hover_btn = cand.first
                            break
                        
                        # Check page scope if not found in popup
                        cand_page = page.locator(sel)
                        if cand_page.count() > 0 and cand_page.first.is_visible():
                             hover_btn = cand_page.first
                             break
                    
                    if hover_btn:
                         print("[Draft Handler] Found Hover Action Button! Clicking...")
                         hover_btn.click(force=True)
                         time.sleep(1.0)
                         
                         # VERIFY: Did it add to the list?
                         # Usually added items appear in a bottom grid/list or have a 'Delete/Cancel' button.
                         # We'll look for *any* indicator of selected items, e.g., a "Delete" button or rows in a second grid.
                         
                         # Common pattern: "삭제" (Delete) button appears for selected items
                         verify_sel = popup.locator("button:has-text('삭제'), button img[src*='delete'], .btn_del")
                         if verify_sel.count() > 0:
                             print("[Draft Handler] Verification: Item added to selection list.")
                             success_add = True
                         else:
                             print("[Draft Handler] Verification Failed: Item NOT found in selection list after click. Retrying click...")
                             hover_btn.click(force=True)
                             time.sleep(1.0)
                             if verify_sel.count() > 0:
                                 success_add = True
                             else:
                                 print("[Draft Handler] Retry failed. Proceeding hoping it worked or manual interaction needed.")
                                 # We mark success_add=True to allow Confirm click to try, but warn.
                                 success_add = True 

                    else:
                         print("[Draft Handler] Hover Action Button not found.")
                else:
                     print("[Draft Handler] Canvas grid not found.")
            except Exception as e:
                print(f"[Draft Handler] Canvas Strategy failed: {e}")

            # -------------------------------------------------------------------
            # Fallback Strategies (DOM based)
            # -------------------------------------------------------------------
            if not success_add:
                print("[Draft Handler] Falling back to DOM-based strategies...")
                
                # Find the target row first (prefer text match, fallback to first row)
                target_row = None
                search_text = old_title[:6]
                
                # Try finding row by text
                try:
                    # Use a broad Xpath to find the text anywhere in the grid
                    text_el = popup.locator(f"xpath=.//*[contains(text(), '{search_text}')]").first
                    if text_el.count() > 0 and text_el.is_visible():
                        # visual row container
                        target_row = text_el.locator("xpath=./ancestor::tr | ./ancestor::div[contains(@class, 'row')] | ./ancestor::div[@role='row']").first
                        print("[Draft Handler] Found target row by text match.")
                except: pass

                # Fallback to first row
                if not target_row or target_row.count() == 0:
                     print("[Draft Handler] Text match failed. Trying to find ANY row...")
                     # Selector for rows
                     row_selectors = [
                         ".grid_body .row", 
                         ".OBTListGrid_dataRow__3q3J-", 
                         "tr[class*='row']", 
                         "div[role='row']", 
                         "tr" # absolute fallback (might catch header, handle index)
                     ]
                     
                     for sel in row_selectors:
                         rows = popup.locator(sel)
                         if rows.count() > 0:
                             # Filter for visibility
                             for i in range(rows.count()):
                                 r = rows.nth(i)
                                 if r.is_visible():
                                     # Skip if it looks like a header (e.g. has 'th')
                                     if r.locator("th").count() > 0:
                                         continue
                                     target_row = r
                                     print(f"[Draft Handler] Found visible row using selector '{sel}' at index {i}.")
                                     break
                             if target_row: break
                
                if target_row and target_row.is_visible():
                    try:
                        # Click the row to select it (handling RealGrid canvas issues by clicking text center)
                        print("[Draft Handler] Clicking row to select...")
                        target_row.click(force=True, position={"x": 50, "y": 10}) 
                        time.sleep(0.5)

                        # Look for Central Down Button (Move to bottom list)
                        # Located usually between two grids
                        add_btn_candidates = [
                            "button.arrBtnDown", 
                            "button[class*='Down']", 
                            "button[class*='down']",
                            "button:has(i[class*='down'])",
                            ".btn_arrow_down",
                            "button[title='추가']", # Sometimes central button has title
                            "xpath=//button[contains(., '▼')]" # Visual text fallback
                        ]
                        
                        add_btn = None
                        for sel in add_btn_candidates:
                            cand = popup.locator(sel)
                            # We want the one that is visible and likely between grids (not the row icon)
                            # Usually these are separate from the grid.
                            if cand.count() > 0:
                                for k in range(cand.count()):
                                    b = cand.nth(k)
                                    if b.is_visible():
                                        add_btn = b
                                        break
                            if add_btn: break
                        
                        if add_btn:
                            print("[Draft Handler] Found Central 'Down' button. Clicking...")
                            add_btn.click(force=True)
                            success_add = True
                        else:
                            print("[Draft Handler] Central 'Down' button not found.")
                    except Exception as e:
                        print(f"[Draft Handler] Strategy 1 failed: {e}")
                
                # Strategy 2: Row-specific 'Add' Icon (Fallback)
                if not success_add:
                    print("[Draft Handler] Strategy 2: Row 'Add' Icon...")
                    try:
                        if target_row and target_row.is_visible():
                            # Hover to reveal if needed
                            target_row.hover(force=True)
                            time.sleep(0.3)
                            
                            # Look for icon inside the row
                            # User screenshot shows tooltip '추가'
                            
                            icon_selectors = [
                                "button[title='추가']",
                                "img[title='추가']",
                                "img[alt='추가']",
                                "*[title='추가']",
                                "button img[src*='7f022f7c']", # original specific
                                "button img[src*='ic_docu_add']",
                                ".btn_add"
                            ]

                            icon_btn = None
                            for sel in icon_selectors:
                                 cand = target_row.locator(sel)
                                 if cand.count() > 0 and cand.first.is_visible():
                                     icon_btn = cand.first
                                     break
                            
                            if icon_btn:
                                print("[Draft Handler] Found Row 'Add' Icon. Clicking...")
                                icon_btn.click(force=True)
                                success_add = True
                            else:
                                 print("[Draft Handler] Row 'Add' Icon not found.")
                                 
                                 # Absolute fallback: Click the last clickable element in the row
                                 print("[Draft Handler] Clicking last button in row as fallback...")
                                 target_row.locator("button, a").last.click(force=True)
                                 success_add = True

                        else:
                            print("[Draft Handler] No result rows found to interact with.")

                    except Exception as e:
                        print(f"[Draft Handler] Strategy 2 failed: {e}")

            time.sleep(0.5)

            time.sleep(0.5)

            # [E] 확인
            confirm_btn = popup.locator("button:has-text('확인')").last
            if confirm_btn.count() > 0 and confirm_btn.is_visible():
                confirm_btn.click(force=True)
                print("[Draft Handler] Confirmed reference doc selection.")
            else:
                print("[Draft Handler] Confirm button missing.")

            _debug_dump(page, "after_ref_confirm")

            # Check if popup is closed (Success check)
            time.sleep(1.0)
            if not popup.is_visible():
                 print("[Draft Handler] Reference popup successfully closed.")
            else:
                 print("[Draft Handler] Reference popup still open (Did Add/Confirm fail?).")

        except Exception as e:
            print(f"[Draft Handler] Ref Error: {e}")
            _debug_dump(page, "ref_error_state")

        # ============================================================
        # Inject Report Body
        # ============================================================
        # ============================================================
        # Inject Report Body
        # ============================================================
        _inject_report_body(page, trip_data)
        time.sleep(1.0)

        # ============================================================
        # Finalization: Click 'Reflect' (반영) button in body
        # ============================================================
        print("[Draft Handler] Finalizing: Clicking body 'Reflect' button...")
        try:
            # Selector provided by user: div.docuBtn.docSave
            body_reflect_btn = page.locator(".docuBtn.docSave, .btn_save, button:has-text('반영')").last
            
            if body_reflect_btn.count() > 0:
                # Ensure we are not clicking a leftover popup button
                # Scope to body or ensure it's not in a dialog
                if body_reflect_btn.is_visible():
                    print("[Draft Handler] Found body 'Reflect' button. Clicking...")
                    body_reflect_btn.click(force=True)
                    time.sleep(1.0)
                else:
                    print("[Draft Handler] Body 'Reflect' button found but not visible.")
            else:
                print("[Draft Handler] Body 'Reflect' button not found.")
                
        except Exception as e:
            print(f"[Draft Handler] Body Reflect Button Error: {e}")

        # ============================================================
        # Done
        # ============================================================
        msg = f"Draft Created!\nTitle: {new_title}"
        if not title_filled:
            msg += "\n(Title input not filled - check debug_before_title_fill.png)"
        return True, msg

    except Exception as e:
        print(f"[Draft Handler] Error: {e}")
        _debug_dump(page, "fatal_error_state")
        return False, f"Error: {str(e)}"


def _inject_report_body(page, trip_data=None):
    """
    Helper function to inject report body content from 'report_template.html'.
    Separated to ensure stability of the main drafting logic.
    """
    print(f"[Draft Handler] Injecting report body content (via helper)... Data: {trip_data}")
    try:
        template_path = os.path.join(os.path.dirname(__file__), "report_template.html")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                # Read strictly for evaluate argument
                raw_html = f.read()

            # Perform Placeholders Replacement
            if trip_data:
                # Default empty if missing
                period = trip_data.get("trip_period", "")
                dest = trip_data.get("destination", "")
                dept = trip_data.get("dept", "")
                name = trip_data.get("name", "")
                pos = trip_data.get("position", "")
                
                raw_html = raw_html.replace("{{TRIP_PERIOD}}", period)
                raw_html = raw_html.replace("{{DESTINATION}}", dest)
                raw_html = raw_html.replace("{{DEPT}}", dept)
                raw_html = raw_html.replace("{{NAME}}", name)
                raw_html = raw_html.replace("{{POSITION}}", pos)
            else:
                # Remove placeholders if no data
                raw_html = raw_html.replace("{{TRIP_PERIOD}}", "").replace("{{DESTINATION}}", "")
                raw_html = raw_html.replace("{{DEPT}}", "").replace("{{NAME}}", "").replace("{{POSITION}}", "")

            # Wait for iframe availability
            page.wait_for_selector("#editorView_1", state="attached", timeout=10000)
            
            # [Stabilization] Wait for the Editor to initialize and load the Default Header (Form System).
            # If we inject too early (into an empty body), the system might skip loading the header, stripping the form.
            print("[Draft Handler] Waiting for existing header content in editor...")
            header_found = False
            for _ in range(15):  # Wait up to ~15 seconds
                check_script = """
                    () => {
                        var iframe = document.getElementById('editorView_1');
                        if (iframe) {
                            var doc = iframe.contentDocument || iframe.contentWindow.document;
                            if (doc && doc.body && doc.body.innerText.length > 20) {
                                return doc.body.innerText.includes("문서번호") || doc.body.innerText.includes("결재");
                            }
                        }
                        return false;
                    }
                """
                if page.evaluate(check_script):
                    header_found = True
                    print("[Draft Handler] Existing header found. Proceeding to append.")
                    break
                time.sleep(1.0)
            
            if not header_found:
                print("[Draft Handler] Warning: Document header not detected. Injecting anyway...")
            
            # Execute JS to set content
            # [Modification] Use insertAdjacentHTML to append instead of overwrite.
            # This preserves existing headers/form layout if they exist in the editor body.
            # We clear only if we are sure (but usually better to append to the end).
            js_script = """
                (html) => {
                    var iframe = document.getElementById('editorView_1');
                    if (iframe) {
                        var doc = iframe.contentDocument || iframe.contentWindow.document;
                        if (doc && doc.body) {
                            // Append to the end of the body
                            doc.body.insertAdjacentHTML('beforeend', html);
                            return true;
                        }
                    }
                    return false;
                }
            """
            result = page.evaluate(js_script, raw_html)
            
            if result:
                print("[Draft Handler] Body content injected successfully.")
            else:
                print("[Draft Handler] Failed to inject body content (iframe or doc not found).")
        else:
            print("[Draft Handler] Template file 'report_template.html' not found.")

    except Exception as e:
        print(f"[Draft Handler] Body Injection Error: {e}")
