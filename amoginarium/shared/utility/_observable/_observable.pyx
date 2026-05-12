# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: initializedcheck=False

import weakref
import types
from libc.stdlib cimport malloc, realloc, free
from cpython.ref cimport PyObject

# EXPLICIT C-API
cdef extern from "Python.h":
    void Py_INCREF(PyObject *o)
    void Py_DECREF(PyObject *o)
    PyObject * PyWeakref_GetObject(PyObject *ref)

cdef type MethodType = types.MethodType

cdef class CyObservable:
    def __cinit__(self):
        self._callbacks = NULL
        self._capacity = 0
        self._count = 0
        self._seen_refs = set()

    def __init__(self, object value):
        self._value = value

    def __dealloc__(self):
        cdef size_t i
        if self._callbacks != NULL:
            for i in range(self._count):
                Py_DECREF(self._callbacks[i].target_ref)
                if self._callbacks[i].func != NULL:
                    Py_DECREF(self._callbacks[i].func)
            free(self._callbacks)

    cpdef object get_value(self):
        return self._value

    cpdef void set_value(self, object new_value):
        cdef object old_value = self._value
        cdef size_t i = 0
        cdef CallbackEntry * entry
        cdef PyObject * obj
        cdef tuple sig

        self._value = new_value

        if old_value != new_value:
            while i < self._count:
                entry = &self._callbacks[i]
                obj = PyWeakref_GetObject(entry.target_ref)

                if obj != NULL and (<object> obj) is not None:
                    # UPDATED: Pass both new_value and old_value
                    if entry.func != NULL:
                        (<object> entry.func)(<object> obj, new_value, old_value)
                    else:
                        (<object> obj)(new_value, old_value)
                    i += 1
                else:
                    sig = (<object> entry.target_ref,
                           <object> entry.func if entry.func != NULL else None)
                    self._seen_refs.discard(sig)

                    Py_DECREF(entry.target_ref)
                    if entry.func != NULL:
                        Py_DECREF(entry.func)

                    self._count -= 1
                    if i < self._count:
                        self._callbacks[i] = self._callbacks[self._count]

    cpdef void subscribe(self, object callback):
        cdef object t_ref, t_func
        cdef tuple sig

        if type(callback) is MethodType:
            t_ref = weakref.ref(callback.__self__)
            t_func = callback.__func__
        else:
            t_ref = weakref.ref(callback)
            t_func = None

        sig = (t_ref, t_func)

        if sig not in self._seen_refs:
            self._seen_refs.add(sig)

            if self._capacity == 0:
                self._capacity = 4
                self._callbacks = <CallbackEntry *> malloc(
                    self._capacity * sizeof(CallbackEntry))
                if not self._callbacks: raise MemoryError()
            elif self._count == self._capacity:
                self._capacity *= 2
                self._callbacks = <CallbackEntry *> realloc(self._callbacks,
                                                            self._capacity * sizeof(CallbackEntry))
                if not self._callbacks: raise MemoryError()

            self._callbacks[self._count].target_ref = <PyObject *> t_ref
            Py_INCREF(<PyObject *> t_ref)

            if t_func is not None:
                self._callbacks[self._count].func = <PyObject *> t_func
                Py_INCREF(<PyObject *> t_func)
            else:
                self._callbacks[self._count].func = NULL

            self._count += 1

    cpdef void unsubscribe(self, object callback):
        cdef object t_ref, t_func
        cdef tuple sig
        cdef size_t i
        cdef PyObject * ref_ptr
        cdef PyObject * func_ptr

        if type(callback) is MethodType:
            t_ref = weakref.ref(callback.__self__)
            t_func = callback.__func__
        else:
            t_ref = weakref.ref(callback)
            t_func = None

        sig = (t_ref, t_func)

        if sig in self._seen_refs:
            self._seen_refs.discard(sig)

            ref_ptr = <PyObject *> t_ref
            func_ptr = <PyObject *> t_func if t_func is not None else NULL

            for i in range(self._count):
                if self._callbacks[i].target_ref == ref_ptr and self._callbacks[
                    i].func == func_ptr:

                    Py_DECREF(self._callbacks[i].target_ref)
                    if self._callbacks[i].func != NULL:
                        Py_DECREF(self._callbacks[i].func)

                    self._count -= 1
                    if i < self._count:
                        self._callbacks[i] = self._callbacks[self._count]
                    break
