import itertools
import random
import unittest

import k3thread
import k3ut

import k3priorityqueue

dd = k3ut.dd


class TestConsumedQueue(unittest.TestCase):
    def test_init(self):
        cq = k3priorityqueue.Producer(1, 1, [])
        self.assertEqual(1, cq.priority)
        self.assertEqual(0, cq.consumed)
        self.assertEqual(k3priorityqueue.default_priority / cq.priority, cq.item_cost)

    def test_priority(self):
        self.assertRaises(ValueError, k3priorityqueue.Producer, 1, 0, [])
        self.assertRaises(ValueError, k3priorityqueue.Producer, 1, -1, [])
        self.assertRaises(ValueError, k3priorityqueue.Producer, 1, "", [])

        for priority in (float("nan"), float("inf"), float("-inf"), "nan", "inf"):
            self.assertRaises(ValueError, k3priorityqueue.Producer, 1, priority, [])

            pq = k3priorityqueue.PriorityQueue()
            self.assertRaises(ValueError, pq.add_producer, 1, priority, [])

    def test_consumed(self):
        a = k3priorityqueue.Producer(1, 1, [1, 2])
        b = k3priorityqueue.Producer(1, 10, range(20))

        self.assertEqual(1, a.get())
        self.assertEqual(2, a.get())
        self.assertRaises(k3priorityqueue.Empty, a.get)

        for i in range(20):
            b.get()

        self.assertEqual(a.consumed, b.consumed)

    def test_lt_init(self):
        a = k3priorityqueue.Producer(1, 1, [1, 2])
        b = k3priorityqueue.Producer(1, 1, [1, 2])

        self.assertFalse(a < b, "both empty")
        self.assertFalse(b < a, "both empty")

        a.get()
        b.get()

        self.assertFalse(a < b, "both empty")
        self.assertFalse(b < a, "both empty")

    def test_lt(self):
        a = k3priorityqueue.Producer(1, 1, range(100))
        b = k3priorityqueue.Producer(1, 10, range(100))

        # 0 0, but b has smaller item_cost
        self.assertFalse(a < b, "b has higher priority")
        self.assertTrue(b < a, "b has higher priority")

        # 0 0.1
        b.get()
        self.assertTrue(a < b, "b consumed 1")
        self.assertFalse(b < a, "b consumed 1")

        # 1 0.1
        a.get()
        self.assertFalse(a < b, "a consumed 1")
        self.assertTrue(b < a, "a consumed 1")

        # 1 0.2
        b.get()
        self.assertFalse(a < b, "a b consumed 1")
        self.assertTrue(b < a, "a b consumed 1")

        # 1 1
        for _ in range(8):
            b.get()
        self.assertFalse(a < b, "a b consumed 1")
        self.assertTrue(b < a, "a consume 1 b consumed 10")

        # 1 1.1
        b.get()
        self.assertTrue(a < b, "a b consumed 1")
        self.assertFalse(b < a, "a b consumed 1")


class TestPriorityQueue(unittest.TestCase):
    def test_get(self):
        producers = (
            # id, priority, iterable
            (1, 1, [1] * 10),
            (2, 2, [2] * 10),
            (3, 3, [3] * 10),
        )
        expected = [
            3,  # .3    0  0.0
            2,  # .3   .5  0.0
            1,  # .3   .5  1.0
            3,  # .6   .5  1.0
            2,  # .6  1.0  1.0
            3,  # 1.0  1.0  1.0
            3,  # 1.3  1.0  1.0
            2,  # 1.3  1.5  1.0
            1,  # 1.3  1.5  2.0
            3,  # 1.6  1.5  2.0
            2,  # 1.6  2.0  2.0
            3,  # 2.0  2.0  2.0
        ]
        pq = k3priorityqueue.PriorityQueue()
        for pid, prio, itr in producers:
            pq.add_producer(pid, prio, itr)

        dd(pq)
        rst = []
        for _ in expected:
            val = pq.get()
            rst.append(val)
        self.assertEqual(expected, rst)

    def test_add_queue(self):
        pq = k3priorityqueue.PriorityQueue()
        pq.add_producer(1, 1, [1, 1])
        self.assertEqual(1, pq.get())

        # re-add should update iterable
        pq.add_producer(1, 1, [2, 2])
        self.assertEqual(2, pq.get())

        # new queue with higher priority comes first
        pq.add_producer(2, 10, [10, 10])
        self.assertEqual(10, pq.get())

    def test_add_queue_update_priority(self):
        pq = k3priorityqueue.PriorityQueue()

        pq.add_producer(1, 1, [1, 1, 1])
        self.assertEqual(1, pq.get())

        pq.add_producer(2, 2, [2, 2, 2])
        self.assertEqual(2, pq.get())
        self.assertEqual(2, pq.get())

        # re-add should update priority, iterable and adjust heap
        pq.add_producer(1, 10, [10, 10, 10])
        dd(pq)
        dd(pq.consumable_heap)

        self.assertEqual(10, pq.get())

    def test_add_queue_update_failed(self):
        # A failed update of an existing producer changes nothing: the queue produces the same items.
        def build():
            pq = k3priorityqueue.PriorityQueue()
            for pid in (1, 2, 3):
                pq.add_producer(pid, 1, [pid] * 4)
            pq.get()
            pq.get()
            return pq

        def drain(pq):
            rst = []
            while True:
                try:
                    rst.append(pq.get())
                except k3priorityqueue.Empty:
                    return rst

        want = drain(build())

        for priority, iterable, err in (
            (100, 5, TypeError),
            (float("inf"), [3] * 4, ValueError),
            (0, [3] * 4, ValueError),
        ):
            pq = build()
            self.assertRaises(err, pq.add_producer, 3, priority, iterable)
            self.assertEqual(want, drain(pq), (priority, iterable))

    def test_remove_queue(self):
        pq = k3priorityqueue.PriorityQueue()
        pq.add_producer(1, 1, [1, 1])
        pq.remove_producer(1)

        self.assertRaises(k3priorityqueue.Empty, pq.get)
        pq.add_producer(1, 1, [1, 1])
        pq.add_producer(10, 10, [10, 10])
        self.assertEqual(10, pq.get())

        pq.remove_producer(10)
        self.assertEqual(1, pq.get())

    def test_remove_queue_inexistent(self):
        pq = k3priorityqueue.PriorityQueue()
        self.assertRaises(KeyError, pq.remove_producer, 1)
        pq.remove_producer(1, ignore_not_found=True)

    def test_bench(self):
        pq = k3priorityqueue.PriorityQueue()

        ntimes = 10240
        nq = 1024
        n_thread = 3
        ths = []

        def worker():
            for _ in range(ntimes):
                pq.get()

        for i in range(1, nq + 1):
            pq.add_producer(i, i, yield_forever())

        with k3ut.Timer() as t:
            for i in range(n_thread):
                th = k3thread.daemon(worker)
                ths.append(th)

            for th in ths:
                th.join()

            us_per_call = t.spent() / ntimes / n_thread * 1000 * 1000
            dd(us_per_call, "us/call")

        self.assertLess(us_per_call, 100)

    def test_concurrent(self):
        pq = k3priorityqueue.PriorityQueue()
        ntimes = 10240
        nq = 3
        n_thread = 3
        ths = []
        got_by_thread = [[] for _ in range(n_thread)]

        def worker(got):
            for _ in range(ntimes):
                got.append(pq.get())

        for i in range(1, nq + 1):
            # Producer i yields (i, 0), (i, 1), ..., so every item is distinct.
            pq.add_producer(i, i, zip(itertools.repeat(i), itertools.count()))

        for i in range(n_thread):
            th = k3thread.daemon(worker, args=(got_by_thread[i],))
            ths.append(th)

        for th in ths:
            th.join()

        got = []
        for items in got_by_thread:
            got.extend(items)
        got.sort()

        # Every item is got once, and no producer skips an item.
        want = []
        consumed = []
        for i in range(1, nq + 1):
            q = pq.producer_by_id[i]
            consumed.append(q.consumed)
            dd("get:", q.stat)
            want.extend((i, k) for k in range(q.stat["get"]))

        self.assertEqual(want, got)

        dd("consumed:", consumed)
        self.assertAlmostEqual(consumed[0], consumed[1])
        self.assertAlmostEqual(consumed[1], consumed[2])


def yield_forever():
    i = random.randint(1, 1000000)
    while True:
        i += 1
        yield (i * 2654435769) & 0xFFFFFFFF
