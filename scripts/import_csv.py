from import_csv_lotes import import_csv_lote, parse_args
from import_utils import load_backend_env


def import_csv(args) -> None:
    print("Modo compatibilidad: usando el pipeline oficial por lotes con staging y trazabilidad.")
    import_csv_lote(args)


if __name__ == "__main__":
    load_backend_env()
    arguments = parse_args()
    import_csv(arguments)
