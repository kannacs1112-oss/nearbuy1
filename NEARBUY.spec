# PyInstaller one-folder build. Build this spec on Windows.
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from pathlib import Path
root = Path(SPECPATH)
datas = [(str(root / "templates"), "templates"), (str(root / "static"), "static"), (str(root / "locales"), "locales")]
# tzdata supplies the IANA time zone database that zoneinfo needs on Windows.
datas += collect_data_files("tzdata")
hidden = collect_submodules("flask_sqlalchemy") + collect_submodules("sqlalchemy") + ["tzdata"]
a = Analysis([str(root / "app.py")], pathex=[str(root)], binaries=[], datas=datas, hiddenimports=hidden, hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="NEARBUY", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name="NEARBUY")
