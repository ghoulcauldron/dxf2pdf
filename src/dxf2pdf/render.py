from __future__ import annotations

from pathlib import Path
from typing import Optional

import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from .report import compute_extents
from .units import UnitsInfo, units_to_inches


class RenderError(RuntimeError):
    pass


def render_true_scale_pdf(
    input_dxf: Path,
    output_pdf: Path,
    units: UnitsInfo,
) -> None:
    """
    Render DXF to a vector PDF whose *page size* matches the DXF extents in real units.

    - If units.unit is None, we still export, but page size becomes arbitrary (based on matplotlib defaults).
      In that case you should rerun with --units.
    """
    try:
        doc = ezdxf.readfile(str(input_dxf))
    except Exception as e:
        raise RenderError(f"Failed to read DXF: {input_dxf} ({e})") from e

    ext = compute_extents(doc)

    # Figure sizing: only meaningful if units are known.
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

    # Draw using ezdxf's drawing frontend (handles SPLINE/ARC/HATCH/TEXT/INSERT/etc. as supported)
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Save WITHOUT bbox_inches="tight" to preserve the figure's physical size.
    # bbox_inches="tight" would change page geometry and can break 1:1 size.
    fig.savefig(str(output_pdf), format="pdf", bbox_inches=None, pad_inches=0.0)
    plt.close(fig)