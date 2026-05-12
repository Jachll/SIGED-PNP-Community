import re

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")


def normalize_territory_name(value: str | None) -> str:
    if value is None:
        return ""

    collapsed = _WHITESPACE_RE.sub(" ", value.strip())
    return collapsed.upper()


def build_territory_code(prefix: str, value: str | None, fallback: str = "SIN_DATO") -> str:
    normalized = normalize_territory_name(value) or fallback
    slug = _NON_ALNUM_RE.sub("_", normalized).strip("_") or fallback
    return f"{prefix}-{slug}"
