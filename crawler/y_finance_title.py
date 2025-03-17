import requests
from bs4 import BeautifulSoup

# 目标URL
url = 'https://finance.yahoo.com/'


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 发送HTTP请求
response = requests.get(url, headers=headers)
response.raise_for_status()


with open("yahoo.html", "w", encoding="utf-8") as f:
    f.write(response.text)
print("HTML 已保存到 yahoo.html，请用浏览器打开")


# 解析HTML
soup = BeautifulSoup(response.text, 'html.parser')


# 查找所有可能包含新闻标题的标签
# 由于不同的新闻标题可能位于不同的标签中，这里需要根据实际情况调整
# 以下是一些可能的标签和类名，您需要根据实际的HTML结构进行修改
possible_selectors = [
    ('h3', 'Mb(5px)'),
    ('h2', 'Mb(10px)'),
    ('a', 'Fw(b)'),
    ('div', "content yf-1jvnfga btmMargin")
]

news_titles = []

for tag, class_name in possible_selectors:
    titles = soup.find_all(tag, class_=class_name)
    for title in titles:
        news_titles.append(title.get_text(strip=True))

# 输出新闻标题
print('最新新闻标题：')
for idx, title in enumerate(news_titles, 1):
    print(f'{idx}. {title}')


news_items = soup.find_all("div", class_="content yf-1jvnfga btmMargin")

# <div class="titles font-medium-static yf-1jvnfga"><h2 class="tw-line-clamp-3 yf-1jvnfga">Fed set to lay down a marker on Trump tariffs</h2> <p cla
# 提取新闻标题
for item in news_items:
    # 方法 1: 直接从 <h2> 标签提取文本
    h2_tag = item.find("h2", class_="tw-line-clamp-3 yf-1jvnfga")
    if h2_tag:
        print("标题:", h2_tag.text.strip())

    # 方法 2: 从 <a> 标签的 title 属性提取
    a_tag = item.find("a", class_="tw-w-full titles-link noUnderline   yf-1xqzjha")
    if a_tag and a_tag.has_attr("title"):
        print("标题（来自 <a> title 属性）:", a_tag["title"])

    # 获取新闻链接
    if a_tag and a_tag.has_attr("href"):
        print("链接:", "https://finance.yahoo.com" + a_tag["href"])

    print("-" * 80)