from playwright.sync_api import sync_playwright, TimeoutError
import re

from openai_client import ask_gpt
from prompt_templates import SORTING_TEMPLATE_PROMPT, WRITING_REPORT_PROMPT

LOGIN_URL = "https://gw.kothea.or.kr/#/login?logout=Y&lang=kr"


class MeetingBrowserSession:
    def __init__(self, headless=False):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.target_frame = None

    def close(self):
        self.browser.close()
        self.p.stop()


def crawl_detail_page_text(detail_page):
    detail_page.wait_for_selector(
        "td#divFormContents",
        state="attached",
        timeout=30000
    )
    return detail_page.locator("td#divFormContents").inner_text().strip()


def js_click(page, selector):
    page.evaluate(f"""
    () => {{
        const el = document.querySelector('{selector}');
        if (el) el.click();
    }}
    """)

# 2026년도 선택시 사용 X
def expand_year_and_team(frame, year: int):
    year = str(year)

    # 연도
    frame.locator(
        f'div[data-tree-node-key="y|{year}"] img'
    ).first.click(force=True)

    frame.wait_for_timeout(200)

    # 팀
    frame.locator(
        'div[data-tree-node-key="w|602025"] img'
    ).first.click(force=True)

    frame.wait_for_timeout(200)

    # 일반기안
    frame.locator(
        'div[data-tree-node-key="a|1122"] img'
    ).first.click(force=True)

    # ✅ 핵심: 목록 갱신 대기
    frame.wait_for_selector(
        'ul.tableBody',
        state="attached",
        timeout=30000
    )

    # ✅ 회의 제목이 등장할 때까지 대기
    frame.wait_for_function("""
        () => {
            const rows = document.querySelectorAll(
                'ul.tableBody li.h-box.listChk'
            );
            return Array.from(rows)
                .some(r => r.innerText.includes('회의'));
        }
    """)

    # ✅ 안정화 딜레이 (짧게)
    frame.wait_for_timeout(300)





def login_and_fetch_meeting_drafts(user_id, password, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # =========================
        # 1️⃣ 로그인
        # =========================
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        print(">>> 페이지 접속 완료")

        page.wait_for_selector('#reqLoginId', timeout=15000)
        page.locator('#reqLoginId:not([disabled])').fill(user_id)
        page.get_by_role("button", name=re.compile("다음|확인|로그인", re.I)).click()

        page.wait_for_selector('#reqLoginPw', timeout=15000)
        page.locator('#reqLoginPw').fill(password)
        page.get_by_role("button", name=re.compile("로그인|확인", re.I)).click()

        page.wait_for_function(
            "() => !location.hash.includes('/login')",
            timeout=15000
        )
        print("[OK] 로그인 성공")

        # =========================
        # 2️⃣ 전자결재(비영리)
        # =========================
        page.wait_for_selector('#sideGnb li.module-item', timeout=30000)

        page.locator(
            '#sideGnb li.module-item',
            has_text="전자결재(비영리)"
        ).first.click()

        print(">>> 전자결재(비영리) 클릭")

        # =========================
        # 3️⃣ 문서함 → 기록물철문서 (JS 클릭)
        # =========================
        page.wait_for_selector('#UCA_UCA4000', timeout=20000)
        js_click(page, '#UCA_UCA4000')
        print(">>> 문서함 클릭")

        page.wait_for_selector('#UCA4030_UCA', timeout=20000)
        js_click(page, '#UCA4030_UCA')
        print(">>> 기록물철문서 클릭")

        # =========================
        # 4️⃣ iframe 진입
        # =========================
        target_frame = next(
            (f for f in page.frames if "ea" in f.url),
            None
        )
        if not target_frame:
            raise RuntimeError("전자결재 iframe 못 찾음")

        # =========================
        # 5️⃣ 연도 -> 기획1팀 → 일반기안
        # =========================
        target_frame.wait_for_selector(
            'div[data-tree-node-key]',
            timeout=30000
        )

        # 2025 폴더
        expand_year_and_team(target_frame, 2025)
    

        target_frame.locator(
            'button[class^="OBTTreeView_treeLabelText"]',
            has_text="기획1팀"
        ).first.click()

        target_frame.locator(
            'button[class^="OBTTreeView_treeLabelText"]',
            has_text="일반기안"
        ).first.click()

        print(">>> 기획1팀 → 일반기안 진입")

        # =========================
        # 6️⃣ 회의 기안 목록 수집
        # =========================
        target_frame.wait_for_selector(
            'ul.tableBody li.h-box.listChk',
            timeout=30000
        )

        meetings = []  # dict 목록으로

        rows = target_frame.locator('ul.tableBody li.h-box.listChk')

        for i in range(rows.count()):
            row = rows.nth(i)

            # 제목
            title_el = row.locator(
                'div.OBTTooltip_root__3Bfdz.title span'
            )
            if title_el.count() == 0:
                continue

            title = title_el.first.inner_text().strip()

            if "회의" not in title:
                continue

            # 기안일
            date = ""
            date_el = row.locator('div.dateText')
            if date_el.count() > 0:
                date = date_el.first.inner_text().strip()

            # 기안자
            author = ""
            author_el = row.locator('div.nameDiv')
            if author_el.count() > 0:
                author = author_el.first.inner_text().strip()

            meetings.append({
                "title": title,
                "author": author,
                "date": date
            })

        print(">>> 회의 기안 목록:", meetings)
        return meetings
    

def crawl_all_meeting_drafts(user_id, password, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # -----------------
        # 1️⃣ 로그인
        # -----------------
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.wait_for_selector('#reqLoginId', timeout=15000)
        page.locator('#reqLoginId:not([disabled])').fill(user_id)
        page.get_by_role("button", name=re.compile("다음|확인|로그인")).click()

        page.wait_for_selector('#reqLoginPw', timeout=15000)
        page.locator('#reqLoginPw').fill(password)
        page.get_by_role("button", name=re.compile("로그인|확인")).click()

        page.wait_for_function(
            "() => !location.hash.includes('/login')",
            timeout=15000
        )

        # -----------------
        # 2️⃣ 전자결재 → 일반기안
        # -----------------
        page.wait_for_selector('#sideGnb li.module-item', timeout=30000)
        page.locator(
            '#sideGnb li.module-item',
            has_text="전자결재(비영리)"
        ).first.click()

        # 2025 폴더 
        expand_year_and_team(target_frame, 2025)


        # JS click (안정성)
        page.evaluate("document.querySelector('#UCA_UCA4000').click()")
        page.evaluate("document.querySelector('#UCA4030_UCA').click()")

        # -----------------
        # 3️⃣ iframe
        # -----------------
        target_frame = next(
            (f for f in page.frames if "ea" in f.url),
            None
        )
        if not target_frame:
            raise RuntimeError("iframe 못 찾음")

        # -----------------
        # 4️⃣ 회의 목록 + 본문 크롤링
        # -----------------
        target_frame.wait_for_selector(
            'ul.tableBody li.h-box.listChk',
            timeout=30000
        )

        rows = target_frame.locator('ul.tableBody li.h-box.listChk')
        results = []

        for i in range(rows.count()):
            row = rows.nth(i)

            title_el = row.locator(
                'div.OBTTooltip_root__3Bfdz.title span'
            )
            if title_el.count() == 0:
                continue

            title = title_el.first.inner_text().strip()
            if "회의" not in title:
                continue

            # 👉 기안 클릭
            title_el.first.click()

            target_frame.wait_for_selector(
                'div[class*="editor"], div.OBTEditor_root',
                timeout=20000
            )

            content_text = target_frame.locator(
                'div[class*="editor"], div.OBTEditor_root'
            ).first.inner_text().strip()

            results.append({
                "index": i,
                "title": title,
                "content_text": content_text
            })

            # 목록으로 복귀
            page.go_back()
            target_frame.wait_for_selector(
                'ul.tableBody li.h-box.listChk',
                timeout=20000
            )

        browser.close()
        return results
    

def crawl_detail_page_text(detail_page):
    detail_page.wait_for_selector(
        "td#divFormContents",
        state="attached",
        timeout=30000
    )
    return detail_page.locator("td#divFormContents").inner_text().strip()


def crawl_one_meeting_with_gpt(
    user_id: str,
    password: str,
    meeting_index: int,          # ⭐ 0-based index (프론트에서 넘기는 index 그대로)
    headless: bool = True,
):
    """
    전략 1:
    회의 하나 클릭할 때마다 Playwright를 새로 띄워서
    로그인 → 메뉴 이동 → 목록 → meeting_index 선택 → 본문 → GPT 까지 처리
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # =========================
        # 0) 접속
        # =========================
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        # =========================
        # 1) 로그인 (1단계 아이디)
        # =========================
        page.wait_for_selector('#reqLoginId', timeout=15000)
        login_id_input = page.locator('#reqLoginId:not([disabled])')

        if login_id_input.count() == 0:
            page.screenshot(path="debug_step1_no_reqLoginId.png", full_page=True)
            browser.close()
            raise RuntimeError("1단계 reqLoginId 입력창을 찾지 못함")

        login_id_input.fill(user_id)
        page.get_by_role("button", name=re.compile("다음|확인|로그인", re.I)).click()

        # =========================
        # 2) 로그인 (2단계 비밀번호)
        # =========================
        try:
            page.wait_for_selector('#reqLoginPw', timeout=15000)
        except TimeoutError:
            page.screenshot(path="debug_step2_no_password.png", full_page=True)
            browser.close()
            raise RuntimeError("2단계 비밀번호 입력창(#reqLoginPw)을 찾지 못함")

        page.locator('#reqLoginPw').fill(password)
        page.get_by_role("button", name=re.compile("로그인|확인", re.I)).click()

        # =========================
        # 3) 로그인 성공 판정
        # =========================
        try:
            page.wait_for_function(
                "() => !location.hash.includes('/login')",
                timeout=15000
            )
        except TimeoutError:
            page.screenshot(path="debug_login_failed.png", full_page=True)
            browser.close()
            raise RuntimeError("로그인 실패 (비밀번호 오류 또는 추가 인증)")

        # =========================
        # 4) 전자결재(비영리) 클릭
        # =========================
        page.wait_for_selector('#sideGnb li.module-item', timeout=30000)
        page.locator('#sideGnb li.module-item', has_text="전자결재(비영리)").first.click()

        # =========================
        # 5) 문서함 → 기록물철문서
        # =========================
        page.wait_for_selector('#UCA_UCA4000', timeout=30000)
        page.locator('#UCA_UCA4000').click()

        page.wait_for_selector('#UCA4030_UCA', timeout=30000)
        page.locator('#UCA4030_UCA').click()

        # =========================
        # 6) iframe 잡기 (ea)
        # =========================
        # ⭐ SPA라서 프레임이 늦게 붙는 경우가 있어 잠깐 대기 + 재탐색
        target_frame = None
        for _ in range(40):  # 최대 약 4초 (100ms * 40)
            for f in page.frames:
                if "ea" in (f.url or ""):
                    target_frame = f
                    break
            if target_frame:
                break
            page.wait_for_timeout(100)

        if not target_frame:
            page.screenshot(path="debug_no_ea_iframe.png", full_page=True)
            browser.close()
            raise RuntimeError("전자결재 iframe 못 찾음")

        # =========================
        # 7) 기획1팀 → 일반기안
        # =========================
        target_frame.wait_for_selector(
            'button[class^="OBTTreeView_treeLabelText"]',
            timeout=30000
        )

        expand_year_and_team(target_frame, 2025, "기획1팀")


        target_frame.locator(
            'button[class^="OBTTreeView_treeLabelText"]',
            has_text="기획1팀"
        ).first.click()

        target_frame.wait_for_selector(
            'button[class^="OBTTreeView_treeLabelText"]:has-text("일반기안")',
            timeout=30000
        )

        target_frame.locator(
            'button[class^="OBTTreeView_treeLabelText"]',
            has_text="일반기안"
        ).first.click()

        # =========================
        # 8) 회의 목록 수집
        # =========================
        target_frame.wait_for_selector(
            'ul.tableBody li.h-box.listChk',
            timeout=30000
        )

        rows = target_frame.locator('ul.tableBody li.h-box.listChk')
        meeting_rows = []  # (row, title)

        for i in range(rows.count()):
            row = rows.nth(i)
            title_span = row.locator('div.OBTTooltip_root__3Bfdz.title span')
            if title_span.count() == 0:
                continue

            title = title_span.first.inner_text().strip()
            if "회의" in title:
                meeting_rows.append((row, title))

        if meeting_index < 0 or meeting_index >= len(meeting_rows):
            browser.close()
            raise ValueError(f"회의 index 범위 초과: {meeting_index} / 총 {len(meeting_rows)}개")

        # =========================
        # 9) 선택 회의 열기 (popup)
        # ⚠️ row는 target_frame 기준인데 popup 대기는 page 기준으로 해도 됨
        # =========================
        row, title = meeting_rows[meeting_index]
        title_span = row.locator('div.OBTTooltip_root__3Bfdz.title span').first
        title_span.scroll_into_view_if_needed()
        page.wait_for_timeout(200)

        with page.expect_popup() as popup_info:
            title_span.click()

        detail_page = popup_info.value
        detail_page.wait_for_load_state("networkidle")

        full_text = crawl_detail_page_text(detail_page)

        # =========================
        # 10) GPT 정리
        # =========================
        prompt = SORTING_TEMPLATE_PROMPT.format(full_text=full_text)
        gpt_result = ask_gpt(prompt)

        browser.close()

        return {
            "title": title,
            "raw_text": full_text,
            "parsed": gpt_result
        }
    

def generate_minutes_body_with_gpt(
    project_name: str,
    meeting_name: str,
    meeting_datetime_text: str,
    meeting_location: str,
    participants: list,
    summary_text: str,
) -> str:

    participant_lines = []
    for i, p in enumerate(participants, start=1):
        dept = p.get("department", "")
        name = p.get("name", "")
        pos = p.get("position", "")

        line = f"({i}) {dept}/{name}"
        if pos:
            line += f"({pos})"
        participant_lines.append(line)

    participants_text = "\n".join(participant_lines) if participant_lines else "None"

    prompt = WRITING_REPORT_PROMPT.format(
        summary_text=summary_text
    )

    return ask_gpt(prompt).strip()