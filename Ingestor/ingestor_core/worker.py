import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import boto3

from .engine import IngestionEngine
from .models import IngestionOptions


@dataclass
class WorkerConfig:
    redis_url: str
    input_queue: str
    processing_queue: str
    output_queue: str
    dlq_queue: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
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

        # Initialize S3 Client to download files from MinIO
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.config.minio_endpoint,
            aws_access_key_id=self.config.minio_access_key,
            aws_secret_access_key=self.config.minio_secret_key,
            region_name='us-east-1' # Default for MinIO/S3 compatibility
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    @staticmethod
    def _safe_relative_path(raw_path: str) -> Path:
        rel = Path(raw_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"Invalid file path in job payload: {raw_path}")
        return rel

    def _build_final_envelope(self, job_id: str, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assembles the final output payload once all files for a commit are ingested.
        This ensures the output matches the exact schema defined in the Ingestor README.
        """
        # Fetch initial commit metadata saved by the webhook manager
        metadata_raw = self.redis.get(f"job:{job_id}:metadata")
        metadata = json.loads(metadata_raw) if metadata_raw else {}

        # Fetch all partially ingested files parked in Redis Hash
        parsed_files_raw = self.redis.hgetall(f"job:{job_id}:parsed_files")
        
        all_files = []
        for file_list_json in parsed_files_raw.values():
            all_files.extend(json.loads(file_list_json))

        # Recalculate summary metrics for the final payload
        success_count = sum(1 for f in all_files if f.get("status") == "success")
        error_count = sum(1 for f in all_files if f.get("status") == "error")

        ingestion_payload = {
            "source": "github_webhook",
            "generated_at": self._now_iso(),
            "summary": {
                "total_files": len(all_files),
                "success_count": success_count,
                "error_count": error_count
            },
            "files": all_files
        }

        # Clean up temporary state keys from Redis
        self.redis.delete(f"job:{job_id}:pending")
        self.redis.delete(f"job:{job_id}:metadata")
        self.redis.delete(f"job:{job_id}:parsed_files")

        return {
            "id": job_id,
            "source": ticket.get("source", "github_webhook"),
            "type": "ingestion_result",
            "timestamp": self._now_iso(),
            "status": "completed",
            "project_name": metadata.get("project", "Unknown"),
            "summary": ingestion_payload["summary"],
            "ingestion": ingestion_payload,
            "attempt": int(ticket.get("_attempt", 0)),
        }

    def process_reserved_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        """
        Processes a single file from the queue.
        Returns the final aggregated envelope ONLY if it's the last file for the job.
        Otherwise, returns None to indicate partial completion.
        """
        try:
            ticket = json.loads(raw_message)
        except json.JSONDecodeError as exc:
            raise ValueError("Queue message is not valid JSON.") from exc

        job_id = ticket.get("job_id")
        s3_uri = ticket.get("s3_uri")
        original_path = ticket.get("original_github_path")

        if not all([job_id, s3_uri, original_path]):
            raise ValueError("Ticket is missing required fields (job_id, s3_uri, original_github_path).")

        print(f"[*] Processing file: {original_path} (Job: {job_id})")

        with TemporaryDirectory(prefix="ingestor-job-") as temp_dir:
            root = Path(temp_dir)
            
            # Preserve original folder structure for the engine
            target_path = (root / self._safe_relative_path(original_path)).resolve()
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 1. Download file from MinIO
            parsed_uri = urlparse(s3_uri)
            bucket = parsed_uri.netloc
            key = parsed_uri.path.lstrip('/')
            self.s3.download_file(bucket, key, str(target_path))

            # 2. Run your original Ingestion Engine on the downloaded file
            ingestion_result = self.engine.ingest_path(root)

        # 3. Save the ingested file data into Redis Hash
        files_array = ingestion_result.get("files", [])
        self.redis.hset(f"job:{job_id}:parsed_files", original_path, json.dumps(files_array))

        # 4. Atomic Decrement: Check if this is the last file for the commit
        pending_left = self.redis.decr(f"job:{job_id}:pending")
        
        if pending_left == 0:
            print(f">>> [Job {job_id}] All files ingested! Generating final aggregated payload... <<<")
            return self._build_final_envelope(job_id, ticket)
            
        print(f"[Job {job_id}] File processed. Waiting for {pending_left} more files...")
        return None

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
            # Push to output_queue ONLY if the entire job is finished (output is not None)
            if output is not None:
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
        minio_endpoint=os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        minio_access_key=os.environ.get("MINIO_ROOT_USER", "admin"),
        minio_secret_key=os.environ.get("MINIO_ROOT_PASSWORD", "SuperSecretMinio123!"),
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
    print(f"[*] Ingestor Worker started. Listening on {config.input_queue}")
    worker.run_forever(max_jobs=args.max_jobs)
    return 0