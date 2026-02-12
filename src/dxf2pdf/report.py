from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import ezdxf
from ezdxf import bbox

from .units import UnitsInfo, units_to_inches


@dataclass(frozen=True)
class Extents:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


@dataclass(frozen=True)
class DxfReport:
    input_path: str
    units: UnitsInfo
    extents_modelspace: Extents
    physical_width_in: Optional[float]
    physical_height_in: Optional[float]


class ReportError(RuntimeError):
    pass


def compute_extents(doc) -> Extents:
    msp = doc.modelspace()
    try:
        ext = bbox.extents(msp)
    except Exception as e:
        raise ReportError(f"Failed computing extents: {e}") from e

    if ext is None:
        raise ReportError("No extents found (empty modelspace?)")

    (minx, miny, _minz), (maxx, maxy, _maxz) = ext.extmin, ext.extmax
    return Extents(min_x=float(minx), min_y=float(miny), max_x=float(maxx), max_y=float(maxy))


def build_report(input_path: Path, units: UnitsInfo) -> DxfReport:
    doc = ezdxf.readfile(str(input_path))
    ex = compute_extents(doc)

    pw = ph = None
    if units.unit is not None:
        pw = units_to_inches(ex.width, units.unit)
        ph = units_to_inches(ex.height, units.unit)

    return DxfReport(
        input_path=str(input_path),
        units=units,
        extents_modelspace=ex,
        physical_width_in=pw,
        physical_height_in=ph,
    )


def write_report_json(report: DxfReport, out_path: Path) -> None:
    import json
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # dataclasses -> dict (including nested dataclasses)
    payload = asdict(report)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)