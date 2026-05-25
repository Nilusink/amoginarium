"""
Tests multi-device input using Windows Raw Input and PyOpenGL.

| ``Path``: amoginarium/_test_individual_inputs/test_pg.py
| ``Project``: amoginarium
| ``Created``: 16.03.2026
| ``Authors``: LukasKrah
"""

import ctypes
import random
import sys
from ctypes import wintypes

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *

user32 = ctypes.windll.user32

# --- Win32 Constants & Structs ---
WM_INPUT = 0x00FF
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RID_INPUT = 0x10000003
GWLP_WNDPROC = -4

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)

user32.CallWindowProcW.argtypes = [
    ctypes.c_void_p,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.CallWindowProcW.restype = LRESULT

if ctypes.sizeof(ctypes.c_void_p) == 8:
    set_window_long = user32.SetWindowLongPtrW
    restore_window_long = user32.SetWindowLongPtrW
else:
    set_window_long = user32.SetWindowLongW
    restore_window_long = user32.SetWindowLongW

set_window_long.argtypes = [wintypes.HWND, ctypes.c_int, WNDPROC]
set_window_long.restype = ctypes.c_void_p
restore_window_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
restore_window_long.restype = ctypes.c_void_p

user32.GetRawInputData.argtypes = [
    wintypes.LPARAM,
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT,
]
user32.GetRawInputData.restype = wintypes.UINT


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.WORD),
        ("usUsage", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]


class RAWMOUSE(ctypes.Structure):
    class _BUTTONS(ctypes.Union):
        class _STRUCT(ctypes.Structure):
            _fields_ = [
                ("usButtonFlags", wintypes.USHORT),
                ("usButtonData", wintypes.USHORT),
            ]

        _fields_ = [("ulButtons", wintypes.ULONG), ("struct", _STRUCT)]

    _anonymous_ = ("buttons",)
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("buttons", _BUTTONS),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]


class RAWINPUT(ctypes.Structure):
    class _DATA(ctypes.Union):
        _fields_ = [
            ("mouse", RAWMOUSE),
            ("keyboard", RAWKEYBOARD),
            ("hid", wintypes.DWORD * 4),
        ]

    _anonymous_ = ("data",)
    _fields_ = [("header", RAWINPUTHEADER), ("data", _DATA)]


# --- Global State ---
original_wndproc = None
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Dictionaries format: { hDevice: {'x': int, 'y': int, 'color': (R, G, B), ...} }
mice_state = {}
keyboards_state = {}

# Virtual Key Codes for WASD
VK_W = 0x57
VK_A = 0x41
VK_S = 0x53
VK_D = 0x44


# --- Core Functions ---


def register_raw_input(hwnd):
    rids = (RAWINPUTDEVICE * 2)()
    rids[0].usUsagePage, rids[0].usUsage, rids[0].dwFlags, rids[0].hwndTarget = (
        0x01,
        0x02,
        0,
        hwnd,
    )  # Mouse
    rids[1].usUsagePage, rids[1].usUsage, rids[1].dwFlags, rids[1].hwndTarget = (
        0x01,
        0x06,
        0,
        hwnd,
    )  # Keyboard
    user32.RegisterRawInputDevices(rids, 2, ctypes.sizeof(RAWINPUTDEVICE))


def custom_wndproc(hwnd, msg, wparam, lparam):
    if msg == WM_INPUT:
        size = wintypes.UINT(0)
        user32.GetRawInputData(
            lparam, RID_INPUT, None, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER)
        )

        if size.value > 0:
            buffer = ctypes.create_string_buffer(size.value)
            if (
                user32.GetRawInputData(
                    lparam,
                    RID_INPUT,
                    buffer,
                    ctypes.byref(size),
                    ctypes.sizeof(RAWINPUTHEADER),
                )
                > 0
            ):
                raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents
                hDev = raw.header.hDevice

                # --- Process Mouse Data ---
                if raw.header.dwType == RIM_TYPEMOUSE:
                    dx = raw.mouse.lLastX
                    dy = raw.mouse.lLastY

                    if dx != 0 or dy != 0:
                        if hDev not in mice_state:
                            mice_state[hDev] = {
                                "x": WINDOW_WIDTH // 2,
                                "y": WINDOW_HEIGHT // 2,
                                "color": (
                                    random.random(),
                                    random.random(),
                                    random.random(),
                                ),
                            }
                        mice_state[hDev]["x"] += dx
                        mice_state[hDev]["y"] += dy
                        mice_state[hDev]["x"] = max(
                            0, min(WINDOW_WIDTH, mice_state[hDev]["x"])
                        )
                        mice_state[hDev]["y"] = max(
                            0, min(WINDOW_HEIGHT, mice_state[hDev]["y"])
                        )

                # --- Process Keyboard Data ---
                elif raw.header.dwType == RIM_TYPEKEYBOARD:
                    vkey = raw.keyboard.VKey
                    # Flags bit 0 determines state (0 = KeyDown, 1 = KeyUp)
                    is_down = (raw.keyboard.Flags & 1) == 0

                    # Register new keyboard if unseen
                    if hDev not in keyboards_state:
                        keyboards_state[hDev] = {
                            "x": WINDOW_WIDTH // 2,
                            "y": WINDOW_HEIGHT // 2,
                            "color": (
                                random.random(),
                                random.random(),
                                random.random(),
                            ),
                            "keys": {
                                VK_W: False,
                                VK_A: False,
                                VK_S: False,
                                VK_D: False,
                            },
                        }

                    # Update key states for this specific keyboard
                    if vkey in keyboards_state[hDev]["keys"]:
                        keyboards_state[hDev]["keys"][vkey] = is_down

    return user32.CallWindowProcW(original_wndproc, hwnd, msg, wparam, lparam)


wndproc_callback = WNDPROC(custom_wndproc)


def apply_keyboard_movement():
    """Moves keyboard dots smoothly based on their currently held keys."""
    speed = 5
    for state in keyboards_state.values():
        if state["keys"][VK_W]:
            state["y"] -= speed
        if state["keys"][VK_S]:
            state["y"] += speed
        if state["keys"][VK_A]:
            state["x"] -= speed
        if state["keys"][VK_D]:
            state["x"] += speed

        state["x"] = max(0, min(WINDOW_WIDTH, state["x"]))
        state["y"] = max(0, min(WINDOW_HEIGHT, state["y"]))


def draw_entities():
    """Draws colored dots for every active mouse and keyboard."""
    glPointSize(15.0)
    glBegin(GL_POINTS)

    # Draw Mice
    for state in mice_state.values():
        glColor3f(*state["color"])
        glVertex2f(state["x"], state["y"])

    # Draw Keyboards
    for state in keyboards_state.values():
        glColor3f(*state["color"])
        glVertex2f(state["x"], state["y"])

    glEnd()


# --- Main Application ---


def main():
    pygame.init()
    display = (WINDOW_WIDTH, WINDOW_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Multi-Mouse & Multi-Keyboard Surface")

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(0.1, 0.1, 0.1, 1)

    wm_info = pygame.display.get_wm_info()
    hwnd = wm_info["window"]
    register_raw_input(hwnd)

    global original_wndproc
    original_wndproc = set_window_long(hwnd, GWLP_WNDPROC, wndproc_callback)

    print("--- MULTI-INPUT ACTIVE ---")
    print("Move mice or use W/A/S/D on any keyboard to spawn and move dots.")
    print("Press ESCAPE on any keyboard to exit.")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        # Apply continuous movement for held keyboard keys
        apply_keyboard_movement()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_entities()
        pygame.display.flip()

        clock.tick(60)  # Lock to 60 FPS for consistent movement speed

    restore_window_long(hwnd, GWLP_WNDPROC, original_wndproc)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
