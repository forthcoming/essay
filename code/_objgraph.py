import gc
import sys


# https://github.com/mgedmin/objgraph/blob/master/objgraph.py
def type_stats():
    """
    Count the number of instances for each type tracked by the GC.
    Note that classes with the same name but defined in different modules will be lumped together if shortnames is True.
    The Python garbage collector does not track simple objects like int or str.
    See https://docs.python.org/3/library/gc.html#gc.is_tracked
    """
    objects = gc.get_objects()  # Returns a list of all objects tracked by the collector, excluding the list returned.
    try:
        stats = {}
        for obj in objects:
            name = type(obj).__name__
            stats[name] = stats.get(name, 0) + 1
        return stats
    finally:
        del objects  # clear cyclic references to frame


def show_most_common_types(limit=10):
    stats = sorted(type_stats().items(), key=lambda item: item[1], reverse=True)
    if limit:
        stats = stats[:limit]
    width = max(len(name) for name, count in stats)
    for name, count in stats:
        sys.stdout.write('%-*s %i\n' % (width, name, count))


def show_growth(limit=10, peak_stats={}):
    """
    Show the increase in peak object counts since last call.
    peak_stats, a dictionary from type names to previously seen peak object counts.
    Usually you don't need to pay attention to this argument.
    """
    gc.collect()  # 手动执行垃圾回收,避免循环引用干扰
    stats = type_stats()
    deltas = {}
    for name, count in stats.items():
        old_count = peak_stats.get(name, 0)
        if count > old_count:
            deltas[name] = count - old_count
            peak_stats[name] = count
    deltas = sorted(deltas.items(), key=lambda item: item[1], reverse=True)
    if limit:
        deltas = deltas[:limit]
    result = [(name, stats[name], delta) for name, delta in deltas]
    if result:
        width = max(len(name) for name, _, _ in result)
        for name, count, delta in result:
            sys.stdout.write('%-*s%9d %+9d\n' % (width, name, count, delta))

