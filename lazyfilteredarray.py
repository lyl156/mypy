class LazyArray:
    def __init__(self, length, generator_fn):
        self._length = length
        self._generator_fn = generator_fn
        self._cache = {}

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(self._length))]
        elif isinstance(index, int):
            if index < 0:
                index += self._length
            if 0 <= index < self._length:
                if index not in self._cache:
                    self._cache[index] = self._generator_fn(index)
                return self._cache[index]
            else:
                raise IndexError("Index out of bounds")
        else:
            raise TypeError("Invalid argument type")

    def __iter__(self):
        for i in range(self._length):
            yield self[i]

    def map(self, func):
        # 返回新的 LazyArray，组合函数
        return LazyArray(self._length, lambda i: func(self[i]))

    def filter(self, predicate):
        # 返回一个 LazyFilteredArray，对索引重新定义
        return LazyFilteredArray(self, predicate)

class LazyFilteredArray:
    def __init__(self, source_array, predicate):
        self._source = source_array
        self._predicate = predicate
        self._filtered_indices = None  # 延迟计算

    def _compute_filtered_indices(self):
        if self._filtered_indices is None:
            self._filtered_indices = [
                i for i in range(len(self._source)) if self._predicate(self._source[i])
            ]

    def __len__(self):
        self._compute_filtered_indices()
        return len(self._filtered_indices)

    def __getitem__(self, index):
        self._compute_filtered_indices()
        if isinstance(index, int):
            if index < 0:
                index += len(self)
            if 0 <= index < len(self):
                source_index = self._filtered_indices[index]
                return self._source[source_index]
            else:
                raise IndexError("Index out of bounds")
        elif isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        else:
            raise TypeError("Invalid argument type")

    def __iter__(self):
        self._compute_filtered_indices()
        for i in self._filtered_indices:
            yield self._source[i]

    def map(self, func):
        # 支持继续链式 map
        return LazyArray(len(self), lambda i: func(self[i]))

    def filter(self, predicate):
        # 多层 filter 链式调用
        return LazyFilteredArray(self, predicate)
    
    def reduce(self, func):
        from functools import reduce as functools_reduce
        """与 functools.reduce 一致，必须至少有一个元素，否则报错"""
        return functools_reduce(func, self)

    def fold(self, initial, func):
        result = initial
        for item in self:
            result = func(result, item)
        return result
    
    def groupBy(self, key_fn):
        from collections import defaultdict
        groups = defaultdict(list)
        for item in self:
            key = key_fn(item)
            groups[key].append(item)
        return groups
    
# TODO: .window(size, step=1), .join(other, key_fn1, key_fn2)
# TODO: .distinct(), .flatMap(fn)
# TODO: 加入 broadcast 与 zip 多输入支持（map(lambda x, y: ...)）
# TODO: 使用生成器而非预加载索引，进一步减少内存
# TODO: .materialize() → 真实 list
# TODO: .numpy() / .torch() → 与 NumPy / PyTorch 对接
# TODO: 编译计算图（e.g. lazy JIT trace）→ 像 PyTorch FX/Graph 模块

arr = LazyArray(10, lambda x: x)
result = arr.map(lambda x: x * 3).filter(lambda x: x % 2 == 0).map(str)

print(list(result))  # ['0', '6', '12', '18', '24']