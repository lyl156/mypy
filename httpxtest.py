import asyncio
import httpx
import random
import time
from typing import List, Dict, Tuple, Optional

MAX_CONCURRENCY = 10
MAX_RETRY = 3

async def fetch_one(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
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
                resp = await client.get(url, headers=headers, timeout=10.0)
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 5
                    wait_time = min(wait_time, max_retry_wait)
                    print(f"[RateLimit] ID {id_} 第 {attempt} 次遭限流，等待 {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                resp.raise_for_status()
                return id_, resp.text
            except Exception as e:
                print(f"[Error] ID {id_} 嘗試 {attempt}/{MAX_RETRY} 失敗：{e}")
                await asyncio.sleep(1 + attempt * 0.5)
        return id_, None

async def fetch_all(
    ids: List[int],
    base_url: str = "https://twitter.com/get/",
    proxy: Optional[str] = None
) -> Tuple[Dict[int, str], List[int]]:
    results: Dict[int, str] = {}
    failed: List[int] = []
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async with httpx.AsyncClient(proxies=proxy, timeout=15.0) as client:
        task_map = {}  # 對應 future <-> id

        for id_ in ids:
            coro = fetch_one(sem, client, id_, base_url)
            task = asyncio.create_task(asyncio.wait_for(coro, timeout=15.0))
            task_map[task] = id_

        for future in asyncio.as_completed(task_map.keys()):
            id_ = task_map[future]
            try:
                id_result, data = await future
                if data is not None:
                    results[id_result] = data
                else:
                    print(f"[Fail] ID {id_result} 回傳空資料")
                    failed.append(id_result)
            except asyncio.TimeoutError:
                print(f"[Timeout] ID {id_} 超時")
                failed.append(id_)
            except Exception as e:
                print(f"[Error] ID {id_} 發生錯誤：{e}")
                failed.append(id_)

    return results, failed


def run_fetch(ids: List[int], base_url: str = "https://twitter.com/get/", proxy: Optional[str] = None) -> None:
    start = time.time()
    results, failed = asyncio.run(fetch_all(ids, base_url, proxy))
    print("成功數量:", len(results))
    print("失敗 ID:", failed)
    print("耗時: %.2f 秒" % (time.time() - start))

if __name__ == "__main__":
    test_ids = list(range(1001, 1021))
    run_fetch(test_ids, proxy=None)  # or proxy="http://127.0.0.1:7890"
