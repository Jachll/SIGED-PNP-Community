from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import close_connection_pool  # noqa: E402
from app.repositories.analisis_repository import (  # noqa: E402
    fetch_agregados_espaciales,
    fetch_hotspots,
    fetch_zonas_criticas,
)
from app.repositories.estadisticas_repository import fetch_estadisticas_por_dia  # noqa: E402
from app.repositories.eventos_repository import fetch_eventos, fetch_eventos_heatmap  # noqa: E402
from app.services.recomendaciones_service import generate_patrol_recommendations  # noqa: E402


@dataclass(frozen=True)
class BenchmarkResult:
    nombre: str
    iteraciones: int
    min_ms: float
    max_ms: float
    avg_ms: float
    median_ms: float
    p95_ms: float
    filas_muestra: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Baseline reproducible de rendimiento para consultas criticas SIGED-PNP."
    )
    parser.add_argument("--iterations", type=int, default=3, help="Numero de iteraciones por consulta.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Ruta del reporte JSON. Por defecto usa scripts/logs/.",
    )
    return parser.parse_args(argv)


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]

    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * quantile))
    return ordered[index]


def benchmark_case(name: str, callback, iterations: int) -> BenchmarkResult:
    durations: list[float] = []
    sample_rows = 0

    for _ in range(iterations):
        started_at = perf_counter()
        rows = callback()
        duration_ms = (perf_counter() - started_at) * 1000
        durations.append(duration_ms)
        sample_rows = len(rows)

    return BenchmarkResult(
        nombre=name,
        iteraciones=iterations,
        min_ms=round(min(durations), 2),
        max_ms=round(max(durations), 2),
        avg_ms=round(statistics.mean(durations), 2),
        median_ms=round(statistics.median(durations), 2),
        p95_ms=round(percentile(durations, 0.95), 2),
        filas_muestra=sample_rows,
    )


def build_default_output_path() -> Path:
    logs_dir = ROOT_DIR / "scripts" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return logs_dir / f"perf_baseline_{timestamp}.json"


def main() -> int:
    args = parse_args(sys.argv[1:])
    iterations = max(args.iterations, 1)

    cases = [
        (
            "eventos_listado",
            lambda: fetch_eventos(
                fecha_inicio=None,
                fecha_fin=None,
                id_delito=None,
                distrito=None,
                id_comisaria=None,
                region=None,
                division=None,
                comisaria=None,
                jurisdiccion=None,
                sector=None,
                limite=500,
                offset=0,
            ),
        ),
        (
            "eventos_heatmap",
            lambda: fetch_eventos_heatmap(
                fecha_inicio=None,
                fecha_fin=None,
                id_delito=None,
                distrito=None,
                id_comisaria=None,
                region=None,
                division=None,
                comisaria=None,
                jurisdiccion=None,
                sector=None,
                limite=1000,
            ),
        ),
        (
            "estadisticas_por_dia",
            lambda: fetch_estadisticas_por_dia(
                fecha_inicio=None,
                fecha_fin=None,
                id_delito=None,
                distrito=None,
                id_comisaria=None,
                region=None,
                division=None,
                comisaria=None,
                jurisdiccion=None,
                sector=None,
            ),
        ),
        (
            "analisis_agregados_espaciales",
            lambda: fetch_agregados_espaciales(
                fecha_inicio=None,
                fecha_fin=None,
                id_delito=None,
                distrito=None,
                id_comisaria=None,
                region=None,
                division=None,
                comisaria=None,
                jurisdiccion=None,
                sector=None,
                tamano_celda_metros=300,
                min_eventos=2,
                limite=100,
            ),
        ),
        (
            "analisis_zonas_criticas_distrito",
            lambda: fetch_zonas_criticas(
                fecha_inicio=None,
                fecha_fin=None,
                id_delito=None,
                distrito=None,
                id_comisaria=None,
                region=None,
                division=None,
                comisaria=None,
                jurisdiccion=None,
                sector=None,
                agrupado_por="distrito",
                min_eventos=3,
                limite=25,
            ),
        ),
        (
            "analisis_hotspots",
            lambda: fetch_hotspots(
                fecha_inicio=None,
                fecha_fin=None,
                id_delito=None,
                distrito=None,
                id_comisaria=None,
                region=None,
                division=None,
                comisaria=None,
                jurisdiccion=None,
                sector=None,
                estado="ACTIVO",
                limite=50,
            ),
        ),
        (
            "recomendaciones_patrullaje",
            lambda: generate_patrol_recommendations(
                fecha_inicio=None,
                fecha_fin=None,
                fecha_operativa=None,
                id_delito=None,
                distrito=None,
                id_comisaria=None,
                region=None,
                division=None,
                comisaria=None,
                jurisdiccion=None,
                sector=None,
                turno=None,
                limite=20,
                guardar=False,
            ).recomendaciones,
        ),
    ]

    output_path = args.output or build_default_output_path()
    results = [benchmark_case(name, callback, iterations) for name, callback in cases]

    payload = {
        "generated_at": datetime.now().isoformat(),
        "iterations": iterations,
        "results": [asdict(result) for result in results],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    for result in results:
        print(
            f"{result.nombre}: avg={result.avg_ms}ms median={result.median_ms}ms "
            f"p95={result.p95_ms}ms filas={result.filas_muestra}"
        )
    print(f"Reporte guardado en: {output_path}")

    close_connection_pool()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
