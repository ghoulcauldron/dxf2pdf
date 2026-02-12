from __future__ import annotations

import sys
from pathlib import Path
import click

from .convert import convert_one
from .utils import is_dxf


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--out", "out_pdf", type=click.Path(path_type=Path), help="Output PDF path.")
@click.option("--units", type=click.Choice(["mm", "in", "cm", "m"]), help="Override DXF units for true-scale export.")
@click.option("--report", is_flag=True, help="Write a JSON report (units + extents + physical size).")
@click.option("--svg", is_flag=True, help="Also export an SVG (debug/interop helper).")
@click.option("--batch", is_flag=True, help="Convert all .dxf files in a directory.")
@click.option("--recursive", is_flag=True, help="With --batch, recurse into subfolders.")
def main(input_path: Path, out_pdf: Path | None, units: str | None, report: bool, svg: bool,
         batch: bool, recursive: bool):
    """
    DXF → true-scale vector PDF (pattern-friendly).

    INPUT_PATH: a .dxf file (default) or a directory when using --batch.
    """
    if batch:
        if not input_path.is_dir():
            raise click.ClickException("--batch requires INPUT_PATH to be a directory.")
        pattern = "**/*.dxf" if recursive else "*.dxf"
        files = sorted(input_path.glob(pattern))
        if not files:
            click.echo("No .dxf files found.")
            return

        failures = 0
        for f in files:
            try:
                outs = convert_one(f, out_pdf=None, units_override=units, write_report=report, out_svg=svg)
                click.echo(f"✔ {f} → " + ", ".join(str(p) for p in outs))
            except Exception as e:
                failures += 1
                click.echo(f"✖ {f}: {e}", err=True)

        if failures:
            sys.exit(1)
        return

    if not is_dxf(input_path):
        raise click.ClickException("INPUT_PATH must be a .dxf file (or use --batch).")

    outs = convert_one(input_path, out_pdf=out_pdf, units_override=units, write_report=report, out_svg=svg)
    click.echo("✔ " + ", ".join(str(p) for p in outs))