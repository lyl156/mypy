import redis
import time
from typing import Optional


class RedisClient:
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 decode_responses: bool = True):
        pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses
        )
        self.client = redis.Redis(connection_pool=pool)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        return self.client.set(key, value, ex=ex)

    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)

    def ping(self) -> bool:
        return self.client.ping()

    def get_raw_client(self) -> redis.Redis:
        return self.client


class RedisDistributedLock:
    def __init__(self, client: redis.Redis, lock_key: str, timeout: int = 10):
        self.lock = client.lock(lock_key, timeout=timeout)

    def __enter__(self):
        acquired = self.lock.acquire(blocking=True, blocking_timeout=5)
        if not acquired:
            raise TimeoutError("無法取得 Redis 鎖")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock.locked():
            self.lock.release()


if __name__ == "__main__":
    redis_client = RedisClient(host="localhost", port=6379)
    client = redis_client.get_raw_client()

    try:
        # 用 Redis 做些事
        redis_client.set("hello", "world", ex=30)
        print("hello =", redis_client.get("hello"))

        # 使用分布式鎖做一件只能一人做的事
        with RedisDistributedLock(client, "my_lock_key"):
            print("取得鎖，開始關鍵操作")
            time.sleep(3)
            print("操作完成，釋放鎖")

    except TimeoutError as e:
        print("⚠️ 無法取得鎖，跳過這輪任務")
    except redis.RedisError as e:
        print(f"⚠️ Redis 發生錯誤: {e}")
