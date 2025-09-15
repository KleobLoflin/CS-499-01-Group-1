# holds any constants needed in the project

# examples: window size, tick rate, input bindings, asset paths, default server host/port
# any .py files that need to can read constants from here
import pygame

class Config:

    # window
    WINDOW_W = 640
    WINDOW_H = 360
    WINDOW_TITLE = "TBD"
    BG_COLOR = (18, 18, 24)

    # ticks
    CLIENT_FPS = 120
    FIXED_DT = 1.0 / 60.0

    # temporary player
    RECT_SIZE = (16, 16)
    RECT_COLOR = (90, 100, 255) 
