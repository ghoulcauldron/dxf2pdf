# dxf2pdf

DXF → **true-scale** vector PDF for flat fashion pattern drawings (Photoshop import for art/print placement).

Core goals:
- **True scale (1:1 physical size)** in exported PDF page size
- **Vector output** (no rasterization)
- CAD-ish entity support via ezdxf drawing pipeline:
  - SPLINE, ARC, HATCH, TEXT/MTEXT, INSERT (blocks), lineweights, layers

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .