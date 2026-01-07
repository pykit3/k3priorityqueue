# k3priorityqueue

[![Action-CI](https://github.com/pykit3/k3priorityqueue/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3priorityqueue/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/k3priorityqueue/badge/?version=stable)](https://k3priorityqueue.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3priorityqueue)](https://pypi.org/project/k3priorityqueue)

Priority queue with weighted producer support.

k3priorityqueue is a component of [pykit3](https://github.com/pykit3) project: a python3 toolkit set.

## Installation

```bash
pip install k3priorityqueue
```

## Quick Start

PriorityQueue pops items from producers according to their priority weights.
If producers A, B, C have priorities 1, 3, 7, items are popped in that ratio:

```python
import k3priorityqueue

producers = (
    # id, priority, iterable
    (1, 1, [1] * 10),
    (2, 2, [2] * 10),
    (3, 3, [3] * 10),
)

pq = k3priorityqueue.PriorityQueue()

for pid, prio, itr in producers:
    pq.add_producer(pid, prio, itr)

count = {}
for _ in range(12):
    val = pq.get()
    count[val] = count.get(val, 0) + 1

print('counts:', repr(count))
# Output shows ratio approximately 1:2:3
```

## API Reference

::: k3priorityqueue

## License

The MIT License (MIT) - Copyright (c) 2015 Zhang Yanpo (张炎泼)
