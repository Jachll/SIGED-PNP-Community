import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
UPLOADS_DIR = (BACKEND_DIR / "uploads").resolve()
sys.path.insert(0, str(BACKEND_DIR))

from app.database import get_cursor  # noqa: E402


DEFAULT_MARKER = "SIGED_E2E_SMOKE_QA"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Limpia lotes de validacion identificados por un marcador funcional y "
            "elimina staging/eventos asociados."
        )
    )
    parser.add_argument(
        "marker",
        nargs="?",
        default=DEFAULT_MARKER,
        help="Marcador exacto usado en lotes_carga.observaciones.",
    )
    return parser.parse_args(argv)


def safe_unlink_upload(ruta_archivo: str | None) -> bool:
    if not ruta_archivo:
        return False

    candidate = Path(ruta_archivo)
    if not candidate.is_absolute():
        candidate = (ROOT_DIR / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(UPLOADS_DIR)
    except ValueError:
        return False

    if not candidate.exists() or not candidate.is_file():
        return False

    candidate.unlink()
    return True


def cleanup_lotes(marker: str) -> dict[str, int]:
    deleted_uploads = 0

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                id_lote,
                ruta_archivo
            FROM lotes_carga
            WHERE observaciones = %s
            ORDER BY id_lote;
            """,
            (marker,),
        )
        lotes = cur.fetchall()

        if not lotes:
            return {
                "deleted_lotes": 0,
                "deleted_staging_rows": 0,
                "deleted_eventos": 0,
                "deleted_uploads": 0,
            }

        lotes_ids = [int(item["id_lote"]) for item in lotes]

        for lote in lotes:
            if safe_unlink_upload(lote.get("ruta_archivo")):
                deleted_uploads += 1

        cur.execute(
            """
            DELETE FROM eventos_delictivos
            WHERE id_lote_carga = ANY(%s)
               OR id_evento IN (
                SELECT DISTINCT id_evento_final
                FROM staging_eventos
                WHERE id_lote = ANY(%s)
                  AND id_evento_final IS NOT NULL
            );
            """,
            (lotes_ids, lotes_ids),
        )
        deleted_eventos = cur.rowcount

        cur.execute(
            """
            DELETE FROM staging_eventos
            WHERE id_lote = ANY(%s);
            """,
            (lotes_ids,),
        )
        deleted_staging_rows = cur.rowcount

        cur.execute(
            """
            DELETE FROM lotes_carga
            WHERE id_lote = ANY(%s);
            """,
            (lotes_ids,),
        )
        deleted_lotes = cur.rowcount

    return {
        "deleted_lotes": deleted_lotes,
        "deleted_staging_rows": deleted_staging_rows,
        "deleted_eventos": deleted_eventos,
        "deleted_uploads": deleted_uploads,
    }


def main() -> int:
    args = parse_args(sys.argv[1:])

    summary = cleanup_lotes(args.marker)
    print(f"marker|{args.marker}")
    print(f"deleted_lotes|{summary['deleted_lotes']}")
    print(f"deleted_staging_rows|{summary['deleted_staging_rows']}")
    print(f"deleted_eventos|{summary['deleted_eventos']}")
    print(f"deleted_uploads|{summary['deleted_uploads']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
