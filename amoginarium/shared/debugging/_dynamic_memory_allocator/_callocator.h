#include <stdint.h>
#include <string.h>

typedef struct {
    uint32_t size;
    uint8_t free;
    uint32_t next;
} block_t;

typedef struct {
    uint32_t heap_size;
    uint32_t first_block;
} heap_t;

heap_t* get_heap(void* base);
static inline void* ptr_from_offset(void* base, uint32_t off);
uint32_t alloc(void* base, heap_t* heap, uint32_t size);
void free_block(void* base, heap_t* heap, uint32_t payload_off);
void init_heap(void* base, heap_t* heap, uint32_t size);
