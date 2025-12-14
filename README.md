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
-  **Shift Key** - Toggle lowercase/uppercase with SHIFT key
-  **Save & Copy** - Save typed text to file or copy to clipboard
-  **Structured Logging** - Professional logging with timestamps
-  **AI Version** - Dual-hand control with ML data collection
-  **Gesture Data Collection** - Build custom gesture recognition models

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
| `S` | Save typed text to file |
| `C` | Copy text to clipboard |
| `T` | Cycle through color themes |
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

```

 SHIFT  1  2  3  4  5  6  7  8  9  0  <-

  Q  W  E  R  T  Y  U  I  O  P  !

   A  S  D  F  G  H  J  K  L  ;  '

    Z  X  C  V  B  N  M  ,  .  ?

       SPACE      ENTER    TAB

```

**Special Keys:**
- `SHIFT` = Toggle case (auto-disables after letter)
- `__` = Spacebar
- `<-` = Backspace
- `ENTER` = Enter/Return
- `TAB` = Tab
- `;`, `'`, `,`, `.`, `?`, `!` = Punctuation

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

### Gesture Settings

Edit `src/utils/config.py` to customize:

```python
# Gesture thresholds
PINCH_THRESHOLD = 40        # Distance for pinch detection (pixels)
DWELL_TIME = 0.2           # Hover time before activation (seconds)
DEBOUNCE_INTERVAL = 0.3    # Minimum time between clicks (seconds)

# Hand detection
DETECTION_CONFIDENCE = 0.8  # Hand detection confidence (0.0-1.0)
MAX_HANDS = 2              # Maximum hands to detect

# UI
BORDER_RADIUS = 20         # Corner radius for keys (pixels)
FLASH_DURATION = 0.3       # Key flash duration (seconds)
```

---

##  Troubleshooting

### Webcam Not Detected

**Problem:** "Could not open webcam" error

**Solutions:**
1. Check if webcam is connected and working
2. Try changing camera index in code:
   ```python
   cap = cv2.VideoCapture(1)  # Try 1, 2, etc.
   ```
3. Grant camera permissions to Python
4. Close other apps using the webcam

### Audio Not Working

**Problem:** No click sound

**Solutions:**
1. Check if `clickSound.mp3` exists in project folder
2. Application will continue without audio (warning shown)
3. Verify pygame installation: `pip install pygame`

### Hand Not Detected

**Problem:** "Hand Not Detected" message

**Solutions:**
1. Ensure good lighting conditions
2. Position hand clearly in front of camera
3. Adjust `DETECTION_CONFIDENCE` in config.py (lower = more sensitive)
4. Keep hand within camera frame

### Gestures Not Registering

**Problem:** Clicks not working

**Solutions:**
1. Adjust `CLICK_THRESHOLD` in code (increase for easier detection)
2. Ensure thumb and index finger are clearly visible
3. Practice pinch gesture - bring fingers closer together
4. Check `CLICK_DELAY` - may need to wait between clicks

### Performance Issues

**Problem:** Lag or low FPS

**Solutions:**
1. Close other applications
2. Reduce webcam resolution in code
3. Update graphics drivers
4. Use a more powerful computer

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
│   │   └── themes.py           # Color themes (Dark, Neon, etc.)
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

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Ideas for Contributions

- Add more gesture types
- Implement ML gesture recognition
- Add word prediction/autocomplete
- Multi-language keyboard layouts
- Mobile/tablet support
- Performance optimizations
- UI themes and customization

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Acknowledgments

- **MediaPipe** - Hand tracking technology
- **cvzone** - Simplified hand detection
- **OpenCV** - Computer vision library
- **PyAutoGUI** - Keyboard simulation

---

## 🌟 Star History

If you find this project useful, please consider giving it a  on GitHub!

---

##  Screenshots

### Main Keyboard Interface
![Main Interface](screenshots/main_interface.png)

### Gesture Detection
![Gesture Detection](screenshots/gesture_detection.png)

### AI Version with Dual Hands
![AI Version](screenshots/ai_version.png)

---

##  Roadmap

- [x] Basic gesture keyboard
- [x] Dual-hand AI version
- [x] Gesture data collection
- [x] Special keys and punctuation
- [x] Visual feedback system
- [x] Save/copy functionality
- [ ] ML gesture recognition model
- [ ] Settings UI with calibration
- [ ] Word prediction
- [ ] Multi-language support
- [ ] Mobile app version

---

**Made with ❤️ and hand gestures**
