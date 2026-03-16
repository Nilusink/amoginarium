"""
/test_pg.py

Project: amoginarium
Created: 16.03.2026
Authors: LukasKrah
"""
import pygame as pg
import sys

# Initialize Pygame
pg.init()
screen = pg.display.set_mode((400, 300))
clock = pg.time.Clock()

# Colors
BG_COLOR = (30, 30, 30)
RECT_COLOR = (0, 200, 150)

while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.init()
            sys.exit()

    screen.fill(BG_COLOR)

    # Drawing the rounded rectangle
    # rect(surface, color, (x, y, width, height), border_radius)
    pg.draw.rect(screen, RECT_COLOR, (100, 100, 200, 100), border_radius=20)

    pg.display.flip()
    clock.tick(60)
