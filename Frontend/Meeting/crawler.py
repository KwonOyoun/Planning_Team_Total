def get_meeting_list(session):
    frame = session.target_frame

    frame.wait_for_selector('ul.tableBody', timeout=30000)
    frame.wait_for_selector('ul.tableBody li.h-box.listChk', timeout=30000)

    rows = frame.locator('ul.tableBody li.h-box.listChk')
    meetings = []

    for i in range(rows.count()):
        row = rows.nth(i)

        # 제목
        title_el = row.locator('div.OBTTooltip_root__3Bfdz.title span')
        if title_el.count() == 0:
            continue

        title = title_el.first.inner_text().strip()
        if "회의" not in title:
            continue

        # ✅ 기안자
        author_el = row.locator('div.nameDiv.ellipsis')
        author = author_el.first.inner_text().strip() if author_el.count() else ""

        # ✅ 기안일자
        date_el = row.locator('div.dateText')
        date = date_el.first.inner_text().strip() if date_el.count() else ""

        meetings.append({
            "dom_index": i,
            "title": title,
            "author": author,
            "date": date
        })

    return meetings


def open_meeting_by_index(session, index: int):
    frame = session.target_frame
    rows = frame.locator('ul.tableBody li.h-box.listChk')

    row = rows.nth(index)
    title_span = row.locator('div.OBTTooltip_root__3Bfdz.title span').first

    title_span.scroll_into_view_if_needed()
    frame.wait_for_timeout(200)

    with session.page.expect_popup() as popup_info:
        title_span.click()

    detail_page = popup_info.value
    detail_page.wait_for_load_state("networkidle")

    return detail_page


def crawl_detail_page_text(detail_page):
    detail_page.wait_for_selector(
        "td#divFormContents",
        timeout=30000
    )
    return detail_page.locator("td#divFormContents").inner_text().strip()
