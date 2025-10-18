from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def _ensure_docling_on_path() -> None:
    """Ensure local docling package (docling-main) is importable.

    Looks for `docling-main/docling` next to this file and prepends its parent
    folder to `sys.path` so that `import docling` works without installing.
    """

    here = Path(__file__).resolve().parent
    candidate = here / "docling-main" / "docling"
    if candidate.exists():
        pkg_root = str((here / "docling-main").resolve())
        if pkg_root not in sys.path:
            sys.path.insert(0, pkg_root)


def convert_with_docling(
    input_path: str | os.PathLike,
    output_path: Optional[str | os.PathLike] = None,
    *,
    as_markdown: bool = False,
) -> str:
    """Convert a document/audio with Docling and save text transcription.

    Args:
        input_path: Path to the source file (PDF/DOCX/IMG/MP3/WAV/VTT/etc.).
        output_path: Optional path to save the extracted text. If not provided,
            will be created next to the input with `.txt` (or `.md` if
            `as_markdown=True`).
        as_markdown: If True, exports Markdown. Otherwise tries plain text; if
            plain text export is unavailable, falls back to Markdown content in
            a `.txt` file.

    Returns:
        The path to the written text file as a string.

    Raises:
        FileNotFoundError: If `input_path` does not exist.
        RuntimeError: If Docling conversion fails.
    """

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    _ensure_docling_on_path()

    # Import after modifying sys.path to prefer the vendored copy.
    try:
        from docling.document_converter import DocumentConverter
    except Exception as e:  # pragma: no cover - import-time failure
        raise RuntimeError(
            "Failed to import docling. Ensure docling-main is present or the package is installed."
        ) from e

    try:
        converter = DocumentConverter()
        result = converter.convert(str(src))
    except Exception as e:
        raise RuntimeError(f"Docling conversion failed for {src}: {e}") from e

    # Prefer plain text when requested and available; else use Markdown.
    doc = getattr(result, "document", None)
    if doc is None:
        raise RuntimeError("Docling returned no document in the result.")

    content: str
    if as_markdown:
        # Always available according to Docling README
        content = doc.export_to_markdown()
        default_suffix = ".md"
    else:
        export_txt = getattr(doc, "export_to_text", None)
        if callable(export_txt):
            content = export_txt()
            default_suffix = ".txt"
        else:
            # Fallback: write Markdown as .txt when plain text export isn't available
            content = doc.export_to_markdown()
            default_suffix = ".txt"

    if output_path is None:
        out = src.with_suffix(default_suffix)
    else:
        out = Path(output_path)
        if out.is_dir():
            out = out / (src.stem + (".md" if as_markdown else ".txt"))

    out.parent.mkdir(parents=True, exist_ok=True)
    # Write UTF-8 to support multilingual content.
    out.write_text(content, encoding="utf-8")

    return str(out)


if __name__ == "__main__":
    # Minimal CLI for quick manual use:
    #   python ulitsDocling.py path/to/file.pdf [--md] [--out path]
    import argparse

    parser = argparse.ArgumentParser(description="Run Docling and save transcription.")
    parser.add_argument("input", help="Path to input file")
    parser.add_argument("--out", dest="out", default=None, help="Output file or directory")
    parser.add_argument("--md", dest="as_md", action="store_true", help="Export Markdown instead of plain text")
    args = parser.parse_args()

    out_path = convert_with_docling(args.input, args.out, as_markdown=args.as_md)
    print(out_path)
