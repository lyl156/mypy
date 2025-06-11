import asyncio
import aiohttp
import logging
import time
from typing import Optional, Dict, Any, List

from profiler2 import async_profile_time_to_file

# 初始化 logger
logger = logging.getLogger("data_monitor")
handler = logging.FileHandler("data_monitor.log")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

# 儲存 profile log
prof_logs = []

class BaseSource:
    url: str
    last_seen_id: Optional[str] = None

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        try:
            async with self.session.get(self.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            logger.error(f"❌ fetch_data 錯誤 ({self.url}): {e}")
            return None

    def extract_id(self, data: Dict[str, Any]) -> Optional[str]:
        return data.get("id")

    def prepare_forward_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    async def forward_data(self, data: Dict[str, Any]) -> None:
        try:
            async with self.session.post("https://example.com/api/receive", json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                logger.info(f"✅ 成功轉發 ID {data.get('id')}")
        except Exception as e:
            logger.error(f"❌ forward_data 發生錯誤: {e}")

    async def monitor(self):
        data = await self.fetch_data()
        if data:
            current_id = self.extract_id(data)
            if current_id and current_id != self.last_seen_id:
                await self.forward_data(self.prepare_forward_data(data))
                self.last_seen_id = current_id
            else:
                logger.info(f"🟡 [{self.__class__.__name__}] ID 相同（{current_id}），略過")
        else:
            logger.warning(f"⚠️ [{self.__class__.__name__}] 回傳資料為空或格式錯誤")

class SourceA(BaseSource):
    url = "https://example.com/source_a/data"

    def prepare_forward_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"source": "source_a", **data}

class SourceB(BaseSource):
    url = "https://example.com/source_b/data"

    def prepare_forward_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"source": "source_b", **data}

@async_profile_time_to_file(prof_logs, logger)
async def monitor_loop():
    timeout = aiohttp.ClientTimeout(total=15)
    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        sources: List[BaseSource] = [SourceA(session), SourceB(session)]

        while True:
            tasks = [source.monitor() for source in sources]
            await asyncio.gather(*tasks)
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        logger.info("🛑 中止程式")
    except Exception as e:
        logger.exception(f"‼️ 主迴圈例外: {e}")
