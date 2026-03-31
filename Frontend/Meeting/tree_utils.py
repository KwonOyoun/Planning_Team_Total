
def expand_year_and_team(target_frame, year: int):
    year = str(year)

    # 1️⃣ 연도 폴더
    target_frame.wait_for_selector(
        f'div[data-tree-node-key="y|{year}"]',
        timeout=30000
    )
    target_frame.locator(
        f'div[data-tree-node-key="y|{year}"] img[class^="OBTTreeView_imageUrl"]'
    ).first.click(force=True)

    target_frame.wait_for_timeout(300)

    # 2️⃣ 기획1팀 (w|602025)
    target_frame.wait_for_selector(
        'div[data-tree-node-key="w|602025"] img',
        timeout=10000
    )
    target_frame.locator(
        'div[data-tree-node-key="w|602025"] img[class^="OBTTreeView_imageUrl"]'
    ).first.click(force=True)

    target_frame.wait_for_timeout(300)

    # 일반기안 (JS 이벤트)
    target_frame.evaluate("""
    () => {
      const node = document.querySelector(
        'div.OBTTreeView_treeNodeContents__1nPxq[data-tree-node-key="a|1122"]'
      );
      node.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      node.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
      node.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }
    """)
    
    target_frame.wait_for_timeout(300)

# wotjr1207!