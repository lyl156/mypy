# run_fetch (sync wrapper)
#   └── asyncio.run(fetch_all(...))              # 真正進入 event loop
#         └── fetch_all(...)                     # 創建任務 + 管理併發 + 回收結果
#               └── fetch_one(...)               # 每一個 HTTP 請求任務

import asyncio
import aiohttp
import random
import time
from typing import List, Dict, Tuple, Optional

MAX_CONCURRENCY = 10  # 同時最多 10 個請求
MAX_RETRY = 3         # 最多重試次數

async def fetch_one(
    sem: asyncio.Semaphore,
    session: aiohttp.ClientSession,
    id_: int,
    base_url: str,
    max_retry_wait: int = 300
) -> Tuple[int, Optional[str]]:
    url = f"{base_url}{id_}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MyBot/1.0)"
    }

    async with sem:
        for attempt in range(1, MAX_RETRY + 1):
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 429:
                        retry_after = resp.headers.get("Retry-After")
                        wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 5
                        wait_time = min(wait_time, max_retry_wait)
                        print(f"[RateLimit] ID {id_} 第 {attempt} 次遭限流，等待 {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    resp.raise_for_status()
                    data = await resp.text()
                    return id_, data
            except Exception as e:
                print(f"[Error] ID {id_} 嘗試 {attempt}/{MAX_RETRY} 失敗：{e}")
                await asyncio.sleep(1 + attempt * 0.5)  # 指數退避
        return id_, None  # 最終失敗

async def fetch_all(
    ids: List[int],
    base_url: str = "https://twitter.com/get/",
    proxy: Optional[str] = None
) -> Tuple[Dict[int, str], List[int]]:
    results: Dict[int, str] = {}
    failed: List[int] = []
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY, ssl=False)

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        if proxy:
            session._default_headers.clear()  # 清空多餘 header，防止部分 proxy 驗證失敗

        tasks = [
            fetch_one(sem, session, id_, base_url)
            for id_ in ids
        ]
        for future in asyncio.as_completed(tasks, timeout = 15.0):
            try:
                id_, data = await future
                if data is not None:
                    results[id_] = data
                else:
                    failed.append(id_)
            except asyncio.TimeoutError:
                print("[Timeout] 單一 task 超時")
                failed.append(None)
            except Exception as e:
                print(f"[Error] 任務錯誤：{e}")
        failed.append(None)
    return results, failed

# ✅ 用法
def run_fetch(ids: List[int], base_url: str = "https://twitter.com/get/", proxy: Optional[str] = None) -> None:
    start = time.time()
    results, failed = asyncio.run(fetch_all(ids, base_url, proxy))
    print("成功數量:", len(results))
    print("失敗 ID:", failed)
    print("耗時: %.2f 秒" % (time.time() - start))

if __name__ == "__main__":
    test_ids = list(range(101, 121))  # 模擬 20 筆 ID
    run_fetch(test_ids, proxy=None)  # 可放 proxy="http://127.0.0.1:7890"
