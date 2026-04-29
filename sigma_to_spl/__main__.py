import sys
from pathlib import Path

import click

from .config import load_config, default_config
from .converter import Converter, ConversionError
from .postprocess import format_savedsearches


@click.group()
def cli():
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=None)
@click.option("--format", "-f", "output_format", type=click.Choice(["spl", "savedsearches"]), default="spl")
def convert(path: Path, config: Path, output_dir: Path, output_format: str):
    """Convert a Sigma rule or directory of rules to SPL."""
    cfg = load_config(config) if config else default_config()
    converter = Converter(cfg)

    if path.is_file():
        _convert_single(path, converter, output_dir, output_format)
    elif path.is_dir():
        results = converter.convert_directory(path)
        errors = 0
        for name, spl in results.items():
            if spl.startswith("# ERROR"):
                click.echo(f"FAIL  {name}: {spl}", err=True)
                errors += 1
            else:
                _write_or_print(name, spl, output_dir, output_format)
                click.echo(f"OK    {name}")
        if errors:
            sys.exit(1)
    else:
        click.echo(f"Error: {path} is not a file or directory", err=True)
        sys.exit(1)


def _convert_single(path: Path, converter: Converter, output_dir: Path, output_format: str):
    try:
        spl = converter.convert_file(path)
    except ConversionError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    _write_or_print(path.name, spl, output_dir, output_format)


def _write_or_print(name: str, spl: str, output_dir: Path, output_format: str):
    if output_format == "savedsearches":
        title = Path(name).stem
        content = format_savedsearches(title, spl)
    else:
        content = spl

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / (Path(name).stem + (".conf" if output_format == "savedsearches" else ".spl"))
        out_path.write_text(content)
    else:
        click.echo(content)


if __name__ == "__main__":
    cli()
