import time
import logging
from functools import wraps
import asyncio

# 建議設好 log（或你可以改成 print）
logging.basicConfig(level=logging.INFO)

def profile_time(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        end = time.perf_counter()
        logging.info(f"[{fn.__name__}] 執行時間: {end - start:.6f} 秒")
        return result
    return wrapper

def async_profile_time(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await fn(*args, **kwargs)
        end = time.perf_counter()
        logging.info(f"[{fn.__name__}] 執行時間: {end - start:.6f} 秒")
        return result
    return wrapper


import inspect

def profile_all_methods_mixed(cls):
    for attr_name, attr in cls.__dict__.items():
        if callable(attr) and not attr_name.startswith("__"):
            if inspect.iscoroutinefunction(attr):
                setattr(cls, attr_name, async_profile_time(attr))
            else:
                setattr(cls, attr_name, profile_time(attr))
    return cls

@profile_all_methods_mixed
class Worker:
    def work(self):
        time.sleep(0.3)

    async def async_work(self):
        await asyncio.sleep(0.5)

# 測試
w = Worker()
w.work()

asyncio.run(w.async_work())