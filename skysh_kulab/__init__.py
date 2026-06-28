from pathlib import Path

_src_package = Path(__file__).resolve().parents[1] / "src" / "skysh_kulab"
if _src_package.exists():
    __path__.append(str(_src_package))

