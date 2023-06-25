import gc
import operator
import sys


# https://github.com/mgedmin/objgraph/blob/master/objgraph.py
def _short_typename(obj):
    return type(obj).__name__


def _long_typename(obj):
    obj_type = type(obj)
    name = obj_type.__name__
    module = getattr(obj_type, '__module__', None)
    if module:
        return f'{module}.{name}'
    else:
        return name


def type_stats(is_short_name=True):
    """
    Count the number of instances for each type tracked by the GC.
    Note that classes with the same name but defined in different modules will be lumped together if shortnames is True.
    The Python garbage collector does not track simple objects like int or str.
    See https://docs.python.org/3/library/gc.html#gc.is_tracked
    """
    objects = gc.get_objects()  # Returns a list of all objects tracked by the collector, excluding the list returned.
    try:
        typename = _short_typename if is_short_name else _long_typename
        stats = {}
        for obj in objects:
            name = typename(obj)
            stats[name] = stats.get(name, 0) + 1
        return stats
    finally:
        del objects  # clear cyclic references to frame


def show_growth(limit=10, shortnames=True, peak_stats={}):
    """
    Show the increase in peak object counts since last call.
    peak_stats, a dictionary from type names to previously seen peak object counts.
    Usually you don't need to pay attention to this argument.
    """
    gc.collect()  # 手动执行垃圾回收,避免循环引用干扰
    stats = type_stats(is_short_name=shortnames)
    deltas = {}
    for name, count in stats:
        old_count = peak_stats.get(name, 0)
        if count > old_count:
            deltas[name] = count - old_count
            peak_stats[name] = count
    deltas = sorted(deltas.items(), key=operator.itemgetter(1), reverse=True)
    if limit:
        deltas = deltas[:limit]
    result = [(name, stats[name], delta) for name, delta in deltas]
    width = max(len(name) for name, _, _ in result)
    for name, count, delta in result:
        sys.stdout.write('%-*s%9d %+9d\n' % (width, name, count, delta))


def show_most_common_types(limit=10, shortnames=True):
    stats = sorted(type_stats(is_short_name=shortnames).items(), key=operator.itemgetter(1), reverse=True)
    if limit:
        stats = stats[:limit]
    width = max(len(name) for name, count in stats)
    for name, count in stats:
        sys.stdout.write('%-*s %i\n' % (width, name, count))
