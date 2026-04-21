"""Multi-format data ingestion to structured JSON.

Usage:
    python Ingestor.py --input "./data" --output "./ingested.json"
"""

from __future__ import annotations

from typing import List, Optional

from ingestor_core.cli import CliApp


def main(argv: Optional[List[str]] = None) -> int:
    return CliApp().run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
