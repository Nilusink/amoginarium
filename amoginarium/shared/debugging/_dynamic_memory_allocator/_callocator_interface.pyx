from libc.stdint cimport uint32_t
from libc.string cimport memcpy, memset

from ._callocator cimport alloc, free_block, get_heap, heap_t

from multiprocessing.shared_memory import SharedMemory


cdef class SharedHeap:
    cdef void* base
    cdef heap_t* heap
    cdef object shm

    def __init__(self, name):
        self.shm = SharedMemory(name=name)
        self.base = <void*>self.shm.buf
        self.heap = self.heap = get_heap(self.base)

    cpdef alloc(self, int size):
        cdef uint32_t off
        off = alloc(self.base, self.heap, size)
        cdef char* ptr = <char*>self.base + off
        memset(ptr, 0, size)
        return off

    cpdef free(self, int off):
        free_block(self.base, self.heap, off)

    cpdef write(self, int off, bytes data):
        cdef char* ptr = <char*>self.base + off
        cdef Py_ssize_t n = len(data)

        memcpy(ptr, <char*>data, n)

    cpdef read(self, int off, int n):
        cdef char* ptr = <char*>self.base + off
        return <bytes>ptr[:n]
