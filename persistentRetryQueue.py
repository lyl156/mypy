import asyncio
import httpx
import json
import os
from typing import List, Dict, Optional, Tuple

MAX_CONCURRENCY = 10
MAX_RETRY = 3
FAILURE_FILE = "failed_ids.json"

class PersistentRetryQueue:
    def __init__(self, ids: List[int], retry_limit: int = MAX_RETRY):
        self.retry_limit = retry_limit
        self.queue: Dict[int, int] = {id_: 0 for id_ in ids}  # id_: retry count
        self.failed: List[int] = []

    def get_pending_ids(self) -> List[int]:
        return list(self.queue.keys())

    def should_retry(self, id_: int) -> bool:
        return self.queue.get(id_, 0) < self.retry_limit

    def mark_failure(self, id_: int):
        self.queue[id_] += 1
        if not self.should_retry(id_):
            self.failed.append(id_)
            del self.queue[id_]

    def mark_success(self, id_: int):
        self.queue.pop(id_, None)

    def save_failures(self, path: str = FAILURE_FILE):
        with open(path, "w") as f:
            json.dump(self.failed, f, indent=2)
        print(f"[Write] 寫入失敗 ID 至 {path}")

async def fetch_one(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    id_: int,
    base_url: str,
    timeout: float = 10.0
) -> Tuple[int, Optional[str]]:
    url = f"{base_url}{id_}"
    headers = {"User-Agent": "Mozilla/5.0"}

    async with sem:
        try:
            resp = await client.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                await asyncio.sleep(min(retry_after, 60))
                raise TimeoutError(f"Rate limited: ID {id_}")
            resp.raise_for_status()
            return id_, resp.text
        except Exception as e:
            print(f"[Error] ID {id_} failed: {e}")
            return id_, None
        
def on_task_done(task: asyncio.Task):
    try:
        result = task.result()  # 若有 exception，這裡會 raise
        # 可選：額外 log 或 debug 用
        # print("Task completed successfully:", result)
    except Exception as e:
        print(f"[on_done] Task exception caught: {e}")
        
async def run_retry_queue(
    queue: PersistentRetryQueue,
    base_url: str,
    proxy: Optional[str] = None
) -> Dict[int, str]:
    results: Dict[int, str] = {}
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async with httpx.AsyncClient(proxies=proxy, timeout=15.0) as client:
        while queue.get_pending_ids():
            pending_ids = queue.get_pending_ids()

            tasks = []
            for id_ in pending_ids:
                coro = fetch_one(sem, client, id_, base_url)
                task = asyncio.create_task(coro)
                task.add_done_callback(on_task_done)  # ✅ 加上 callback
                tasks.append(task)

            for future in asyncio.as_completed(tasks):
                try:
                    id_, data = await future
                    if data is not None:
                        results[id_] = data
                        queue.mark_success(id_)
                    else:
                        queue.mark_failure(id_)
                except Exception as e:
                    # ✅ 還是建議這裡再加一次 try/except
                    print(f"[main] Task failed: {e}")

    queue.save_failures()
    return results

def run(ids: List[int], base_url: str = "https://twitter.com/get/", proxy: Optional[str] = None):
    queue = PersistentRetryQueue(ids)
    results = asyncio.run(run_retry_queue(queue, base_url, proxy))
    print(f"成功數量: {len(results)}")
    print(f"寫入失敗檔案: {FAILURE_FILE}")


if __name__ == "__main__":
    id_list = list(range(1001, 1021))  # 模擬 20 筆 ID
    run(id_list)
