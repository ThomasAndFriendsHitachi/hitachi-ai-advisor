import json
import runpy
from pathlib import Path

import pytest

import Ingestor
from ingestor_core import CliApp, FileIngestionResult, IngestionOptions
from ingestor_core.cli import CliApp as RealCliApp
from ingestor_core.engine import IngestionEngine
from ingestor_core.engine.extractor_registry import ExtractorRegistry
from ingestor_core.models import FileIngestionResult as FIR


def test_model_to_dict_and_init_exports() -> None:
    res = FIR(
        file_path="a",
        relative_path="a",
        extension=".txt",
        size_bytes=1,
        status="success",
        content_type="text",
        content="x",
        sections={"S": "v"},
        tables=[{"x": 1}],
        metadata={"m": 1},
        error="e",
        structured_sections={"S": {"k": "v"}},
    )
    data = res.to_dict()
    assert data["sections"]["S"] == "v"
    assert data["tables"][0]["x"] == 1
    assert data["error"] == "e"
    assert CliApp is not None and FileIngestionResult is not None and IngestionOptions is not None


def test_registry_resolve_known_text_unknown() -> None:
    reg = ExtractorRegistry()
    extractor, unknown = reg.resolve(Path("a.pdf"))
    assert unknown is False
    extractor2, unknown2 = reg.resolve(Path("a.txt"))
    assert unknown2 is False and extractor2 is reg.text_extractor
    extractor3, unknown3 = reg.resolve(Path("a.bin"))
    assert unknown3 is True and extractor3 is reg.text_extractor


def test_engine_default_options_init() -> None:
    engine = IngestionEngine()
    assert isinstance(engine.options, IngestionOptions)


def test_ingestor_main_function(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingestor_core.cli.CliApp.run", lambda self, argv=None: 7)
    assert Ingestor.main(["--input", "x", "--output", "y"]) == 7


def test_entrypoint_dunder_main_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingestor_core.cli.CliApp.run", lambda self, argv=None: 0)
    with pytest.raises(SystemExit) as ex1:
        runpy.run_path("Ingestor.py", run_name="__main__")
    assert ex1.value.code == 0


def test_engine_helpers_and_ingest_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "data"
    base.mkdir()
    f1 = base / "a.txt"
    f2 = base / "b.bin"
    f1.write_text("x", encoding="utf-8")
    f2.write_text("y", encoding="utf-8")

    files_from_dir = IngestionEngine.gather_files(base)
    assert len(files_from_dir) == 2
    files_from_file = IngestionEngine.gather_files(f1)
    assert files_from_file == [f1]

    metadata = {}
    structured = IngestionEngine._enrich_with_structured_sections(
        {"S": "Alpha: alpha beta gamma delta\nBeta: beta gamma delta epsilon zeta"},
        metadata,
    )
    assert structured is not None
    assert metadata["structured_section_count"] == 1

    r = IngestionEngine._make_result(
        file_path=f1,
        relative_path="a.txt",
        extension=".txt",
        size_bytes=1,
        status="success",
        content_type="text",
        content="x",
        sections={"S": "Alpha: alpha beta gamma delta\nBeta: beta gamma delta epsilon zeta"},
        tables=None,
        metadata={},
        with_structured_sections=True,
    )
    assert r.structured_sections is not None

    class FakeExtractor:
        def __init__(self, fail=False, as_text=True):
            self.fail = fail
            self.as_text = as_text

        def extract(self, file_path: Path, options: IngestionOptions):
            if self.fail:
                raise ValueError("bad")
            if self.as_text:
                return "text", "hello", {"S": "Alpha: alpha beta gamma delta\nBeta: beta gamma delta epsilon zeta"}, None, {}
            return "json", {"a": 1}, None, None, {}

    engine = IngestionEngine(IngestionOptions())
    monkeypatch.setattr(engine.registry, "resolve", lambda _p: (FakeExtractor(), True))
    success = engine.ingest_file(f2, base)
    assert success.status == "success"
    assert success.metadata["fallback"] == "unknown_extension_as_text"

    monkeypatch.setattr(engine.registry, "resolve", lambda _p: (FakeExtractor(fail=True), False))
    failed = engine.ingest_file(f2, base)
    assert failed.status == "error"

    seq = [
        FIR("a", "a", ".txt", 1, "success", "text", "x", None, None, {}),
        FIR("b", "b", ".txt", 1, "error", "unknown", None, None, None, {}, "e"),
    ]
    monkeypatch.setattr(IngestionEngine, "gather_files", staticmethod(lambda _path: [f1, f2]))
    monkeypatch.setattr(engine, "ingest_file", lambda p, r: seq.pop(0))
    payload = engine.ingest_path(base)
    assert payload["summary"] == {"total_files": 2, "success_count": 1, "error_count": 1}


def test_cli_parse_and_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        RealCliApp.parse_args(["--input", "x", "--output", "y", "--pretty", "--compact"])

    rc = RealCliApp().run(["--input", "missing.file", "--output", str(tmp_path / "o.json")])
    assert rc == 1

    input_file = tmp_path / "input.txt"
    input_file.write_text("x", encoding="utf-8")

    class FakeEngine:
        def __init__(self, options: IngestionOptions):
            self.options = options

        def ingest_path(self, input_path: Path):
            return {
                "source": str(input_path),
                "generated_at": "now",
                "summary": {"total_files": 1, "success_count": 1, "error_count": 0},
                "files": [],
            }

    monkeypatch.setattr("ingestor_core.cli.IngestionEngine", FakeEngine)

    out_pretty = tmp_path / "pretty.json"
    rc2 = RealCliApp().run(["--input", str(input_file), "--output", str(out_pretty), "--pretty"])
    assert rc2 == 0
    assert "\n  \"summary\"" in out_pretty.read_text(encoding="utf-8")

    out_compact = tmp_path / "compact.json"
    rc3 = RealCliApp().run(["--input", str(input_file), "--output", str(out_compact), "--compact"])
    assert rc3 == 0
    txt = out_compact.read_text(encoding="utf-8")
    assert "\n" not in txt
    parsed = json.loads(txt)
    assert parsed["summary"]["total_files"] == 1

    output = capsys.readouterr()
    assert "Ingestion complete." in output.out
