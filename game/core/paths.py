import sys
from pathlib import Path

def resource_path(relative: str) -> str:
    """
    Resolves paths for both:
    - Source execution
    - Frozen PyInstaller executable
    """
    if hasattr(sys, "_MEIPASS"):
        # Running from the PyInstaller bundle
        base = Path(sys._MEIPASS)
    else:
        # Running from source; repo root = one folder above /game/
        base = Path(__file__).resolve().parents[2]

    return str(base / relative)
