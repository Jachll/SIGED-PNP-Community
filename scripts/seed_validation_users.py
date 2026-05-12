import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import get_cursor  # noqa: E402
from app.security import hash_password  # noqa: E402


DEFAULT_PASSWORD = "Siged1234!"
VALIDATION_USERS = (
    ("admin.qa", "Administrador QA", "admin"),
    ("analista.qa", "Analista QA", "analista"),
    ("consulta.qa", "Consulta QA", "consulta"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crea o actualiza usuarios QA de validacion para admin, analista y consulta."
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Password explicito para los usuarios QA. Si no se envia, se busca en backend/.env.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=BACKEND_DIR / ".env",
        help="Ruta alternativa al archivo .env para leer SIGED_VALIDATION_PASSWORD.",
    )
    return parser.parse_args(argv)


def resolve_validation_password(
    *,
    explicit_password: str | None = None,
    env_file: Path | None = None,
) -> tuple[str, str]:
    if explicit_password and explicit_password.strip():
        return explicit_password.strip(), "cli"

    candidate_env_file = env_file or (BACKEND_DIR / ".env")
    if candidate_env_file.exists():
        for raw_line in candidate_env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "SIGED_VALIDATION_PASSWORD":
                return value.strip().strip('"') or DEFAULT_PASSWORD, "env"

    return DEFAULT_PASSWORD, "default"


def upsert_validation_user(username: str, nombre_completo: str, rol_codigo: str, password: str) -> str:
    password_hash = hash_password(password)

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id_usuario
            FROM auth_usuarios
            WHERE LOWER(username) = LOWER(%s)
            LIMIT 1;
            """,
            (username,),
        )
        existing_user = cur.fetchone()

        if existing_user:
            cur.execute(
                """
                UPDATE auth_usuarios
                SET
                    nombre_completo = %s,
                    rol_codigo = %s,
                    activo = TRUE,
                    password_hash = %s,
                    updated_at = NOW()
                WHERE id_usuario = %s;
                """,
                (nombre_completo, rol_codigo, password_hash, existing_user["id_usuario"]),
            )
            return "updated"

        cur.execute(
            """
            INSERT INTO auth_usuarios (
                username,
                nombre_completo,
                password_hash,
                rol_codigo,
                activo
            )
            VALUES (%s, %s, %s, %s, TRUE);
            """,
            (username, nombre_completo, password_hash, rol_codigo),
        )
        return "created"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    password, password_source = resolve_validation_password(
        explicit_password=args.password,
        env_file=args.env_file,
    )

    print(f"validation_password_source|{password_source}")

    for username, nombre_completo, rol_codigo in VALIDATION_USERS:
        status = upsert_validation_user(username, nombre_completo, rol_codigo, password)
        print(f"{status}|{username}|{rol_codigo}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
