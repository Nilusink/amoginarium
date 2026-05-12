from cpython.ref cimport PyObject

ctypedef struct CallbackEntry:
    PyObject * target_ref
    PyObject * func

cdef class CyObservable:
    cdef object _value
    cdef public object __orig_class__

    cdef CallbackEntry * _callbacks
    cdef size_t _capacity
    cdef size_t _count
    cdef set _seen_refs

    cpdef object get_value(self)
    cpdef void set_value(self, object new_value)

    cpdef void subscribe(self, object callback)
    cpdef void unsubscribe(self, object callback)
