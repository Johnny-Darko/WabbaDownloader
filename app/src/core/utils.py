"""
This module contains utility functions that are used in the project.

Useful functions:
- convert_byte_size: Convert a size in bytes to a human-readable format.
"""

import math

def convert_byte_size(size_in_bytes: int|float) -> str:
    """
    Convert the size in bytes to a human-readable format.
    """
    assert isinstance(size_in_bytes, (int, float)), f"size_in_bytes must be integer or float, given {type(size_in_bytes)} instead"
    assert size_in_bytes >= 0, "size_in_bytes must be greater than or equal to 0"

    if size_in_bytes == 0:
        return "0B"
    size_units: tuple[str, ...] = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    unit_index: int = min(int(math.floor(math.log(size_in_bytes, 1024))), len(size_units) - 1)
    size_in_unit: float = math.pow(1024, unit_index)
    size_rounded: float = round(size_in_bytes / size_in_unit, 2)
    return f"{size_rounded:.2f}{size_units[unit_index]}"
