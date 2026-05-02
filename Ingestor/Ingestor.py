"""Multi-format data ingestion to structured JSON.

Usage:
    python Ingestor.py --input "./data" --output "./ingested.json"
"""

from __future__ import annotations

import sys  
from typing import List, Optional

from ingestor_core.cli import CliApp
from ingestor_core.worker import run_worker_from_env


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    if "--worker" in argv:
        worker_argv = [arg for arg in argv if arg != "--worker"]
        return run_worker_from_env(worker_argv)
    return CliApp().run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
