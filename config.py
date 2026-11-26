import os, sys, shutil
from pathlib import Path

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_NAME = "NEARBUY"
if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / APP_NAME
else:
    DATA_DIR = Path(os.getenv("NEARBUY_DATA_DIR", Path(__file__).resolve().parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
# Preserve the original prototype database when moving to the new data location.
_new_db = DATA_DIR / "nearbuy.db"
_old_db = Path(__file__).resolve().parent / "nearbuy.db"
if not _new_db.exists() and _old_db.exists() and _old_db.resolve() != _new_db.resolve():
    shutil.copy2(_old_db, _new_db)

def _load_or_create_secret():
    path = DATA_DIR / ".secret_key"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    import secrets
    value = secrets.token_urlsafe(48)
    path.write_text(value, encoding="utf-8")
    try: path.chmod(0o600)
    except OSError: pass
    return value

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or _load_or_create_secret()
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'nearbuy.db').as_posix()}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 12
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
