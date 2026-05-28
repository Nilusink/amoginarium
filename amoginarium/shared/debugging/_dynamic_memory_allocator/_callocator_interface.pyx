from libc.stdint cimport uint32_t, uint8_t
from libc.string cimport memcpy, memset

from ._callocator cimport alloc, free_block, get_heap, heap_t, init_heap

from multiprocessing.shared_memory import SharedMemory


cdef class SharedHeap:
    cdef void* base
    cdef heap_t* heap
    cdef object shm
    cdef unsigned char[:] _view

    def __init__(self, shm: SharedMemory):
        self.shm = shm

        # store shared memory object + memory view
        self._view = self.shm.buf
        self.base = <void*>&self._view[0]
        self.heap = get_heap(self.base)

        # initialize heap
        init_heap(self.base, self.heap, shm.size)

    cpdef alloc(self, int size):
        cdef uint32_t off

        # try to get offset
        off = alloc(self.base, self.heap, size)

        # check if invalid
        if off == 0:
            msg = "Out of memory"
            raise MemoryError(msg)

        # initialize block to 0
        cdef char* ptr = <char*>self.base + off
        memset(ptr, 0, size)

        # return offset
        return off

    cpdef free(self, int off):
        free_block(self.base, self.heap, off)

    cpdef write(self, int off, bytes data):
        cdef char* ptr = <char*>self.base + off
        cdef Py_ssize_t n = len(data)

        memcpy(ptr, <char*>data, n)

    cpdef write_byte(self, int off, uint8_t data):
        cdef char* ptr = <char*>self.base + off
        memcpy(ptr, &data, 1)

    cpdef bytes read(self, int off, int n):
        cdef char* ptr = <char*>self.base + off
        return <bytes>ptr[:n]

    cpdef int read_byte(self, int off):  # type: (int) -> int
        cdef char* ptr = <char*>self.base + off
        return <int>ptr[0]
