"""Central configuration for paths, theme constants, and shared Plotly layout."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Directory paths (all relative to project root)
# ---------------------------------------------------------------------------
ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = ROOT / "data"
MODELS_DIR: Path = ROOT / "models"
REPORTS_DIR: Path = ROOT / "reports"
IMAGES_DIR: Path = ROOT / "images"
FONTS_DIR: Path = ROOT / "fonts"

# ---------------------------------------------------------------------------
# Theme color constants (retro neon dark)
# ---------------------------------------------------------------------------
BG: str = "#0D0D0D"
BG_SECONDARY: str = "#1A1A2E"
CYAN: str = "#00FFCC"
PINK: str = "#FF6EC7"
YELLOW: str = "#FFFF00"
PURPLE: str = "#7B68EE"
TEXT_COLOR: str = "#E0E0E0"

# ---------------------------------------------------------------------------
# Shared Plotly layout dict
# ---------------------------------------------------------------------------
PLOTLY_LAYOUT: dict = {
    "template": "plotly_dark",
    "paper_bgcolor": BG,
    "plot_bgcolor": BG_SECONDARY,
    "font": {"color": TEXT_COLOR},
}
