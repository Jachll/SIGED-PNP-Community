import argparse
from pathlib import Path

from import_utils import (
    add_db_arguments,
    create_db_connection,
    load_backend_env,
    write_error_log,
)

from app.etl import import_tabular_file_to_lote, persist_local_input_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingesta oficial por lotes (CSV o Excel) con staging para SIGED-PNP")
    parser.add_argument(
        "--input",
        "--csv",
        dest="input_file",
        required=True,
        help="Ruta del archivo de entrada (.csv o .xlsx)",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        help="Nombre de la hoja Excel a usar. Si no se indica, se usa la primera hoja",
    )
    parser.add_argument("--observaciones", default="", help="Observaciones opcionales del lote")
    add_db_arguments(parser)
    return parser.parse_args()


def import_csv_lote(args: argparse.Namespace) -> None:
    input_path = Path(args.input_file)
    managed_path = persist_local_input_file(input_path)
    conn = create_db_connection(args, autocommit=False)

    try:
        result = import_tabular_file_to_lote(
            conn,
            managed_path=managed_path,
            original_filename=input_path.name,
            observaciones=args.observaciones,
            sheet_name=args.sheet,
        )
    finally:
        conn.close()

    log_path = write_error_log(result.errors, prefix=f"lote_{result.id_lote}_errores")

    print(f"Lote creado: {result.id_lote}")
    print(f"Archivo original: {input_path.name}")
    print(f"Archivo gestionado: {result.ruta_archivo}")
    print(f"Total filas leidas: {result.summary['total_filas']}")
    print(f"Filas validas: {result.summary['filas_validas']}")
    print(f"Filas con error: {result.summary['filas_error']}")
    print(f"Filas promovidas: {result.summary['filas_promovidas']}")
    print(f"Estado lote: {result.estado_lote}")
    if log_path:
        print(f"Log de errores: {log_path}")


if __name__ == "__main__":
    load_backend_env()
    arguments = parse_args()
    import_csv_lote(arguments)
