from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# 配置 Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 无头模式（不打开浏览器窗口）
options.add_argument("--disable-blink-features=AutomationControlled")  # 规避反爬检测
options.add_argument("--start-maximized")  # 最大化窗口
options.add_argument("--disable-gpu")  # 兼容某些浏览器
options.add_argument("--no-sandbox")  # 适用于 Linux 服务器
options.add_argument("--disable-dev-shm-usage")  # 适用于 Docker

# 启动 WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # 访问 Google
    driver.get("https://www.google.com/")

    # 定位搜索框，输入关键词并回车
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("Python 爬虫")
    search_box.send_keys(Keys.RETURN)

    # 等待搜索结果加载
    time.sleep(2)

    # 爬取第一页的搜索结果
    def get_results():
        results = driver.find_elements(By.XPATH, '//div[@class="tF2Cxc"]')
        for result in results:
            title = result.find_element(By.TAG_NAME, "h3").text
            link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
            print(f"标题: {title}\n链接: {link}\n")

    print("=== 第 1 页结果 ===")
    get_results()

    # 点击“下一页”，获取第 2 页数据
    try:
        next_button = driver.find_element(By.XPATH, '//a[@id="pnnext"]')
        next_button.click()
        time.sleep(2)  # 等待下一页加载
        print("\n=== 第 2 页结果 ===")
        get_results()
    except:
        print("\n未找到下一页按钮，可能 Google 限制了访问。")

finally:
    driver.quit()
