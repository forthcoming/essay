import gc
import os
import sys
import time
import weakref
from multiprocessing import Process

import objgraph

'''
引用计数+1情况
对象被创建,例如a=23
对象被引用,例如b=a
对象作为参数传入到一个函数中,例如func(a)
对象作为一个元素存储在容器中,例如list1=[a]

引用计数-1情况
对象的别名被显式销毁,例如del a
对象的别名被赋予新的对象,例如a=24
对象离开它的作用域.例如func函数执行完毕时,func函数中的局部变量(全局变量不会)
对象所在的容器被销毁,或从容器中删除对象

循环引用例子:
arr = [1]
arr.append(arr)
x=[]
y=[]
x.append(y)
y.append(x)

容器指可以引用其他对象的对象,如列表、字典、用户自定义类的对象、元组等,只有容器才可能出现循环引用,而像数字,字符串这类简单类型不会出现循环引用
当新增一个容器时,g0计数器加一,当容器个数达到阈值700时,进行一次g0回收
当g0回收一次时g1计数器加一,当g1计数器达到阈值10时,进行一次g1回收
当g1回收一次时g2计数器加一,当g2计数器达到阈值10时,进行一次g2回收
垃圾回收包含引用计数(不可解决循环引用),标记清除(可解决循环引用)和分代回收
对象被销毁(引用计数为0)时如果自定义了__del__,会执行__del__函数(一般用于资源释放如数据库连接),然后销毁对象
内存泄漏仅仅存在于某个进程中,无法进程间传递(即gc.get_objects仅仅统计所在进程的对象),会随着进程的结束而释放内存

gc流程
1. 创建容器(https://github.com/python/cpython/blob/main/Include/internal/pycore_object.h#L195)
static inline void _PyObject_GC_TRACK(PyObject *op) {
    PyGC_Head *gc = _Py_AS_GC(op);
    PyInterpreterState *interp = _PyInterpreterState_GET();
    PyGC_Head *generation0 = interp->gc.generation0;
    PyGC_Head *last = (PyGC_Head*)(generation0->_gc_prev);
    _PyGCHead_SET_NEXT(last, gc);
    _PyGCHead_SET_PREV(gc, last);
    _PyGCHead_SET_NEXT(gc, generation0);    // 每新建一个容器,都会把它插入到垃圾回收的0代环状双向链表g0中
    generation0->_gc_prev = (uintptr_t)gc;
}

2. 判断g0是否满足垃圾回收条件(https://github.com/python/cpython/blob/main/Modules/gcmodule.c#L2266)
void _PyObject_GC_Link(PyObject *op) {
    PyGC_Head *g = AS_GC(op);
    assert(((uintptr_t)g & (sizeof(uintptr_t)-1)) == 0);  // g must be correctly aligned
    PyThreadState *tstate = _PyThreadState_GET();
    GCState *gcstate = &tstate->interp->gc;
    g->_gc_next = 0;
    g->_gc_prev = 0;
    gcstate->generations[0].count++;   // 0代计数器自增1
    if (gcstate->generations[0].count > gcstate->generations[0].threshold &&  // 0代计数器大于0代阈值
        gcstate->enabled &&  
        gcstate->generations[0].threshold &&
        !gcstate->collecting &&
        !_PyErr_Occurred(tstate)) {
        _Py_ScheduleGC(tstate->interp);
    }
}

3. g0追踪对象数量超过阈值时,开启垃圾回收(https://github.com/python/cpython/blob/main/Modules/gcmodule.c#L1432)
static Py_ssize_t gc_collect_generations(PyThreadState *tstate) {
    GCState *gcstate = &tstate->interp->gc;
    Py_ssize_t n = 0;
    for (int i = NUM_GENERATIONS-1; i >= 0; i--) {  // i从2由老到年轻开始遍历
        if (gcstate->generations[i].count > gcstate->generations[i].threshold) {
            if (i == NUM_GENERATIONS - 1 && gcstate->long_lived_pending < gcstate->long_lived_total / 4)
                continue; // 如果是最老一代,且次代追踪对象数量long_lived_pending小与最老一代追踪对象数量long_lived_total的1/4,则不回收,提高效率
            n = gc_collect_with_callback(tstate, i);  // 找到计数超过阈值最老的一代,连同比它年轻的代追踪的对象将被收集
            break;  // 退出循环,应为更年轻的generation一定满足阈值
        }
    }
    return n;
}

4. 执行垃圾回收(https://github.com/python/cpython/blob/main/Modules/gcmodule.c#L1193)
static Py_ssize_t gc_collect_main(PyThreadState *tstate, int generation,
    Py_ssize_t *n_collected, Py_ssize_t *n_uncollectable, int nofail) {
    int i;
    Py_ssize_t m = 0;  // objects collected
    Py_ssize_t n = 0; // unreachable objects that couldn't be collected
    PyGC_Head *young; // the generation we are examining
    PyGC_Head *old;   // next older generation
    PyGC_Head unreachable; // non-problematic unreachable trash
    PyGC_Head finalizers;  // objects with, & reachable from, __del__
    PyGC_Head *gc;
    _PyTime_t t1 = 0;  
    GCState *gcstate = &tstate->interp->gc;

    if (gcstate->debug & DEBUG_STATS) { // 如果设置了gc.set_debug(gc.DEBUG_STATS)
        PySys_WriteStderr("gc: collecting generation %d...\n", generation);
        show_stats_each_generations(gcstate);
        t1 = _PyTime_GetPerfCounter();
    }

    if (generation+1 < NUM_GENERATIONS)  // 如果父代不是最老代
        gcstate->generations[generation+1].count += 1; //父代计数器自增1(应为其子代将要执行垃圾回收)
    for (i = 0; i <= generation; i++)
        gcstate->generations[i].count = 0;  // 重置子代及其自身的计数器

    for (i = 0; i < generation; i++) {
        gc_list_merge(GEN_HEAD(gcstate, i), GEN_HEAD(gcstate, generation)); // 将所有子代的追踪对象合并到当前代
    }

    young = GEN_HEAD(gcstate, generation);  // 当前代设为yong,即young = [0, 当前代]
    if (generation < NUM_GENERATIONS-1)  // young不是最老代
        old = GEN_HEAD(gcstate, generation+1);  // 父代设为old
    else
        old = young;  // young设为old

    deduce_unreachable(young, &unreachable); // 没看懂,貌似把不可达对象清除了
    untrack_tuples(young);   // 找到可以停止追踪的tuples,减少垃圾回收工作量
    
    if (young != old) {
        if (generation == NUM_GENERATIONS - 2) {  // 如果young是最老代的次代
            gcstate->long_lived_pending += gc_list_size(young); // 更新long_lived_pending,自增young追踪的可达对象数量
        }
        gc_list_merge(young, old);  // 将young追踪的可达对象合并到old
    }
    else {
        untrack_dicts(young);  // We only un-track dicts in full collections, 以避免二次dict build-up. See issue #14775
        gcstate->long_lived_pending = 0;  // 重置long_lived_pending
        gcstate->long_lived_total = gc_list_size(young); // 更新long_lived_total,赋值为young/old追踪的可达对象数量 
    }

    move_legacy_finalizers(&unreachable, &finalizers);
    move_legacy_finalizer_reachable(&finalizers);

    if (gcstate->debug & DEBUG_COLLECTABLE) {  // 如果设置了gc.set_debug(gc.DEBUG_COLLECTABLE)
        for (gc = GC_NEXT(&unreachable); gc != &unreachable; gc = GC_NEXT(gc)) {
            debug_cycle("collectable", FROM_GC(gc));
        }
    }

    m += handle_weakrefs(&unreachable, old);  // 清除弱引用并根据需要调用回调
    finalize_garbage(tstate, &unreachable);  // 调用tp_finalize即__del__

    PyGC_Head final_unreachable;
    handle_resurrected_objects(&unreachable, &final_unreachable, old);  // 没看懂
    m += gc_list_size(&final_unreachable);
    delete_garbage(tstate, gcstate, &final_unreachable, old);

    /* Collect statistics on uncollectable objects found and print
     * debugging information. */
    for (gc = GC_NEXT(&finalizers); gc != &finalizers; gc = GC_NEXT(gc)) {
        n++;  // 统计发现的不可收集对象
        if (gcstate->debug & DEBUG_UNCOLLECTABLE)
            debug_cycle("uncollectable", FROM_GC(gc));
    }
    if (gcstate->debug & DEBUG_STATS) {
        double d = _PyTime_AsSecondsDouble(_PyTime_GetPerfCounter() - t1);
        PySys_WriteStderr("gc: done, %zd unreachable, %zd uncollectable, %.4fs elapsed\n",n+m, n, d);
    }

    if (generation == NUM_GENERATIONS-1) {
        clear_freelists(tstate->interp);  // 仅在最高代回收期间清除freelist
    }
    if (n_collected) {
        *n_collected = m;
    }
    if (n_uncollectable) {
        *n_uncollectable = n;
    }

    struct gc_generation_stats *stats = &gcstate->generation_stats[generation];
    stats->collections++; // 对应gc.get_stats()
    stats->collected += m;
    stats->uncollectable += n;

    return n + m;
}
'''


class Gc:
    def __init__(self):
        self.data = list(range(10000))
        self.next = None


def circular_reference_to_leak():
    a = Gc()
    b = Gc()
    a.next = b  # a.next = weakref.ref(b),解决循环引用问题
    b.next = a  # b.next = weakref.ref(a),解决循环引用问题


def default_parameter_to_leak(idx, _cache={}):
    _cache[idx] = {Gc()}  # a very explicit and easy-to-find "leak" but oh well
    _ = Gc()  # this one doesn't leak
    print("in default_parameter_to_leak", objgraph.count('Gc'))


def generator_to_leak():
    cnt = 0
    _ = [Gc() for _ in range(10)]
    while True:
        yield cnt
        cnt += 1


def test_ref():
    """
    弱引用不增加引用计数,当对像的引用只剩弱引用时, garbage collection可以销毁对象并将其内存重用于其他内容
    弱引用的主要用途是实现保存大对象的高速缓存或映射, 并希望大对象仅仅因为它出现在高速缓存或映射中而保持存活;还能解决循环引用
    WeakKeyDictionary 弱引用键的映射类, 当不再有对键的强引用时字典中的条目将被丢弃
    WeakValueDictionary 弱引用值的映射类, 当不再存在对该值的强引用时, 字典中的条目将被丢弃
    WeakSet 保持对其元素弱引用的集合类, 当不再有对某个元素的强引用时元素将被丢弃
    """
    a = Gc()
    c = weakref.ref(a)
    _a = c()  # 相当与给a增加了一个引用计数,一般不建议这么使用
    print(a, _a, c)
    print(sys.getrefcount(a))  # 3, 返回的计数通常比预期高1,因为它包含引用作为getrefcount参数
    print(sys.getrefcount(_a))  # 3
    print(sys.getrefcount(c))  # 2
    print(weakref.getweakrefs(a), weakref.getweakrefcount(a))  # [<weakref at 0x10dace660; to 'Gc' at 0x10d8862d0>] 1
    del a, _a
    print(c())  # None,建议使用前先判断是否为None


def test_cache():
    """
    为避免重复创建和销毁一些常见对象,会维护一个缓存池,里面包含如-5,-4,...257,字符等常见对象,用户定义的字符串,数字等不可变类型,也会被加入到缓存池
    当再有其他变量需要用到缓存池内对象时,直接指向即可,即地址不变,当变量值发生改变时才会重新创建对象
    用户定义的数组,字典等可变类型,当引用计数为0被销毁时,如果free_list未满会被加入其中,当用户再定义一个类型相同的对象时直接从free_list选地址赋值即可,即地址不变
    """
    immutable_val = "1314520."
    id_immutable_val = id(immutable_val)
    del immutable_val
    immutable_val1 = "1314520."
    immutable_val2 = "1314520."
    print(id_immutable_val == id(immutable_val1) == id(immutable_val2))  # True

    def test_mutable_cache():
        set1 = set()
        list1 = []
        return id(set1), id(list1)

    set2 = {1}
    list2 = [1]
    id_set2, id_list2 = id(set2), id(list2)
    id_set1, id_list1 = test_mutable_cache()  # 放在set2,list2前面调用会不同
    del set2, list2
    set3, list3 = {2}, [2]
    set4, list4 = {3}, [3]
    print(id_set2 == id(set3), id_list2 == id(list3), id_set1 == id(set4), id_list1 == id(list4))  # True True True True
    print(len({id_set2, id_list2, id_set1, id_list1}) == 4)  # True


def test_circular_reference():
    for idx in range(40):
        time.sleep(1)
        circular_reference_to_leak()
        if idx == 20:
            print(gc.collect())
        print(os.getpid(), objgraph.count('Gc'), gc.get_count())


def test_multiprocess_circular_reference():
    processes = [Process(target=test_circular_reference) for _ in range(3)]
    for process in processes:
        process.start()
    for idx in range(100):
        print("in main", objgraph.count('Gc'))
        time.sleep(.5)


def test_default_parameter():
    objgraph.show_growth(limit=2)  # 调用函数之前We take a snapshot of all the objects counts that are alive
    for idx in range(10):
        default_parameter_to_leak(idx)
        print("in test_default_parameter", objgraph.count('Gc'))
        objgraph.show_growth()


def test_generator():
    it = generator_to_leak()
    next(it)
    print(objgraph.count("Gc"))


class ObjGraph:
    # https://github.com/mgedmin/objgraph/blob/master/objgraph.py
    @staticmethod
    def type_stats():
        """
        Count the number of instances for each type tracked by the GC.
        Note that classes with the same name but defined in different modules will be lumped together if shortnames is True.
        The Python garbage collector does not track simple objects like int or str.
        See https://docs.python.org/3/library/gc.html#gc.is_tracked
        """
        objects = gc.get_objects()
        try:
            stats = {}
            for obj in objects:
                name = type(obj).__name__
                stats[name] = stats.get(name, 0) + 1
            return stats
        finally:
            del objects  # clear cyclic references to frame

    @staticmethod
    def show_most_common_types(limit=10):
        stats = sorted(ObjGraph.type_stats().items(), key=lambda item: item[1], reverse=True)
        if limit:
            stats = stats[:limit]
        width = max(len(name) for name, count in stats)
        for name, count in stats:
            sys.stdout.write('%-*s %i\n' % (width, name, count))

    @staticmethod
    def show_growth(limit=10, peak_stats={}):
        """
        Show the increase in peak object counts since last call.
        peak_stats, a dictionary from type names to previously seen peak object counts.
        Usually you don't need to pay attention to this argument.
        """
        gc.collect()  # 避免循环引用干扰
        stats = ObjGraph.type_stats()
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


def test_garbage_collection():
    a = [{}, (), 1, ""]
    b = a,
    c = {1: a}
    print(gc.get_referents(a))  # 返回所有被a引用的对象
    print(gc.get_referrers(a))  # 返回所有引用了a的对象

    d = ""
    e = {1: 2}
    assert not gc.is_tracked(d)  # 非容器对象不会被垃圾回收追踪
    assert not gc.is_tracked(e)  # 简单容器也不被垃圾回收追踪
    e[2] = []
    assert gc.is_tracked(e)  # 复杂容器会被垃圾回收追踪

    assert gc.get_threshold() == (700, 10, 10)  # 垃圾回收每代阈值
    print(gc.get_count())  # (407,9,2), 表示当前每一代count值,与get_threshold返回值相对应
    # print(gc.get_objects())  # 返回被垃圾回收器追踪的所有对象的列表,不包括返回的列表
    print(gc.collect())  # 手动执行垃圾回收, 返回不可达(unreachable objects)对象的数目


if __name__ == '__main__':
    test_garbage_collection()
    # test_ref()
    # test_cache()
    # test_circular_reference()
    # test_multiprocess_circular_reference()
    # test_default_parameter()
    # test_generator()
