import argparse
import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

from .engine import IngestionEngine
from .models import IngestionOptions


@dataclass
class WorkerConfig:
    redis_url: str
    input_queue: str
    processing_queue: str
    output_queue: str
    dlq_queue: str
    pop_timeout_seconds: int = 5
    max_retries: int = 3
    recover_inflight_on_start: bool = True


class IngestionQueueWorker:
    def __init__(
        self,
        redis_client: Any,
        engine: IngestionEngine,
        config: WorkerConfig,
    ) -> None:
        self.redis = redis_client
        self.engine = engine
        self.config = config

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    @staticmethod
    def _extract_payload(envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = envelope.get("payload")
        if isinstance(payload, dict):
            return payload
        return envelope

    @staticmethod
    def _safe_relative_path(raw_path: str) -> Path:
        rel = Path(raw_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Invalid file path in job payload: {raw_path}")
        return rel

    @classmethod
    def _write_job_file(cls, root: Path, file_item: Dict[str, Any]) -> Path:
        raw_path = str(file_item.get("path") or file_item.get("name") or "").strip()
        if not raw_path:
            raise ValueError("Each file entry must include 'path' or 'name'.")

        relative_path = cls._safe_relative_path(raw_path)
        target_path = (root / relative_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if "content_base64" in file_item:
            encoded = file_item.get("content_base64")
            if not isinstance(encoded, str):
                raise ValueError("'content_base64' must be a string.")
            try:
                data = base64.b64decode(encoded, validate=True)
            except Exception as exc:
                raise ValueError("Invalid base64 content in file payload.") from exc
            target_path.write_bytes(data)
            return target_path

        if "content" in file_item:
            text = file_item.get("content")
            if not isinstance(text, str):
                raise ValueError("'content' must be a string.")
            encoding = file_item.get("encoding", "utf-8")
            if not isinstance(encoding, str) or not encoding:
                raise ValueError("'encoding' must be a non-empty string when provided.")
            target_path.write_text(text, encoding=encoding)
            return target_path

        raise ValueError("Each file entry must include 'content' or 'content_base64'.")

    def _ingest_from_payload_files(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        files = payload.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("Job payload must include a non-empty 'files' list.")

        with TemporaryDirectory(prefix="ingestor-job-") as temp_dir:
            root = Path(temp_dir)
            for file_item in files:
                if not isinstance(file_item, dict):
                    raise ValueError("Each item in 'files' must be an object.")
                self._write_job_file(root, file_item)

            return self.engine.ingest_path(root)

    @classmethod
    def _build_success_envelope(
        cls,
        input_envelope: Dict[str, Any],
        payload: Dict[str, Any],
        ingestion_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "id": input_envelope.get("id"),
            "source": input_envelope.get("source", "ingestor_worker"),
            "type": "ingestion_result",
            "timestamp": cls._now_iso(),
            "status": "completed",
            "project_name": payload.get("project_name"),
            "summary": ingestion_payload.get("summary", {}),
            "ingestion": ingestion_payload,
            "attempt": int(input_envelope.get("_attempt", 0)),
        }

    def process_reserved_message(self, raw_message: str) -> Dict[str, Any]:
        try:
            envelope = json.loads(raw_message)
        except json.JSONDecodeError as exc:
            raise ValueError("Queue message is not valid JSON.") from exc

        if not isinstance(envelope, dict):
            raise ValueError("Queue message must decode into a JSON object.")

        payload = self._extract_payload(envelope)
        ingestion_payload = self._ingest_from_payload_files(payload)
        return self._build_success_envelope(envelope, payload, ingestion_payload)

    def _build_retry_or_dlq_message(self, raw_message: str, error: Exception) -> str:
        now_iso = self._now_iso()
        try:
            envelope = json.loads(raw_message)
            if not isinstance(envelope, dict):
                envelope = {"raw": raw_message}
        except json.JSONDecodeError:
            envelope = {"raw": raw_message}

        current_attempt = int(envelope.get("_attempt", 0))
        envelope["_attempt"] = current_attempt + 1
        envelope["_last_error"] = str(error)
        envelope["_last_failed_at"] = now_iso
        return json.dumps(envelope, ensure_ascii=False)

    def _handle_failure(self, raw_message: str, error: Exception) -> None:
        message = self._build_retry_or_dlq_message(raw_message, error)
        parsed = json.loads(message)
        attempt = int(parsed.get("_attempt", 0))

        if attempt <= self.config.max_retries:
            self.redis.lpush(self.config.input_queue, message)
            return

        self.redis.lpush(self.config.dlq_queue, message)

    def recover_processing_queue(self) -> int:
        moved = 0
        while True:
            item = self.redis.rpoplpush(self.config.processing_queue, self.config.input_queue)
            if item is None:
                break
            moved += 1
        return moved

    def run_once(self) -> bool:
        reserved = self.redis.brpoplpush(
            self.config.input_queue,
            self.config.processing_queue,
            timeout=self.config.pop_timeout_seconds,
        )
        if reserved is None:
            return False

        try:
            output = self.process_reserved_message(reserved)
            self.redis.lpush(self.config.output_queue, json.dumps(output, ensure_ascii=False))
        except Exception as exc:
            self._handle_failure(reserved, exc)
        finally:
            self.redis.lrem(self.config.processing_queue, 1, reserved)

        return True

    def run_forever(self, max_jobs: int = 0) -> int:
        if self.config.recover_inflight_on_start:
            self.recover_processing_queue()

        processed = 0
        while True:
            did_process = self.run_once()
            if did_process:
                processed += 1
            if max_jobs > 0 and processed >= max_jobs:
                return processed


def parse_worker_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Redis queue worker for Ingestor")
    parser.add_argument("--max-jobs", type=int, default=0, help="Process at most N jobs (0 means infinite)")
    parser.add_argument(
        "--aggressive-pdf-cleanup",
        action="store_true",
        help="Enable stronger PDF table text cleanup (same behavior as CLI mode)",
    )
    return parser.parse_args(argv)


def build_config_from_env() -> WorkerConfig:
    input_queue = os.environ.get("INGESTOR_INPUT_QUEUE") or os.environ.get("REDIS_QUEUE_NAME", "queue:ai_tasks")
    return WorkerConfig(
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        input_queue=input_queue,
        processing_queue=os.environ.get("INGESTOR_PROCESSING_QUEUE", f"{input_queue}:processing"),
        output_queue=os.environ.get("INGESTOR_OUTPUT_QUEUE", "queue:ingestor_results"),
        dlq_queue=os.environ.get("INGESTOR_DLQ_QUEUE", "queue:ingestor_dlq"),
        pop_timeout_seconds=int(os.environ.get("INGESTOR_POP_TIMEOUT", "5")),
        max_retries=int(os.environ.get("INGESTOR_MAX_RETRIES", "3")),
        recover_inflight_on_start=os.environ.get("INGESTOR_RECOVER_INFLIGHT", "true").lower() != "false",
    )


def create_redis_client(redis_url: str) -> Any:
    import redis

    return redis.from_url(redis_url, decode_responses=True)


def run_worker_from_env(argv: Optional[List[str]] = None) -> int:
    args = parse_worker_args(argv)
    config = build_config_from_env()

    options = IngestionOptions(aggressive_pdf_cleanup=args.aggressive_pdf_cleanup)
    worker = IngestionQueueWorker(
        redis_client=create_redis_client(config.redis_url),
        engine=IngestionEngine(options),
        config=config,
    )
    worker.run_forever(max_jobs=args.max_jobs)
    return 0