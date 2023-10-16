#import math
import sys
from time import time

from multiprocessing import Process, cpu_count, Queue, Manager, Pool


def factorize(*number):
    res = []
    for i, num in enumerate(number):
        res.append([])
        for val in range(1, num+1):
            if not num%val:
                res[i].append(val)
    return res


def calc_factors_queue(qu: Queue, return_dict: dict):
    """
    Worker function for factorize_multiprocess_queue().
    """
    num = qu.get()
    res = []
    for val in range(1, num+1):
        if not num%val:
            res.append(val)
    return_dict[num] = res
    sys.exit(0)


def factorize_multiprocess_queue(*number):
    """
    Multiprocessing implementation with Queue.
    """
    qu = Queue()
    manager = Manager()
    res_dict = manager.dict()
    prs = []
    for num in number:
        qu.put(num)
        pr = Process(target=calc_factors_queue, args=(qu, res_dict))
        prs.append(pr)
        pr.start()
    [pr.join() for pr in prs]
    return res_dict.values()


def calc_factors_pool(num):
    """
    Worker function for factorize_multiprocess_pool() | _pool_map().
    """
    res = []
    for val in range(1, num+1):
        if not num%val:
            res.append(val)
    return res


def callback(result):
    """
    Callback function for factorize_multiprocess_pool().
    """
    #print(f"Result in callback: {result}")
    global RESULT
    RESULT = result


def factorize_multiprocess_pool(*number):
    """
    Multiprocessing implementation with Pool and map_async.
    """
    global RESULT
    RESULT = {}
    with Pool(cpu_count()) as p:
        p.map_async(
            calc_factors_pool,
            list(number),
            callback=callback
        )
        p.close()  # перестати виділяти процеси в пулл
        p.join()  # дочекатися закінчення всіх процесів
    return RESULT


def factorize_multiprocess_pool_map(*number):
    """
    Multiprocessing implementation with Pool and simple map.
    """
    with Pool(cpu_count()) as pool:
        result = pool.map(calc_factors_pool, number)
    return result


def test(fnc=factorize):
    print("Function:", fnc.__name__)
    start_time = time()
    a, b, c, d = fnc(128, 255, 99999, 10651060)
    end_time = time()

    assert a == [1, 2, 4, 8, 16, 32, 64, 128], a
    assert b == [1, 3, 5, 15, 17, 51, 85, 255]
    assert c == [1, 3, 9, 41, 123, 271, 369, 813, 2439, 11111, 33333, 99999]
    assert d == [1, 2, 4, 5, 7, 10, 14, 20, 28, 35, 70, 140, 76079, 152158, 304316, 380395, 532553, 760790, 1065106,
                 1521580, 2130212, 2662765, 5325530, 10651060]
    print("Test passed")
    print("Time spent:", end_time - start_time)


if __name__ == "__main__":
    #print("Available CPUs:", cpu_count())
    test(factorize)
    test(factorize_multiprocess_queue)
    test(factorize_multiprocess_pool)
    test(factorize_multiprocess_pool_map)

