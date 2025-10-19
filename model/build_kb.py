"""Command line helper to build a Raptor knowledge base from a plain-text source."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

from .utils import build_raptor_tree

LOGGER = logging.getLogger(__name__)


def _load_chunks(source_path: Path) -> List[str]:
    """Split the knowledge source into non-empty chunks."""
    raw_text = source_path.read_text(encoding="utf-8")

    chunks: List[str] = []
    current_lines: List[str] = []

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current_lines:
                chunks.append(" ".join(current_lines))
                current_lines = []
            continue
        current_lines.append(stripped)

    if current_lines:
        chunks.append(" ".join(current_lines))

    if not chunks:
        raise ValueError(f"No usable content found in knowledge file: {source_path}")

    return chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Raptor KB pickle from knowledge text.")
    parser.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parent / "knowledge.txt"),
        help="Path to the knowledge text file.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "raptorkb.pickle"),
        help="Destination path for the generated pickle.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    source_path = Path(args.source).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    LOGGER.info("Building Raptor KB from %s -> %s", source_path, output_path)
    chunks = _load_chunks(source_path)
    build_raptor_tree(chunks, output_path)
    LOGGER.info("Raptor KB generated successfully at %s", output_path)


if __name__ == "__main__":
    main()
