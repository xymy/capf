import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Final

import click
from rich.color import ColorSystem
from rich.console import Console
from rich.markup import escape
from rich.style import Style
from rich.text import Text

CONTEXT_SETTINGS: Final = dict(
    help_option_names=["-h", "--help"], max_content_width=120
)


def hlp(path: Path) -> str:
    """Highlight path for rich output."""
    return f"[u]{escape(str(path))}[/u]"


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-b",
    "--builder",
    type=click.Choice(
        [
            "html",
            "dirhtml",
            "singlehtml",
            "htmlhelp",
            "qthelp",
            "devhelp",
            "epub",
            "applehelp",
            "latex",
            "man",
            "texinfo",
            "text",
        ]
    ),
    default="html",
    show_default=True,
    help="Select a builder.",
)
@click.option(
    "--clean/--no-clean",
    show_default=True,
    help="Whether or not to clean the build directory.",
)
@click.option(
    "--dist/--no-dist",
    show_default=True,
    help="Whether or not to build a distribution.",
)
@click.option(
    "--color",
    type=click.Choice(["yes", "no", "auto"]),
    default="auto",
    show_default=True,
    help="Whether or not to enable color output.",
)
def build_docs(*, builder: str, clean: bool, dist: bool, color: str) -> None:
    console = Console(soft_wrap=True, emoji=False, highlight=False)
    if not console.is_terminal:
        console.legacy_windows = False
    match color:
        case "yes" if console._color_system is None:
            console._color_system = ColorSystem.STANDARD
        case "no" if console._color_system is not None:
            console._color_system = None

    cyan = Style(color="cyan", bold=True)
    magenta = Style(color="magenta", bold=True)
    blue = Style(color="blue", bold=True)

    console.rule(Text("Information", cyan))

    root = Path(__file__).parents[1]
    docs_dir = root / "docs"
    source_dir = docs_dir / "source"
    build_dir = docs_dir / "build"
    output_dir = build_dir / builder
    doctrees_dir = build_dir / ".doctrees"

    console.print(f"Docs dir: {hlp(docs_dir)}", style=magenta)
    console.print(f"Source dir: {hlp(source_dir)}", style=magenta)
    console.print(f"Output dir: {hlp(output_dir)}", style=magenta)

    if clean and build_dir.exists():
        console.rule(Text("Cleaning", cyan))
        shutil.rmtree(build_dir)
        console.print(f"Clean the build directory {hlp(build_dir)}", style=blue)

    console.rule(Text("Building", cyan))

    cmd = [sys.executable, "-m", "sphinx.cmd.build"]
    match color:
        case "yes":
            cmd.append("--color")
        case "no":
            cmd.append("--no-color")
    subprocess.run(
        [*cmd, "-b", builder, "-d", doctrees_dir, source_dir, output_dir],
        cwd=root,
        check=True,
    )

    if dist:
        import importlib.metadata

        metadata = importlib.metadata.metadata("capf")

        console.rule(Text("Distribution", cyan))

        dist_dir = docs_dir / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        dist_name = f"{metadata['Name']}-{metadata['Version']}-docs-{builder}"
        dist_path = dist_dir / f"{dist_name}.tar.xz"

        with tarfile.open(dist_path, "w:xz") as tar:
            tar.add(output_dir, dist_name)

        green = Style(color="green", bold=True)
        console.print(f"Build a distribution at {hlp(dist_path)}", style=green)


def main() -> None:
    try:
        build_docs(windows_expand_args=False)
    except Exception:  # noqa: BLE001
        console = Console(stderr=True)
        console.print_exception(suppress=[click])
        sys.exit(1)


if __name__ == "__main__":
    main()
