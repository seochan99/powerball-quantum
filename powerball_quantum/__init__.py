"""
powerball-quantum: Powerball number predictor using quantum-inspired algorithm
"""

from .predictor import (
    predict,
    quick_pick,
    update_data,
    load_data,
    format_pick,
    Pick,
)

__version__ = "1.0.0"
__all__ = ["predict", "quick_pick", "update_data", "load_data", "format_pick", "Pick"]
