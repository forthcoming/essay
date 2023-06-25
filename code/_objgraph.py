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


def get_leaking_objects():
    """
    Return objects that do not have any referents.
    These could indicate reference-counting bugs in C code.  Or they could be legitimate.
    Note that the GC does not track simple objects like int or str.
    """
    gc.collect()
    objects = gc.get_objects()
    try:
        ids = {id(i) for i in objects}
        for i in objects:
            # Return a list of objects directly referred to by any of the arguments
            ids -= {id(j) for j in gc.get_referents(i)}
        return [i for i in objects if id(i) in ids]  # this then is our set of objects without referrers
    finally:
        del objects, i  # clear cyclic references to frame


def count(typename):
    """
    Count objects tracked by the garbage collector with a given class name.
    The class name can optionally be fully qualified.
    Example:
        >>> count('dict')
        42
        >>> count('mymodule.MyClass')
        2
    note:
        The Python garbage collector does not track simple objects like int or str. 
        See https://docs.python.org/3/library/gc.html#gc.is_tracked for more information.
    Instead of looking through all objects tracked by the GC, you may specify your own collection, e.g.
    >>> count('MyClass', get_leaking_objects())
        3
    """
    objects = gc.get_objects()
    try:
        if '.' in typename:
            return sum(1 for o in objects if _long_typename(o) == typename)
        else:
            return sum(1 for o in objects if _short_typename(o) == typename)
    finally:
        del objects  # clear cyclic references to frame


def typestats(shortnames=True, filter=None):
    """
    Count the number of instances for each type tracked by the GC.
    Note that the GC does not track simple objects like int or str.
    Note that classes with the same name but defined in different modules will be lumped together if ``shortnames`` is True.
    If ``filter`` is specified, it should be a function taking one argument and returning a boolean. Objects for which ``filter(obj)`` returns ``False`` will be ignored.
    Example:
        >>> typestats()
        {'list': 12041, 'tuple': 10245, ...}
        >>> typestats(get_leaking_objects())
        {'MemoryError': 1, 'tuple': 2795, 'RuntimeError': 1, 'list': 47, ...}
    """
    objects = gc.get_objects()  # Returns a list of all objects tracked by the collector, excluding the list returned.
    try:
        if shortnames:
            typename = _short_typename
        else:
            typename = _long_typename
        stats = {}
        for o in objects:
            if filter and not filter(o):
                continue
            n = typename(o)
            stats[n] = stats.get(n, 0) + 1
        return stats
    finally:
        del objects  # clear cyclic references to frame


def show_most_common_types(limit=10, shortnames=True, filter=None):
    """
    Print the table of types of most common instances.
    If ``filter`` is specified, it should be a function taking one argument and returning a boolean. Objects for which ``filter(obj)`` returns ``False`` will be ignored.
    Example:
        >>> show_most_common_types(limit=5)
        tuple                      8959
        function                   2442
        wrapper_descriptor         1048
        dict                       953
        builtin_function_or_method 800
    """
    stats = sorted(typestats(shortnames=shortnames, filter=filter).items(), key=operator.itemgetter(1), reverse=True)
    if limit:
        stats = stats[:limit]
    width = max(len(name) for name, count in stats)
    for name, count in stats:
        sys.stdout.write('%-*s %i\n' % (width, name, count))


def show_growth(limit=10, shortnames=True, filter=None, peak_stats={}):
    """
    Show the increase in peak object counts since last call.
    peak_stats, a dictionary from type names to previously seen peak object counts.
    Usually you don't need to pay attention to this argument.
    """
    gc.collect()  # 手动执行垃圾回收,避免循环引用干扰
    stats = typestats(shortnames=shortnames, filter=filter)
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
