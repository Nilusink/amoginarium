#include <stdint.h>
#include <string.h>
#include "_callocator.h"

#define ALIGN4(x) (((x) + 3) & ~3)

heap_t* get_heap(void* base) {
    return (heap_t*)base;
}

static inline void* ptr_from_offset(void* base, uint32_t off) {
    return (uint8_t*)base + off;
}

uint32_t alloc(void* base, heap_t* heap, uint32_t size) {
    size = ALIGN4(size);

    uint32_t prev_off = 0;
    uint32_t curr_off = heap->first_block;

    while (curr_off != 0) {
        block_t* b = (block_t*)ptr_from_offset(base, curr_off);

        if (b->free && b->size >= size) {

            // split block if large enough
            if (b->size > size + sizeof(block_t) + 8) {
                uint32_t new_off = curr_off + sizeof(block_t) + size;

                block_t* newb = (block_t*)ptr_from_offset(base, new_off);
                newb->size = b->size - size - sizeof(block_t);
                newb->free = 1;
                newb->next = b->next;

                b->size = size;
                b->next = new_off;
            }

            b->free = 0;
            return curr_off + sizeof(block_t); // payload offset
        }

        prev_off = curr_off;
        curr_off = b->next;
    }

    return 0; // out of memory
}

void free_block(void* base, heap_t* heap, uint32_t payload_off) {
    if (payload_off == 0)
        return;

    block_t* b =
        (block_t*)((uint8_t*)base + payload_off - sizeof(block_t));

    b->free = 1;
}

void init_heap(void* base, heap_t* heap, uint32_t size) {
    heap->heap_size = size;
    heap->first_block = sizeof(heap_t);

    block_t* b = (block_t*)((uint8_t*)base + heap->first_block);
    b->size = size - sizeof(heap_t) - sizeof(block_t);
    b->free = 1;
    b->next = 0;
}