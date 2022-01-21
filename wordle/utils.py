from math import *

inf = float("inf")

def choose_max(iterable, max_fn):
    currMax = None
    currScore = -inf
    for thing in iterable:
        score = max_fn(thing)
        if currScore < score:
            currMax = thing
            currScore = score
    return currMax

def stddev(collection, mean=None):
    if mean is None:
        mean = sum(collection) / len(collection)
    sumsqr = sum( (pow(e - mean, 2) for e in collection) )
    return sqrt( sumsqr / len(collection))


__all__ = ["inf", "choose_max", "stddev"]
