from libc.stdint cimport uint32_t


cdef extern from "_callocator.h":
    ctypedef struct heap_t:
        pass

    heap_t* get_heap(void* base)
    uint32_t alloc(void* base, heap_t* heap, uint32_t size)
    void free_block(void* base, heap_t* heap, uint32_t off)
    void init_heap(void* base, heap_t* heap, uint32_t size)

