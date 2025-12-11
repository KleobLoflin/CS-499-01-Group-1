# GateCrashers

GateCrashers is a 2D co-op dungeon crawler built with **pygame-ce** and **pytmx**, featuring an ECS architecture, LAN multiplayer, map transitions, character selection, and pixel-art gameplay.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows**
```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install pygame-ce==2.5.7 pytmx==3.32
```

---

## Running the Game

Run the game from the project root:

```bash
python -m game.app
```

This launches the game and loads the Title Scene.

---

## Controls

### Movement
- **W / A / S / D** — Move up, left, down, right  
- **Arrow Keys** — Alternate movement controls

### Actions
- **SPACE** — Basic attack  
- **SHIFT** (Left or Right) — Dash

### Menus
- **W / S** or **UP / DOWN** — Navigate  
- **ENTER** or **SPACE** — Select  
- **ESC** — Back / cancel

### Pause
- **P** — Pause / unpause  
  - Freezes movement + attacks immediately  
  - Works during gameplay and while spectating another player

---

## Multiplayer Overview

GateCrashers supports LAN co-op with up to **five players** (host + four clients).

---

## Requirements

- **Python 3.10+**
- **pygame-ce 2.5.7**
- **pytmx 3.32**

---

## Credits

GateCrashers was developed as a senior design / capstone project by:

- Colin Adams  
- Scott Petty  
- Nicholas Loflin  
- Matthew Payne
- Cole Herzog