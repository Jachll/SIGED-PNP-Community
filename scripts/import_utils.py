import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"


def bootstrap_backend_path() -> Path:
    backend_path = str(BACKEND_DIR)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    return BACKEND_DIR


bootstrap_backend_path()


def load_backend_env() -> None:
    load_dotenv(BACKEND_DIR / ".env")


def add_db_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--db-host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.getenv("DB_PORT", "5432"))
    parser.add_argument("--db-name", default=os.getenv("DB_NAME", "siged_pnp"))
    parser.add_argument("--db-user", default=os.getenv("DB_USER", "postgres"))
    parser.add_argument("--db-password", default=os.getenv("DB_PASSWORD", ""))
    return parser


def create_db_connection(args: argparse.Namespace, autocommit: bool = False) -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        host=args.db_host,
        port=args.db_port,
        dbname=args.db_name,
        user=args.db_user,
        password=args.db_password,
    )
    conn.autocommit = autocommit
    return conn


def write_error_log(errors: list[dict], prefix: str = "import_errors") -> Path | None:
    if not errors:
        return None

    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"{prefix}_{timestamp}.csv"

    with log_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["linea", "codigo", "error", "data"])
        writer.writeheader()
        writer.writerows(errors)

    return log_path
