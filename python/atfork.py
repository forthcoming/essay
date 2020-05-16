"""
Refer: https://github.com/google/python-atfork/blob/master/atfork/__init__.py
功能与os.register_at_fork类似,redis连接池也有类似函数_checkpid,通过pid判断对象切换进程后调用对应函数做清理工作
To use this module, first import it early on your programs initialization:
import atfork
atfork.monkeypatch_os_fork_functions()
Next, register your atfork actions by calling atfork.atfork:
"""

import os, sys, threading, traceback

__all__ = ('monkeypatch_os_fork_functions', 'atfork')

_fork_lock = threading.Lock()   # This lock protects all of the lists below.
_prepare_call_list = []
_parent_call_list = []
_child_call_list = []
_prepare_call_exceptions = []

def monkeypatch_os_fork_functions():
    if hasattr(os, 'fork'):
        global _orig_os_fork
        _orig_os_fork = os.fork
        os.fork = os_fork_wrapper

def atfork(prepare=None, parent=None, child=None):
    """
    Any time a fork() is called from Python, all 'prepare' callables will be called in the order they were registered using this function.
    After the fork (successful or not), all 'parent' callables will be called in the parent process.
    If the fork succeeded, all 'child' callables will be called in the child process.
    No exceptions may be raised from any of the registered callables.  If so they will be printed to sys.stderr after the fork call once it is safe to do so.
    """
    assert not prepare or callable(prepare)
    assert not parent or callable(parent)
    assert not child or callable(child)
    with _fork_lock:
        if prepare:
            _prepare_call_list.append(prepare)
        if parent:
            _parent_call_list.append(parent)
        if child:
            _child_call_list.append(child)

def _call_atfork_list(call_list):
    """
    Given a list of callables in call_list, call them all in order and save and return a list of sys.exc_info() tuples for each exception raised.
    """
    exception_list = []
    for func in call_list:
        try:
            func()
        except:
            exception_list.append(sys.exc_info())
    return exception_list

def _print_exception_list(exceptions, message, output_file=None):
    """
    Given a list of sys.exc_info tuples, print them all using the traceback module preceeded by a message and separated by a blank line.
    """
    output_file = output_file or sys.stderr
    message = f'Exception {message}:\n'
    for exc_type, exc_value, exc_traceback in exceptions:
        output_file.write(message)
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=output_file)
        output_file.write('\n')

def prepare_to_fork_acquire():  # Acquire our lock and call all prepare callables.
    _fork_lock.acquire()
    _prepare_call_exceptions.extend(_call_atfork_list(_prepare_call_list))

def parent_after_fork_release():
    """
    Call all parent after fork callables, release the lock and print all prepare and parent callback exceptions.
    """
    prepare_exceptions = list(_prepare_call_exceptions)  # 拷贝,非引用赋值
    del _prepare_call_exceptions[:]
    exceptions = _call_atfork_list(_parent_call_list)
    _fork_lock.release()
    _print_exception_list(prepare_exceptions, 'before fork')
    _print_exception_list(exceptions, 'after fork from parent')

def child_after_fork_release():
    """
    Call all child after fork callables, release lock and print all all child callback exceptions.
    """
    del _prepare_call_exceptions[:]  # 仅仅清空异常列表,父进程中注册的call_list在子进程中依然存在
    exceptions = _call_atfork_list(_child_call_list)
    _fork_lock.release()  # 子进程中也要释放锁
    _print_exception_list(exceptions, 'after fork from child')

def os_fork_wrapper():  # Wraps os.fork() to run atfork handlers.
    pid = None
    prepare_to_fork_acquire()
    try:
        pid = _orig_os_fork()
    finally:
        if pid == 0:
            child_after_fork_release()
        else:  # We call this regardless of fork success in order for the program to be in a sane state afterwards.
            parent_after_fork_release()
    return pid
