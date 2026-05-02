import base64
import json
import types
from pathlib import Path

import pytest

from ingestor_core.engine import IngestionEngine
from ingestor_core.models import IngestionOptions
from ingestor_core.worker import (
    IngestionQueueWorker,
    WorkerConfig,
    build_config_from_env,
    create_redis_client,
    parse_worker_args,
    run_worker_from_env,
)


class FakeRedis:
    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}

    def lpush(self, queue: str, value: str) -> int:
        self.lists.setdefault(queue, []).insert(0, value)
        return len(self.lists[queue])

    def brpoplpush(self, source: str, destination: str, timeout: int = 0):
        del timeout
        source_list = self.lists.setdefault(source, [])
        if not source_list:
            return None
        value = source_list.pop()
        self.lists.setdefault(destination, []).insert(0, value)
        return value

    def rpoplpush(self, source: str, destination: str):
        source_list = self.lists.setdefault(source, [])
        if not source_list:
            return None
        value = source_list.pop()
        self.lists.setdefault(destination, []).insert(0, value)
        return value

    def lrem(self, queue: str, count: int, value: str) -> int:
        items = self.lists.setdefault(queue, [])
        removed = 0
        rebuilt: list[str] = []
        for item in items:
            if removed < count and item == value:
                removed += 1
                continue
            rebuilt.append(item)
        self.lists[queue] = rebuilt
        return removed


def _config(max_retries: int = 2, recover: bool = False) -> WorkerConfig:
    return WorkerConfig(
        redis_url="redis://localhost:6379/0",
        input_queue="queue:in",
        processing_queue="queue:in:processing",
        output_queue="queue:out",
        dlq_queue="queue:dlq",
        pop_timeout_seconds=1,
        max_retries=max_retries,
        recover_inflight_on_start=recover,
    )


def test_worker_static_helpers_and_payload_extract() -> None:
    stamp = IngestionQueueWorker._now_iso()
    assert stamp.endswith("Z")

    wrapped = {"payload": {"a": 1}}
    assert IngestionQueueWorker._extract_payload(wrapped) == {"a": 1}
    assert IngestionQueueWorker._extract_payload({"x": 2}) == {"x": 2}

    rel = IngestionQueueWorker._safe_relative_path("folder/file.txt")
    assert rel == Path("folder/file.txt")

    with pytest.raises(ValueError):
        IngestionQueueWorker._safe_relative_path("../escape.txt")


def test_write_job_file_variants_and_errors(tmp_path: Path) -> None:
    text_path = IngestionQueueWorker._write_job_file(
        tmp_path,
        {"path": "a/b.txt", "content": "hello", "encoding": "utf-8"},
    )
    assert text_path.read_text(encoding="utf-8") == "hello"

    binary_payload = base64.b64encode(b"abc123").decode("ascii")
    bin_path = IngestionQueueWorker._write_job_file(
        tmp_path,
        {"name": "data.bin", "content_base64": binary_payload},
    )
    assert bin_path.read_bytes() == b"abc123"

    with pytest.raises(ValueError):
        IngestionQueueWorker._write_job_file(tmp_path, {})

    with pytest.raises(ValueError):
        IngestionQueueWorker._write_job_file(tmp_path, {"path": "a.txt", "content_base64": 1})

    with pytest.raises(ValueError):
        IngestionQueueWorker._write_job_file(tmp_path, {"path": "a.txt", "content_base64": "%%%"})

    with pytest.raises(ValueError):
        IngestionQueueWorker._write_job_file(tmp_path, {"path": "a.txt", "content": 1})

    with pytest.raises(ValueError):
        IngestionQueueWorker._write_job_file(tmp_path, {"path": "a.txt", "content": "x", "encoding": ""})

    with pytest.raises(ValueError):
        IngestionQueueWorker._write_job_file(tmp_path, {"path": "a.txt"})


def test_process_reserved_message_success_and_validation_errors() -> None:
    worker = IngestionQueueWorker(FakeRedis(), IngestionEngine(IngestionOptions()), _config())

    message = {
        "id": "job-1",
        "payload": {
            "project_name": "demo/repo",
            "files": [
                {"path": "src/main.py", "content": "print('ok')"},
            ],
        },
    }
    result = worker.process_reserved_message(json.dumps(message))
    assert result["id"] == "job-1"
    assert result["status"] == "completed"
    assert result["summary"]["total_files"] == 1
    assert result["project_name"] == "demo/repo"
    assert result["attempt"] == 0

    with pytest.raises(ValueError):
        worker.process_reserved_message("not-json")

    with pytest.raises(ValueError):
        worker.process_reserved_message(json.dumps(["bad"]))

    with pytest.raises(ValueError):
        worker.process_reserved_message(json.dumps({"payload": {"files": []}}))

    with pytest.raises(ValueError):
        worker.process_reserved_message(json.dumps({"payload": {"files": ["bad"]}}))


def test_retry_message_and_failure_routing() -> None:
    redis = FakeRedis()
    worker = IngestionQueueWorker(redis, IngestionEngine(IngestionOptions()), _config(max_retries=1))

    raw = json.dumps({"id": "job-2", "payload": {"files": [{"path": "a.txt", "content": "x"}]}})
    built = worker._build_retry_or_dlq_message(raw, ValueError("boom"))
    payload = json.loads(built)
    assert payload["_attempt"] == 1
    assert payload["_last_error"] == "boom"
    assert payload["_last_failed_at"].endswith("Z")

    non_dict_raw = json.dumps([1, 2])
    built_non_dict = worker._build_retry_or_dlq_message(non_dict_raw, ValueError("err"))
    parsed_non_dict = json.loads(built_non_dict)
    assert parsed_non_dict["raw"] == non_dict_raw

    bad_json_raw = "{"
    built_bad_json = worker._build_retry_or_dlq_message(bad_json_raw, ValueError("err2"))
    parsed_bad_json = json.loads(built_bad_json)
    assert parsed_bad_json["raw"] == bad_json_raw

    worker._handle_failure(raw, ValueError("retryable"))
    assert len(redis.lists["queue:in"]) == 1

    retry_msg = json.loads(redis.lists["queue:in"][0])
    retry_msg["_attempt"] = 1
    worker._handle_failure(json.dumps(retry_msg), ValueError("final"))
    assert len(redis.lists["queue:dlq"]) == 1


def test_recover_processing_and_run_once_paths() -> None:
    redis = FakeRedis()
    worker = IngestionQueueWorker(redis, IngestionEngine(IngestionOptions()), _config(max_retries=0))

    redis.lpush("queue:in:processing", "stale-1")
    redis.lpush("queue:in:processing", "stale-2")
    moved = worker.recover_processing_queue()
    assert moved == 2
    assert len(redis.lists["queue:in"]) == 2

    assert worker.run_once() is True
    assert worker.run_once() is True
    assert len(redis.lists["queue:dlq"]) == 2
    assert redis.lists["queue:in:processing"] == []

    valid = {
        "id": "job-3",
        "source": "ws1",
        "_attempt": "2",
        "payload": {"project_name": "p", "files": [{"path": "ok.txt", "content": "ok"}]},
    }
    redis.lpush("queue:in", json.dumps(valid))
    assert worker.run_once() is True
    out_message = json.loads(redis.lists["queue:out"][0])
    assert out_message["source"] == "ws1"
    assert out_message["attempt"] == 2

    assert worker.run_once() is False


def test_run_forever_with_max_jobs() -> None:
    redis = FakeRedis()
    worker = IngestionQueueWorker(redis, IngestionEngine(IngestionOptions()), _config(recover=True))

    redis.lpush("queue:in:processing", "stale")
    redis.lpush(
        "queue:in",
        json.dumps({"id": "job", "payload": {"files": [{"path": "x.txt", "content": "x"}]}}),
    )
    processed = worker.run_forever(max_jobs=1)
    assert processed == 1
    assert len(redis.lists["queue:out"]) == 1


def test_parse_args_build_config_and_redis_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    args = parse_worker_args(["--max-jobs", "5", "--aggressive-pdf-cleanup"])
    assert args.max_jobs == 5
    assert args.aggressive_pdf_cleanup is True

    monkeypatch.setenv("REDIS_URL", "redis://broker:6379/1")
    monkeypatch.setenv("REDIS_QUEUE_NAME", "queue:base")
    monkeypatch.setenv("INGESTOR_INPUT_QUEUE", "queue:custom")
    monkeypatch.setenv("INGESTOR_PROCESSING_QUEUE", "queue:proc")
    monkeypatch.setenv("INGESTOR_OUTPUT_QUEUE", "queue:out2")
    monkeypatch.setenv("INGESTOR_DLQ_QUEUE", "queue:dlq2")
    monkeypatch.setenv("INGESTOR_POP_TIMEOUT", "9")
    monkeypatch.setenv("INGESTOR_MAX_RETRIES", "7")
    monkeypatch.setenv("INGESTOR_RECOVER_INFLIGHT", "false")
    config = build_config_from_env()
    assert config.redis_url == "redis://broker:6379/1"
    assert config.input_queue == "queue:custom"
    assert config.processing_queue == "queue:proc"
    assert config.output_queue == "queue:out2"
    assert config.dlq_queue == "queue:dlq2"
    assert config.pop_timeout_seconds == 9
    assert config.max_retries == 7
    assert config.recover_inflight_on_start is False

    fake_module = types.SimpleNamespace(
        from_url=lambda url, decode_responses: {
            "url": url,
            "decode_responses": decode_responses,
        }
    )
    monkeypatch.setitem(__import__("sys").modules, "redis", fake_module)
    client = create_redis_client("redis://x:6379/0")
    assert client["url"] == "redis://x:6379/0"
    assert client["decode_responses"] is True


def test_run_worker_from_env_invokes_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeWorker:
        def __init__(self, redis_client, engine, config):
            self.redis_client = redis_client
            self.engine = engine
            self.config = config
            self.called_max_jobs = None

        def run_forever(self, max_jobs: int = 0):
            self.called_max_jobs = max_jobs
            return 0

    created: dict[str, object] = {}

    def _fake_parse(argv=None):
        del argv
        return types.SimpleNamespace(max_jobs=3, aggressive_pdf_cleanup=True)

    def _fake_build_config():
        return _config()

    def _fake_create_client(redis_url: str):
        return {"redis_url": redis_url}

    def _fake_worker(redis_client, engine, config):
        instance = FakeWorker(redis_client, engine, config)
        created["worker"] = instance
        return instance

    monkeypatch.setattr("ingestor_core.worker.parse_worker_args", _fake_parse)
    monkeypatch.setattr("ingestor_core.worker.build_config_from_env", _fake_build_config)
    monkeypatch.setattr("ingestor_core.worker.create_redis_client", _fake_create_client)
    monkeypatch.setattr("ingestor_core.worker.IngestionQueueWorker", _fake_worker)

    rc = run_worker_from_env(["--max-jobs", "3"])
    assert rc == 0
    worker = created["worker"]
    assert isinstance(worker, FakeWorker)
    assert worker.called_max_jobs == 3
    assert isinstance(worker.engine.options, IngestionOptions)
    assert worker.engine.options.aggressive_pdf_cleanup is True