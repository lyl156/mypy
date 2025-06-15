from bs4 import BeautifulSoup

def get_selector_by_text(soup: BeautifulSoup, text: str) -> str:
    """
    根據文字找出對應的 CSS Selector（例如 span.author）

    :param soup: BeautifulSoup 解析後的物件
    :param text: 你要找的文字內容（需完整包含）
    :return: CSS Selector 字串，例如 'span.author'，如果找不到回傳 None
    """
    node = soup.find(string=lambda s: s and text in s)
    if not node:
        return None

    tag = node.parent  # 取得父標籤

    tag_name = tag.name
    class_list = tag.get("class", [])

    # 構造 CSS Selector：標籤名 + 多個 class 名
    if class_list:
        selector = tag_name + "." + ".".join(class_list)
    else:
        selector = tag_name

    return selector


from bs4 import BeautifulSoup, Tag

def get_element_by_text(soup: BeautifulSoup, keyword: str) -> dict:
    """
    根據文字模糊搜尋，找出該文字所在元素的 CSS Selector 與 Tag。

    :param soup: BeautifulSoup 對象
    :param keyword: 想搜尋的關鍵字（模糊匹配）
    :return: dict 包含 selector, element, text；若找不到則回傳 None
    """
    node = soup.find(string=lambda s: s and keyword in s)
    if not node:
        return None

    tag: Tag = node.parent

    selector_parts = []

    # Step 1: 優先使用 ID
    if tag.has_attr("id"):
        selector_parts.append(f"#{tag['id']}")
    else:
        base = tag.name or ""
        classes = tag.get("class", [])
        if classes:
            base += "." + ".".join(classes)
        selector_parts.append(base)

    # Step 2: 向上找一層有 class 或 id 的父元素當前綴
    parent = tag.find_parent()
    while parent and parent.name != "[document]":
        if parent.has_attr("id"):
            selector_parts.insert(0, f"#{parent['id']}")
            break
        elif parent.has_attr("class"):
            base = parent.name + "." + ".".join(parent.get("class", []))
            selector_parts.insert(0, base)
            break
        parent = parent.find_parent()

    full_selector = " ".join(selector_parts)

    return {
        "selector": full_selector,
        "element": tag,
        "text": tag.get_text(strip=True)
    }

def get_element_by_text(soup: BeautifulSoup, keyword: str, exact_match=False) -> dict:
    """
    :param exact_match: 如果為 True，則完全匹配文字；否則模糊包含
    """
    if exact_match:
        node = soup.find(string=lambda s: s and s.strip() == keyword)
    else:
        node = soup.find(string=lambda s: s and keyword in s)

    if not node:
        return None

    tag: Tag = node.parent

    selector_parts = []

    if tag.has_attr("id"):
        selector_parts.append(f"#{tag['id']}")
    else:
        base = tag.name or ""
        classes = tag.get("class", [])
        if classes:
            base += "." + ".".join(classes)
        selector_parts.append(base)

    parent = tag.find_parent()
    while parent and parent.name != "[document]":
        if parent.has_attr("id"):
            selector_parts.insert(0, f"#{parent['id']}")
            break
        elif parent.has_attr("class"):
            base = parent.name + "." + ".".join(parent.get("class", []))
            selector_parts.insert(0, base)
            break
        parent = parent.find_parent()

    full_selector = " ".join(selector_parts)

    return {
        "selector": full_selector,
        "element": tag,
        "text": tag.get_text(strip=True)
    }


if __name__ == "__main__":
    html = """
    <div id="main">
    <div class="news-block">
        <h2 class="headline">今天是個好天氣</h2>
        <p>天氣晴朗，適合出遊。</p>
        <span class="author highlight">記者: 小明</span>
    </div>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")

    result = get_element_by_text(soup, "小明")

    print("⚙️ Selector:", result["selector"])
    print("🧱 Element Tag:", result["element"])
    print("📄 Text Content:", result["text"])

    # 驗證 selector 可用
    print("✅ 用 select() 找到同元素嗎？", soup.select_one(result["selector"]) == result["element"])

    # 用在爬蟲流程中
    selector = get_element_by_text(soup, "商品名稱")["selector"]
    text = soup.select_one(selector).text

