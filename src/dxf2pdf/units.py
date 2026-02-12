from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# DXF header $INSUNITS mapping (common values)
# 0 = Unitless
# 1 = Inches
# 4 = Millimeters
# 5 = Centimeters
# 6 = Meters
INSUNITS_TO_UNIT = {
    0: None,
    1: "in",
    4: "mm",
    5: "cm",
    6: "m",
}

UNIT_TO_INCH = {
    "in": 1.0,
    "mm": 1.0 / 25.4,
    "cm": 1.0 / 2.54,
    "m": 39.37007874015748,
}

UNIT_LABEL = {
    "in": "inches",
    "mm": "millimeters",
    "cm": "centimeters",
    "m": "meters",
}

SUPPORTED_UNITS = tuple(UNIT_TO_INCH.keys())


@dataclass(frozen=True)
class UnitsInfo:
    unit: Optional[str]           # "mm" | "in" | "cm" | "m" | None
    source: str                   # "insunits" | "override" | "unknown"


def detect_units_from_doc(doc) -> UnitsInfo:
    try:
        code = int(doc.header.get("$INSUNITS", 0))
    except Exception:
        code = 0

    unit = INSUNITS_TO_UNIT.get(code, None)
    if unit is None:
        return UnitsInfo(unit=None, source="unknown")
    return UnitsInfo(unit=unit, source="insunits")


def resolve_units(doc, override: Optional[str]) -> UnitsInfo:
    if override:
        if override not in SUPPORTED_UNITS:
            raise ValueError(f"Unsupported units override: {override} (use one of {SUPPORTED_UNITS})")
        return UnitsInfo(unit=override, source="override")

    detected = detect_units_from_doc(doc)
    return detected


def units_to_inches(value: float, unit: str) -> float:
    return value * UNIT_TO_INCH[unit]