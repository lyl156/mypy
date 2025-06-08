import time
import traceback
from functools import wraps
import logging
import inspect

def profile_time_to_file(log_list, logger):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration = time.perf_counter() - start
                log_list.append({
                    "method": fn.__qualname__,
                    "duration": duration,
                    "args": args,
                    "kwargs": kwargs,
                    "exception": None,
                })
                logger.info(f"[{fn.__qualname__}] 耗時: {duration:.6f} 秒")
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                tb = traceback.format_exc()
                log_list.append({
                    "method": fn.__qualname__,
                    "duration": duration,
                    "args": args,
                    "kwargs": kwargs,
                    "exception": str(e),
                    "traceback": tb,
                })
                logger.error(f"[{fn.__qualname__}] ❌ 發生例外: {e}\n{tb}")
                raise  # 繼續丟出例外讓外部處理
        return wrapper
    return decorator


def async_profile_time_to_file(log_list, logger):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
                duration = time.perf_counter() - start
                log_list.append({
                    "method": fn.__qualname__,
                    "duration": duration,
                    "args": args,
                    "kwargs": kwargs,
                    "exception": None,
                })
                logger.info(f"[{fn.__qualname__}] 耗時: {duration:.6f} 秒 (async)")
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                tb = traceback.format_exc()
                log_list.append({
                    "method": fn.__qualname__,
                    "duration": duration,
                    "args": args,
                    "kwargs": kwargs,
                    "exception": str(e),
                    "traceback": tb,
                })
                logger.error(f"[{fn.__qualname__}] ❌ 發生例外: {e}\n{tb}")
                raise
        return wrapper
    return decorator


def profile_selected_methods_mixed(name_patterns=None, log_file="method_profile.log"):
    name_patterns = name_patterns or []

    def decorator(cls):
        cls._profiled_logs = []

        logger = logging.getLogger(f"profile.{cls.__name__}")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.propagate = False

        for attr_name, attr in cls.__dict__.items():
            if attr_name.startswith("__") or not callable(attr):
                continue
            if not any(p in attr_name for p in name_patterns):
                continue

            if inspect.iscoroutinefunction(attr):
                wrapped = async_profile_time_to_file(cls._profiled_logs, logger)(attr)
            else:
                wrapped = profile_time_to_file(cls._profiled_logs, logger)(attr)

            setattr(cls, attr_name, wrapped)

        return cls
    return decorator

import asyncio
import time

@profile_selected_methods_mixed(name_patterns=["run", "fail"], log_file="profile_with_error.log")
class Test:
    def run_ok(self):
        time.sleep(0.1)
        return "OK"

    def fail_sync(self):
        raise ValueError("同步錯誤")

    async def fail_async(self):
        raise RuntimeError("非同步錯誤")

t = Test()
try:
    t.run_ok()
    t.fail_sync()
except Exception:
    pass

async def test_async_fail():
    try:
        await t.fail_async()
    except Exception:
        pass

asyncio.run(test_async_fail())

print("\n執行記錄（含錯誤）：")
# for log in Test._profiled_logs:
#     print(log)
