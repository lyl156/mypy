import asyncio

class LazyTask:
    def __init__(self, coro_func, *args, **kwargs):
        self._coro_func = coro_func
        self._args = args
        self._kwargs = kwargs
        self._task = None

    def ensure_task(self):
        if self._task is None:
            coro = self._coro_func(*self._args, **self._kwargs)
            self._task = asyncio.create_task(coro)
        return self._task

    def __await__(self):
        return self.ensure_task().__await__()

async def slow_init(x):
    print(f"開始執行: {x}")
    await asyncio.sleep(1)
    return x * 2


async def main():
    lazy = LazyTask(slow_init, 5)

    print("準備好了，現在才執行")

    result = await lazy
    print("結果是：", result)

if __name__ == "__main__":
    asyncio.run(main())
