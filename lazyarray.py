class LazyArray:
    def __init__(self, length, generator_fn):
        self._length = length
        self._generator_fn = generator_fn
        self._cache = {}

    def __len__(self):
        return self._length


    #定义了 __getitem__ 但没有 __iter__，Python 会尝试用 __getitem__ 从 index=0 开始获取元素，
    # 直到抛出 IndexError，这是一种备选机制（老版本行为），但更推荐明确实现 __iter__。
    def __getitem__(self, index):
        if isinstance(index, slice):  # 支持切片访问
            return [self[i] for i in range(*index.indices(self._length))]
        elif isinstance(index, int):  # index 访问
            if 0 <= index < self._length:
                if index not in self._cache:
                    self._cache[index] = self._generator_fn(index)
                return self._cache[index]
            else:
                raise IndexError("Index out of bounds")
        else:
            raise TypeError("Invalid argument type")

# Python 的迭代协议
#   可迭代对象：只要实现了 __iter__() 方法，返回一个迭代器即可。
#   迭代器：同时实现了 __iter__() 且 __next__() 方法，__iter__() 返回自己。
    def __iter__(self):
        for i in range(self._length):
            yield self[i]

    def __next__(self):
        print(self._length)


# 创建一个 LazyArray，包含 100 个数，每个值是 index 的平方
lazy = LazyArray(100, lambda i: i ** 2)

print(lazy[10])  # 输出 100
print(len(lazy))  # 输出 100

lazy = LazyArray(10, lambda x: x ** 2)

print(lazy[3])         # 输出 9
print(list(lazy[:5]))  # 输出 [0, 1, 4, 9, 16]
print(sum(lazy))       # 输出 285
# print(next(lazy))



# 在 for x in iterator: 循环中：
#   __iter__() 只调用一次，在循环开始时调用，用来获取“真正的迭代器”。

#   __next__() 会被调用多次，每次迭代时调用一次，直到抛出 StopIteration。

# for x in obj: 的机制就是：
#   先调用 obj.__iter__() → 得到迭代器 → 每次迭代调用 __next__() → 遇到 StopIteration 结束循环。

class MyIterator:
    def __init__(self):
        self.current = 0

    def __iter__(self):
        print("调用 __iter__")
        return self  # 自己是迭代器

    def __next__(self):
        print("调用 __next__")
        if self.current >= 3:
            raise StopIteration
        val = self.current
        self.current += 1
        return val

for x in MyIterator():
    print("得到值：", x)