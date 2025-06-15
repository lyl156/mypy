import logging
from bs4 import BeautifulSoup, Tag
from typing import Optional, List, Dict, Union

# 設定 logging
logger = logging.getLogger("SelectorHelper")
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)  # 預設為 INFO，debug 模式會改為 DEBUG

def get_element_by_text(
    soup: BeautifulSoup,
    keyword: str,
    debug: bool = False
) -> Optional[Dict[str, Union[str, Tag]]]:
    """
    根據文字模糊搜尋，找出該文字所在元素的 CSS Selector 與 Tag。

    :param soup: BeautifulSoup 對象
    :param keyword: 想搜尋的關鍵字（模糊匹配）
    :param debug: 是否開啟 debug 日誌
    :return: dict 包含 selector, element, text；若找不到則回傳 None
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    node = soup.find(string=lambda s: s and keyword in s)
    if not node:
        logger.warning(f"❌ 無法找到包含文字：'{keyword}'")
        return None

    tag: Tag = node.parent
    logger.debug(f"🎯 找到文字 '{keyword}' 在標籤：<{tag.name}>")

    selector_parts = []

    if tag.has_attr("id"):
        selector_parts.append(f"#{tag['id']}")
    else:
        base = tag.name or ""
        classes = tag.get("class", [])
        if classes:
            base += "." + ".".join(classes)
        selector_parts.append(base)

    # 向上找第一層 class 或 id 作為上下文
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
    logger.debug(f"🧩 組合出的 selector: {full_selector}")

    return {
        "selector": full_selector,
        "element": tag,
        "text": tag.get_text(strip=True)
    }


def get_elements_by_texts(
    soup: BeautifulSoup,
    keywords: List[str],
    debug: bool = False
) -> Dict[str, Optional[Dict[str, Union[str, Tag]]]]:
    """
    批量搜尋多組關鍵字

    :param soup: BeautifulSoup 對象
    :param keywords: 關鍵字列表
    :param debug: 是否開啟 debug 模式
    :return: 每個關鍵字對應的結果 dict
    """
    results = {}
    for kw in keywords:
        logger.debug(f"🔍 處理關鍵字: {kw}")
        result = get_element_by_text(soup, kw, debug=debug)
        results[kw] = result
    return results

def get_element_with_siblings_by_text(
    soup: BeautifulSoup,
    keyword: str,
    debug: bool = False
) -> Optional[Dict[str, Union[str, Tag, List[str]]]]:
    """
    根據文字模糊搜尋，找出該文字所在的元素，
    並返回其 CSS selector、Tag、本身文字與同一層的其他文字

    :param soup: BeautifulSoup 對象
    :param keyword: 要搜尋的文字（模糊匹配）
    :param debug: 是否開啟 debug 模式
    :return: dict 包含 selector, element, text, siblings_text；找不到則回傳 None
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    node = soup.find(string=lambda s: s and keyword in s)
    if not node:
        logger.warning(f"❌ 無法找到包含文字：'{keyword}'")
        return None

    tag: Tag = node.parent
    logger.debug(f"🎯 找到文字 '{keyword}' 在標籤：<{tag.name}>")

    # 1. 組合 selector
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
    logger.debug(f"🧩 組合出的 selector: {full_selector}")

    # 2. 取得兄弟節點文字
    sibling_tags = tag.parent.find_all(recursive=False)  # 同一層級的所有直接子元素
    siblings_text = []
    for sib in sibling_tags:
        if sib == tag:
            continue  # 自己跳過
        text = sib.get_text(strip=True)
        if text:
            siblings_text.append(text)

    return {
        "selector": full_selector,
        "element": tag,
        "text": tag.get_text(strip=True),
        "siblings_text": siblings_text
    }

if __name__ == "__main__":

    html = """
    <div id="main">
    <div class="news-block">
        <h2 class="headline">今天是個好天氣</h2>
        <p>天氣晴朗，適合出遊。</p>
        <span class="author highlight">記者: 小明</span>
        <span class="editor">編輯: 阿綠</span>
    </div>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")

    results = get_elements_by_texts(soup, ["小明", "阿綠", "不存在的"], debug=True)

    for key, value in results.items():
        print(f"🔑 關鍵字: {key}")
        if value:
            print(f"   Selector: {value['selector']}")
            print(f"   Text: {value['text']}")
        else:
            print("   ❗️ 沒找到")

    # 測試 get_element_with_siblings_by_text

        html = """
    <div id="main">
    <div class="info-box">
        <span class="author">記者: 小明</span>
        <span class="editor">編輯: 阿綠</span>
        <span class="source">來源: 風傳媒</span>
    </div>
    </div>
    """

    soup = BeautifulSoup(html, "html.parser")

    result = get_element_with_siblings_by_text(soup, "小明", debug=True)

    print("⚙️ Selector:", result["selector"])
    print("📄 本身文字:", result["text"])
    print("📚 同層其他文字:", result["siblings_text"])
