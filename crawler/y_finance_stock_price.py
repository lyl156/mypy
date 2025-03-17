import requests
from bs4 import BeautifulSoup

# 目标URL
url = 'https://finance.yahoo.com/quote/AAPL'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 发送HTTP请求
response = requests.get(url, headers=headers)
response.raise_for_status()

with open("yahoo_aapl.html", "w", encoding="utf-8") as f:
    f.write(response.text)
print("HTML 已保存到 yahoo_aapl.html，请用浏览器打开")

# 解析HTML
soup = BeautifulSoup(response.text, 'html.parser')

# 查找股票价格所在的标签
price_span = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
price = price_span.text if price_span else 'N/A'

print(f'AAPL 当前股价: {price}')
