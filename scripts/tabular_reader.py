from import_utils import bootstrap_backend_path

bootstrap_backend_path()

from app.etl.tabular import read_tabular_source

__all__ = ["read_tabular_source"]
