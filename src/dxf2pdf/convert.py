from __future__ import annotations

from pathlib import Path
from typing import Optional

import ezdxf

from .render import render_true_scale_pdf
from .report import build_report, write_report_json
from .units import resolve_units
from .utils import ensure_parent_dir


def convert_one(
    input_path: Path,
    out_pdf: Optional[Path] = None,
    units_override: Optional[str] = None,
    write_report: bool = False,
    out_svg: bool = False,
) -> list[Path]:
    if out_pdf is None:
        out_pdf = input_path.with_suffix(".pdf")

    # Load once for unit resolution sanity, then render re-reads (simple & reliable)
    doc = ezdxf.readfile(str(input_path))
    units = resolve_units(doc, units_override)

    ensure_parent_dir(out_pdf)
    render_true_scale_pdf(input_path, out_pdf, units)

    outputs: list[Path] = [out_pdf]

    if write_report:
        report = build_report(input_path, units)
        report_path = out_pdf.with_suffix(".report.json")
        write_report_json(report, report_path)
        outputs.append(report_path)

    if out_svg:
        # Optional SVG export using ezdxf drawing add-on if you want a second vector artifact.
        # This can be useful for sanity-checking in Illustrator.
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.svg import SVGBackend
        from .report import compute_extents

        doc2 = ezdxf.readfile(str(input_path))
        ext = compute_extents(doc2)
        width = ext.width
        height = ext.height

        # SVG backend uses drawing units directly; Illustrator import will interpret as px unless you manage units.
        # We include it as an optional debugging/interop artifact, not the primary “true scale” path.
        ctx = RenderContext(doc2)
        backend = SVGBackend()
        Frontend(ctx, backend).draw_layout(doc2.modelspace(), finalize=True)
        svg_str = backend.get_string()
        svg_path = out_pdf.with_suffix(".svg")
        svg_path.write_text(svg_str, encoding="utf-8")
        outputs.append(svg_path)

    return outputs