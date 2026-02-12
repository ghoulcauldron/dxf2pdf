from __future__ import annotations

from pathlib import Path

import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from .report import compute_extents
from .units import UnitsInfo, units_to_inches


class RenderError(RuntimeError):
    pass


def _normalize_aci_white(doc: ezdxf.EzDxfDocument) -> None:
    """
    Emulate AutoCAD white-on-black logic:
    If effective color resolves to ACI 7, force true black.
    """

    # Fix layers first
    for layer in doc.layers:
        if layer.color == 7:
            layer.dxf.true_color = 0x000000  # RGB black
            layer.color = 256  # BYLAYER (neutral)

    # Fix entities (including inside blocks)
    def fix_entity(e):
        try:
            if e.dxf.hasattr("color") and e.dxf.color == 7:
                e.dxf.true_color = 0x000000
                e.dxf.color = 256
        except Exception:
            pass

    for e in doc.modelspace():
        fix_entity(e)

    for block in doc.blocks:
        for e in block:
            fix_entity(e)


def _scrub_hash_numbers(doc: ezdxf.EzDxfDocument) -> None:
    """
    Remove TEXT entities whose content begins with '#'.
    Applied to both modelspace and all blocks.
    """
    def process_container(container):
        for e in list(container):
            if e.dxftype() == "TEXT":
                try:
                    if e.dxf.text.strip().startswith("#"):
                        container.delete_entity(e)
                except Exception:
                    pass

    process_container(doc.modelspace())

    for block in doc.blocks:
        process_container(block)


def _convert_points_to_circles(doc: ezdxf.EzDxfDocument, units: UnitsInfo) -> None:
    """
    Replace POINT entities with small black CIRCLE entities (~2pt stroke visual size).
    """
    # 2pt diameter ≈ 0.7056 mm → radius ≈ 0.35 mm
    radius_mm = 0.35

    if units.unit == "in":
        radius = radius_mm / 25.4
    elif units.unit == "cm":
        radius = radius_mm / 10.0
    elif units.unit == "m":
        radius = radius_mm / 1000.0
    else:
        # default to mm if unknown
        radius = radius_mm

    def process_container(container):
        for e in list(container):
            if e.dxftype() == "POINT":
                try:
                    center = e.dxf.location
                    container.delete_entity(e)
                    circle = container.add_circle(center, radius)
                    circle.dxf.color = 0  # black
                    circle.dxf.lineweight = 9  # ~0.25pt
                except Exception:
                    pass

    process_container(doc.modelspace())

    for block in doc.blocks:
        process_container(block)


def _uniform_strokes(doc: ezdxf.EzDxfDocument) -> None:
    """
    Force all entity strokes to ~0.1pt except circles created from POINTs.
    DXF lineweight units are in 1/100 mm.
    0.1pt ≈ 0.0353 mm → ~4 in DXF units.
    """
    target_lineweight = 4  # ~0.1pt

    def process_container(container):
        for e in container:
            try:
                if e.dxftype() != "CIRCLE":
                    if e.dxf.hasattr("lineweight"):
                        e.dxf.lineweight = target_lineweight
            except Exception:
                pass

    process_container(doc.modelspace())

    for block in doc.blocks:
        process_container(block)


def render_true_scale_pdf(
    input_dxf: Path,
    output_pdf: Path,
    units: UnitsInfo,
) -> None:
    try:
        doc = ezdxf.readfile(str(input_dxf))
    except Exception as e:
        raise RenderError(f"Failed to read DXF: {input_dxf} ({e})") from e

    # 🔥 Normalize ACI white behavior BEFORE rendering
    _normalize_aci_white(doc)
    _scrub_hash_numbers(doc)
    _convert_points_to_circles(doc, units)
    _uniform_strokes(doc)

    ext = compute_extents(doc)

    fig_kwargs = {}
    if units.unit is not None:
        w_in = max(units_to_inches(ext.width, units.unit), 0.01)
        h_in = max(units_to_inches(ext.height, units.unit), 0.01)
        fig_kwargs["figsize"] = (w_in, h_in)

    fig = plt.figure(**fig_kwargs)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(ext.min_x, ext.max_x)
    ax.set_ylim(ext.min_y, ext.max_y)
    ax.axis("off")

    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(str(output_pdf), format="pdf", bbox_inches=None, pad_inches=0.0)
    plt.close(fig)