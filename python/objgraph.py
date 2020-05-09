import collections, gc, re, operator, os, sys

# https://github.com/mgedmin/objgraph/blob/master/objgraph.py

def _short_typename(obj):
    return type(obj).__name__

def _long_typename(obj):
    objtype = type(obj)
    name = objtype.__name__
    module = getattr(objtype, '__module__', None)
    if module:
        return '{}.{}'.format(module, name)
    else:
        return name

def get_leaking_objects():
    """
    Return objects that do not have any referents.
    These could indicate reference-counting bugs in C code.  Or they could be legitimate.
    Note that the GC does not track simple objects like int or str.
    """
    gc.collect()  # 手动执行垃圾回收
    objects = gc.get_objects()   # Returns a list of all objects tracked by the collector, excluding the list returned.
    try:
        ids = {id(i) for i in objects}
        for i in objects:
            ids -= {id(j) for j in gc.get_referents(i)}  # Return a list of objects directly referred to by any of the arguments
        return [i for i in objects if id(i) in ids]      # this then is our set of objects without referrers
    finally:
        del objects, i  # clear cyclic references to frame

def count(typename, objects=None):
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
    if objects is None:
        objects = gc.get_objects()
    try:
        if '.' in typename:
            return sum(1 for o in objects if _long_typename(o) == typename)
        else:
            return sum(1 for o in objects if _short_typename(o) == typename)
    finally:
        del objects  # clear cyclic references to frame

def typestats(objects=None, shortnames=True, filter=None):
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
    if objects is None:
        objects = gc.get_objects()
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

def show_most_common_types(limit=10, objects=None, shortnames=True, filter=None):
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
    stats = sorted(typestats(objects, shortnames=shortnames, filter=filter).items(), key=operator.itemgetter(1), reverse=True)
    if limit:
        stats = stats[:limit]
    width = max(len(name) for name, count in stats)
    for name, count in stats:
        sys.stdout.write('%-*s %i\n' % (width, name, count))

def show_growth(limit=10, shortnames=True,filter=None,peak_stats={}):
    """
    Show the increase in peak object counts since last call.
    peak_stats, a dictionary from type names to previously seen peak object counts.  Usually you don't need to pay attention to this argument.
    """
    gc.collect()
    stats = typestats(shortnames=shortnames, filter=filter)
    deltas = {}
    for name, count in stats:
        old_count = peak_stats.get(name, 0)
        if count > old_count:
            deltas[name] = count - old_count
            peak_stats[name] = count
    deltas = sorted(deltas.items(), key=operator.itemgetter(1),reverse=True)
    if limit:
        deltas = deltas[:limit]
    result = [(name, stats[name], delta) for name, delta in deltas]
    width = max(len(name) for name, _, _ in result)
    for name, count, delta in result:
        sys.stdout.write('%-*s%9d %+9d\n' % (width, name, count, delta))

def get_new_ids(skip_update=False, limit=10, sortby='deltas', shortnames=None, file=None, _state={}):
    """Find and display new objects allocated since last call.

    Shows the increase in object counts since last call to this
    function and returns the memory address ids for new objects.

    Returns a dictionary mapping object type names to sets of object IDs
    that have been created since the last time this function was called.

    ``skip_update`` (bool): If True, returns the same dictionary that
    was returned during the previous call without updating the internal
    state or examining the objects currently in memory.

    ``limit`` (int): The maximum number of rows that you want to print
    data for.  Use 0 to suppress the printing.  Use None to print everything.

    ``sortby`` (str): This is the column that you want to sort by in
    descending order.  Possible values are: 'old', 'current', 'new',
    'deltas'

    ``shortnames`` (bool): If True, classes with the same name but
    defined in different modules will be lumped together.  If False,
    all type names will be qualified with the module name.  If None (default),
    ``get_new_ids`` will remember the value from previous calls, so it's
    enough to prime this once.  By default the primed value is True.

    ``_state`` (dict): Stores old, current, and new_ids in memory.
    It is used by the function to store the internal state between calls.
    Never pass in this argument unless you know what you're doing.

    The caveats documented in :func:`growth` apply.

    When one gets new_ids from :func:`get_new_ids`, one can use
    :func:`at_addrs` to get a list of those objects. Then one can iterate over
    the new objects, print out what they are, and call :func:`show_backrefs` or
    :func:`show_chain` to see where they are referenced.

    Example:

        >>> _ = get_new_ids() # store current objects in _state
        >>> _ = get_new_ids() # current_ids become old_ids in _state
        >>> a = [0, 1, 2] # list we don't know about
        >>> b = [3, 4, 5] # list we don't know about
        >>> new_ids = get_new_ids(limit=3) # we see new lists
        ======================================================================
        Type                    Old_ids  Current_ids      New_ids Count_Deltas
        ======================================================================
        list                        324          326           +3           +2
        dict                       1125         1125           +0           +0
        wrapper_descriptor         1001         1001           +0           +0
        ======================================================================
        >>> new_lists = at_addrs(new_ids['list'])
        >>> a in new_lists
        True
        >>> b in new_lists
        True

    .. versionadded:: 3.4
    """
    if not _state:
        _state['old'] = collections.defaultdict(set)
        _state['current'] = collections.defaultdict(set)
        _state['new'] = collections.defaultdict(set)
        _state['shortnames'] = True
    new_ids = _state['new']
    if skip_update:
        return new_ids
    old_ids = _state['old']
    current_ids = _state['current']
    if shortnames is None:
        shortnames = _state['shortnames']
    else:
        _state['shortnames'] = shortnames
    gc.collect()
    objects = gc.get_objects()
    for class_name in old_ids:
        old_ids[class_name].clear()
    for class_name, ids_set in current_ids.items():
        old_ids[class_name].update(ids_set)
    for class_name in current_ids:
        current_ids[class_name].clear()
    for o in objects:
        if shortnames:
            class_name = _short_typename(o)
        else:
            class_name = _long_typename(o)
        id_number = id(o)
        current_ids[class_name].add(id_number)
    for class_name in new_ids:
        new_ids[class_name].clear()
    rows = []
    keys_to_remove = []
    for class_name in current_ids:
        num_old = len(old_ids[class_name])
        num_current = len(current_ids[class_name])
        if num_old == 0 and num_current == 0:
            # remove the key from our dicts if we don't have any old or
            # current class_name objects
            keys_to_remove.append(class_name)
            continue
        new_ids_set = current_ids[class_name] - old_ids[class_name]
        new_ids[class_name].update(new_ids_set)
        num_new = len(new_ids_set)
        num_delta = num_current - num_old
        row = (class_name, num_old, num_current, num_new, num_delta)
        rows.append(row)
    for key in keys_to_remove:
        del old_ids[key]
        del current_ids[key]
        del new_ids[key]
    index_by_sortby = {'old': 1, 'current': 2, 'new': 3, 'deltas': 4}
    rows.sort(key=operator.itemgetter(index_by_sortby[sortby], 0),
              reverse=True)
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        return new_ids
    if file is None:
        file = sys.stdout
    width = max(len(row[0]) for row in rows)
    print('='*(width+13*4), file=file)
    print('%-*s%13s%13s%13s%13s' % (width, 'Type', 'Old_ids', 'Current_ids', 'New_ids', 'Count_Deltas'),file=file)
    print('='*(width+13*4), file=file)
    for row_class, old, current, new, delta in rows:
        print('%-*s%13d%13d%+13d%+13d' % (width, row_class, old, current, new, delta), file=file)
    print('='*(width+13*4), file=file)
    return new_ids


