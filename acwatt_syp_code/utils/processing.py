#!/usr/bin/env python

"""Functions to use multithreading and multiprocessing to speed up data downloading."""

# Built-in Imports
# Third-party Imports
# Local Imports

from multiprocessing.pool import ThreadPool
from random import randint
import threading
import time

MAX_THREADS = 20
print_lock = threading.Lock()  # Prevent overlapped printing from threads.


def query_data(trade):
    trade_id = trade[0][1][:6]
    time.sleep(randint(1, 3))  # Simulate variable working time for testing.
    with print_lock:
        print(trade_id)


def process_trades(trade_list):
    pool = ThreadPool(processes=MAX_THREADS)
    results = []
    while(trade_list):
        trade = trade_list.pop()
        results.append(pool.apply_async(query_data, (trade,)))

    pool.close()  # Done adding tasks.
    pool.join()  # Wait for all tasks to complete.


def test():
    trade_list = [[['abc', ('%06d' % id) + 'defghi']] for id in range(1, 101)]
    process_trades(trade_list)


if __name__ == "__main__":
    test()
