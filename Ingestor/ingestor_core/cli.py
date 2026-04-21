import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .engine import IngestionEngine
from .models import IngestionOptions


class CliApp:
    @staticmethod
    def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Ingest files/folders into one structured JSON output"
        )
        parser.add_argument("--input", required=True, help="Input file or folder path")
        parser.add_argument(
            "--output",
            required=True,
            help="Output JSON file path",
        )
        parser.add_argument(
            "--pretty",
            action="store_true",
            default=False,
            help="Write pretty-formatted JSON (default: true)",
        )
        parser.add_argument(
            "--compact",
            action="store_true",
            help="Write compact JSON without indentation",
        )
        parser.add_argument(
            "--aggressive-pdf-cleanup",
            action="store_true",
            help="Enable stronger PDF table text cleanup (optional; may over-normalize in some files)",
        )

        args = parser.parse_args(argv)
        if args.pretty and args.compact:
            parser.error("Use either --pretty or --compact, not both.")
        return args

    def run(self, argv: Optional[List[str]] = None) -> int:
        args = self.parse_args(argv)
        input_path = Path(args.input).expanduser().resolve()
        output_path = Path(args.output).expanduser().resolve()

        if not input_path.exists():
            print(f"Input path does not exist: {input_path}", file=sys.stderr)
            return 1

        options = IngestionOptions(
            aggressive_pdf_cleanup=args.aggressive_pdf_cleanup,
        )
        engine = IngestionEngine(options)
        payload = engine.ingest_path(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            should_pretty = args.pretty or not args.compact
            if should_pretty:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            else:
                json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

        print(
            f"Ingestion complete. Files: {payload['summary']['total_files']}, "
            f"Success: {payload['summary']['success_count']}, "
            f"Errors: {payload['summary']['error_count']}"
        )
        print(f"Output written to: {output_path}")
        return 0
