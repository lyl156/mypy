import time
import random
import requests
from typing import Optional, List, Dict, Tuple
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries(
    proxy_url: Optional[str] = None,
    total_retries: int = 3,
    backoff_factor: float = 0.5,
) -> Session:
    session = requests.Session()

    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    if proxy_url:
        session.proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }

    return session

def fetch_with_rate_limit_handling(
    session: Session,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    max_retry_wait: int = 300
) -> str:
    """自動處理 Rate Limit 與 Retry-After header"""
    while True:
        try:
            res = session.get(url, headers=headers, timeout=10)
            if res.status_code == 429:
                retry_after = res.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 5
                wait_time = min(wait_time, max_retry_wait)
                print(f"[Rate Limit] 等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
                continue

            res.raise_for_status()
            return res.text  # 或 response.json() 視實際需求

        except requests.exceptions.RequestException as e:
            raise e

def fetch_twitter_data(
    ids: List[int],
    base_url: str = "https://twitter.com/get/",
    proxy: Optional[str] = None
) -> Tuple[Dict[int, str], List[int]]:
    session = create_session_with_retries(proxy_url=proxy)

    headers: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (compatible; MyBot /1.0)",
        # "Authorization": "Bearer YOUR_TOKEN"
    }

    results: Dict[int, str] = {}
    failed_ids: List[int] = []

    for id_ in ids:
        url = f"{base_url}{id_}"
        try:
            print(f"[Fetch] ID={id_}")
            data = fetch_with_rate_limit_handling(session, url, headers=headers)
            results[id_] = data
        except Exception as e:
            print(f"[Error] ID {id_} failed: {e}")
            failed_ids.append(id_)

        time.sleep(random.uniform(0.2, 0.5))  # 隨機 delay 模擬人類行為

    return results, failed_ids

# ✅ 使用範例
if __name__ == "__main__":
    ids: List[int] = [101, 202, 303, 404]
    proxy: Optional[str] = "http://127.0.0.1:7890"  # 或 None
    data, failed = fetch_twitter_data(ids, proxy=proxy)
    print("成功數量:", len(data))
    print("失敗 ID:", failed)

    
