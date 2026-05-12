import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "scripts"


def _load_script_module(module_name: str):
    module_path = SCRIPTS_DIR / f"{module_name}.py"
    qualified_name = f"tests.{module_name}"
    spec = spec_from_file_location(qualified_name, module_path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


def test_benchmark_parse_args_accepts_iterations_and_output(tmp_path):
    benchmark_backend = _load_script_module("benchmark_backend")

    output_path = tmp_path / "baseline.json"
    args = benchmark_backend.parse_args(["--iterations", "5", "--output", str(output_path)])

    assert args.iterations == 5
    assert args.output == output_path


def test_benchmark_case_summarizes_durations_and_sample_size():
    benchmark_backend = _load_script_module("benchmark_backend")

    result = benchmark_backend.benchmark_case("demo", lambda: [1, 2, 3], iterations=3)

    assert result.nombre == "demo"
    assert result.iteraciones == 3
    assert result.filas_muestra == 3
    assert result.min_ms <= result.median_ms <= result.max_ms
    assert result.avg_ms >= 0
    assert result.p95_ms >= result.median_ms


def test_cleanup_parse_args_supports_default_and_custom_marker():
    cleanup_validation_lotes = _load_script_module("cleanup_validation_lotes")

    default_args = cleanup_validation_lotes.parse_args([])
    custom_args = cleanup_validation_lotes.parse_args(["LOTE_QA_CUSTOM"])

    assert default_args.marker == cleanup_validation_lotes.DEFAULT_MARKER
    assert custom_args.marker == "LOTE_QA_CUSTOM"


def test_cleanup_safe_unlink_upload_only_deletes_inside_uploads(tmp_path, monkeypatch):
    cleanup_validation_lotes = _load_script_module("cleanup_validation_lotes")

    repo_root = tmp_path / "repo"
    uploads_dir = repo_root / "backend" / "uploads"
    uploads_dir.mkdir(parents=True)
    allowed_file = uploads_dir / "qa.csv"
    allowed_file.write_text("demo", encoding="utf-8")

    outside_file = repo_root / "externo.csv"
    outside_file.write_text("demo", encoding="utf-8")

    monkeypatch.setattr(cleanup_validation_lotes, "ROOT_DIR", repo_root)
    monkeypatch.setattr(cleanup_validation_lotes, "UPLOADS_DIR", uploads_dir.resolve())

    assert cleanup_validation_lotes.safe_unlink_upload(str(allowed_file)) is True
    assert allowed_file.exists() is False

    assert cleanup_validation_lotes.safe_unlink_upload(str(outside_file)) is False
    assert outside_file.exists() is True


def test_seed_parse_args_accepts_password_and_env_file(tmp_path):
    seed_validation_users = _load_script_module("seed_validation_users")

    env_file = tmp_path / ".env.qa"
    args = seed_validation_users.parse_args(["--password", "Temporal123!", "--env-file", str(env_file)])

    assert args.password == "Temporal123!"
    assert args.env_file == env_file


def test_seed_resolve_validation_password_prefers_cli_then_env_then_default(tmp_path):
    seed_validation_users = _load_script_module("seed_validation_users")

    env_file = tmp_path / ".env"
    env_file.write_text('SIGED_VALIDATION_PASSWORD="EnvSecret123!"\n', encoding="utf-8")

    cli_password, cli_source = seed_validation_users.resolve_validation_password(
        explicit_password="CliSecret123!",
        env_file=env_file,
    )
    env_password, env_source = seed_validation_users.resolve_validation_password(env_file=env_file)
    default_password, default_source = seed_validation_users.resolve_validation_password(env_file=tmp_path / "missing.env")

    assert (cli_password, cli_source) == ("CliSecret123!", "cli")
    assert (env_password, env_source) == ("EnvSecret123!", "env")
    assert (default_password, default_source) == (seed_validation_users.DEFAULT_PASSWORD, "default")


def test_seed_main_reports_status_for_all_validation_users(monkeypatch, capsys):
    seed_validation_users = _load_script_module("seed_validation_users")

    monkeypatch.setattr(
        seed_validation_users,
        "resolve_validation_password",
        lambda explicit_password=None, env_file=None: ("Secret123!", "cli"),
    )
    monkeypatch.setattr(
        seed_validation_users,
        "upsert_validation_user",
        lambda username, nombre_completo, rol_codigo, password: "updated",
    )

    exit_code = seed_validation_users.main(["--password", "Secret123!"])
    output_lines = capsys.readouterr().out.strip().splitlines()

    assert exit_code == 0
    assert output_lines[0] == "validation_password_source|cli"
    assert output_lines[1:] == [
        "updated|admin.qa|admin",
        "updated|analista.qa|analista",
        "updated|consulta.qa|consulta",
    ]
