# holds any constants needed in the project

# examples: window size, tick rate, input bindings, asset paths, default server host/port
# any .py files that need to can read constants from here

class Config:
    WINDOW_W = 960
    WINDOW_H = 540
    WINDOW_TITLE = "TBD"
    BG_COLOR = (18, 18, 24)

    # ticks
    CLIENT_FPS = 120
    FIXED_DT = 1.0 / 60.0

    # temporary player
    MOVE_SPEED = 220
    RECT_SIZE = (32, 64)
    RECT_COLOR = (90, 100, 255) 

    DASH_SPEED = 1000     # pixels per second while dashing
    DASH_DURATION = 0.1   # how long the dash lasts
    DASH_COOLDOWN = 1.0   # time before next dash
