#  Touchless Keyboard

A hand gesture-controlled virtual keyboard using computer vision and hand tracking. Type without touching your keyboard using intuitive hand gestures detected through your webcam!

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/opencv-4.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

##  Features

### Core Features
-  **Touchless Typing** - Type using hand gestures, no physical contact needed
-  **Real-time Hand Tracking** - Powered by MediaPipe and cvzone
-  **Full QWERTY Layout** - Complete keyboard with numbers, letters, and special keys
-  **Audio Feedback** - Click sounds for better user experience
-  **Visual Feedback** - Distance indicators and click-ready alerts

### Modern UI
-  **Gradient Keys** - Beautiful gradient backgrounds with smooth colors
-  **Glow Effects** - Glowing borders on hover for futuristic look
-  **4 Color Themes** - Dark, Neon, Cyberpunk, Light (press 't' to cycle)
-  **Responsive Layout** - Auto-scales keyboard based on screen resolution

### Advanced Features
-  **Smart Typing** - Caps Lock, NumPad, Undo/Redo support
-  **Accessibility** - High Contrast theme and adjustable keyboard size
-  **Helper Tools** - On-screen help overlay and volume control
-  **Save & Copy** - Save typed text to file or copy to clipboard
-  **Structured Logging** - Rotating file logs for debugging
-  **AI Version** - Dual-hand control with ML data collection

---

##  Gesture Controls

### Basic Gestures

| Gesture | Action | Description |
|---------|--------|-------------|
|  **Thumb + Index Pinch** | Click/Select | Bring thumb and index finger close together (< 50px) |
|  **Thumb + Middle Pinch** | Exit | Bring thumb and middle finger together to close app |
|  **Index Finger Hover** | Navigate | Move index finger to hover over keys |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `H` | Toggle help overlay |
| `N` | Toggle NumPad / QWERTY layout |
| `S` | Save typed text to file |
| `C` | Copy text to clipboard |
| `T` | Cycle through color themes |
| `U` / `R` | Undo / Redo typing |
| `+` / `-` | Increase / Decrease keyboard size |
| `[` / `]` | Decrease / Increase volume |
| `K` | Start calibration mode |
| `ESC` | Exit application |

---

##  Installation

### Prerequisites

- Python 3.8 or higher
- Webcam
- Windows/Linux/macOS

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/Touchless-Keyboard.git
cd Touchless-Keyboard
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

##  Usage

### Basic Keyboard

Run the standard single-hand virtual keyboard:

```bash
python run.py
```

**Features:**
- Single-hand operation
- Modern gradient UI with glow effects
- 4 color themes (Dark, Neon, Cyberpunk, Light)
- Shift key for lowercase/uppercase
- Responsive keyboard sizing
- Click delay: 0.5s

### AI-Enhanced Keyboard

Run the advanced dual-hand version with ML data collection:

```bash
python run.py --ai
```

**Features:**
- Dual-hand control (left hand clicks, right hand navigates)
- Click threshold: 40px (more precise)
- Click delay: 0.5s (faster)
- Gesture data logging for ML training

**Additional Controls:**
- Press `c` to save click gesture data
- Press `m` to save move gesture data
- Press `e` to save exit gesture data

### Gesture Data Collection

Collect training data for custom gesture recognition:

```bash
python -m tools.collect_gesture_data
```

1. Enter a gesture label (e.g., "thumbs_up", "peace_sign")
2. Position your hand in the gesture
3. Press `s` to save frames
4. Press `q` to quit

Data is saved to `gesture_data.csv` with 21 hand landmarks (x, y, z coordinates).

---

##  Keyboard Layout

The keyboard adapts based on the active mode (QWERTY or NumPad).

**QWERTY Mode (Standard):**
```
 CAPS   1  2  3  4  5  6  7  8  9  0  <-
  Q  W  E  R  T  Y  U  I  O  P  [  ]
   A  S  D  F  G  H  J  K  L  ;  '
    Z  X  C  V  B  N  M  ,  .  ?
       SPACE      ENTER    TAB
```

**NumPad Mode (Press 'N'):**
```
      7  8  9  /
      4  5  6  *
      1  2  3  -
      0  .  <- +
      ENTER   ABC
```

**Special Keys:**
- `CAPS` = Caps Lock toggle
- `NUM` / `ABC` = Switch layout
- `SHIFT` = Toggle case (one-time)
- `__` = Spacebar
- `<-` = Backspace

---

##  Configuration

### Color Themes

Press `t` during runtime to cycle through themes:

| Theme | Description |
|-------|-------------|
| **Dark** | Default dark mode with green accents |
| **Neon** | Purple/magenta with cyan text |
| **Cyberpunk** | Dark blue with gold/yellow |
| **Light** | Light mode for bright environments |
| **High Contrast** | Black/White/Yellow for max visibility |

### Gesture Settings

Edit `src/utils/settings.py` or use the settings file created at `~/.touchless_keyboard/settings.json`.

---

##  Troubleshooting

### Webcam Not Detected

**Problem:** "Could not open webcam" error

**Solutions:**
1. Check if webcam is connected and working
2. Set Environment Variable `WEBCAM_INDEX`:
   ```bash
   # Windows PowerShell
   $env:WEBCAM_INDEX=1; python run.py
   ```
3. Grant camera permissions to Python

### Audio Not Working

**Problem:** No click sound

**Solutions:**
1. Check if `clickSound.mp3` exists in `assets/`
2. Press `]` to increase volume
3. Verify pygame installation: `pip install pygame`

### Hand Not Detected / Jittery

**Problem:** Cursor shaking or not moving smoothly

**Solutions:**
1. Ensure good lighting conditions
2. Press `K` to run calibration
3. Adjust `smoothing_factor` in settings (lower = smoother)
4. Keep hand within camera frame

---

##  Project Structure

```
Touchless-Keyboard/
├── run.py                      # Main launcher script
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
├── src/                        # Source code package
│   ├── __init__.py
│   ├── core/                   # Core application logic
│   │   ├── gesture_handler.py  # Gesture detection + calibration
│   │   └── keyboard_utils.py   # Gradient keys, glow effects
│   ├── utils/                  # Utility modules
│   │   ├── config.py           # Configuration settings
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── file_utils.py       # File/clipboard operations
│   │   ├── logging_config.py   # Structured logging
│   │   ├── performance_monitor.py
│   │   └── themes.py           # Color themes
│   └── apps/                   # Application entry points
│       ├── main.py             # Main keyboard with modern UI
│       └── virtual_keyboard_ai.py
├── tools/                      # Standalone tools
│   └── collect_gesture_data.py # ML data collection
├── assets/                     # Static assets
│   └── clickSound.mp3          # Audio feedback
└── data/                       # Generated data (gitignored)
    └── gesture_data.csv        # ML training data
```

---

##  Contributing

Contributions are welcome!

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Roadmap

- [x] Basic gesture keyboard
- [x] Dual-hand AI version
- [x] Gesture data collection
- [x] Special keys (Caps, Num, Punctuation)
- [x] Visual feedback & Help System
- [x] Save/Copy & Undo/Redo
- [x] Settings & Calibration
- [x] Accessibility (High Contrast, Scaling)
- [ ] ML gesture recognition model
- [ ] Word prediction
- [ ] Mobile app version

---

**Made with ❤️ and hand gestures**
