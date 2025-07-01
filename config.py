# config.py

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720

KEY_W, KEY_H = 60, 60
GAP = 10

ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
KEYS = []

for row_i, row in enumerate(ROWS):
    row_len = len(row)
    total_width = row_len*KEY_W + (row_len-1)*GAP
    start_x = (SCREEN_WIDTH - total_width)//2
    y = SCREEN_HEIGHT - (3 - row_i)*(KEY_H+GAP) - 100
    for j, ch in enumerate(row):
        x = start_x + j*(KEY_W+GAP)
        KEYS.append({'key': ch, 'rect': (x, y, KEY_W, KEY_H)})

# Spacebar
space_w = KEY_W*5 + GAP*4
space_x = (SCREEN_WIDTH - space_w)//2
space_y = SCREEN_HEIGHT - KEY_H - 20
KEYS.append({'key': 'SPACE', 'rect': (space_x, space_y, space_w, KEY_H)})

PINCH_THRESHOLD   = 40
DWELL_TIME        = 0.2
DEBOUNCE_INTERVAL = 0.3
