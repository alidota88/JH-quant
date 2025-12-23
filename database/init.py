# database/__init__.py
from .engine import init_db, engine
from .manager import save_data, get_data, check_data_count
