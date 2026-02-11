from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    data_dir: Path
    db_path: Path
    exports_dir: Path
    backups_dir: Path


def get_config() -> AppConfig:
    # This file lives at: <repo>/supplements/app/config.py
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    exports_dir = data_dir / "exports"
    backups_dir = data_dir / "backups"
    db_path = data_dir / "supplements.db"

    exports_dir.mkdir(parents=True, exist_ok=True)
    backups_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        project_root=project_root,
        data_dir=data_dir,
        db_path=db_path,
        exports_dir=exports_dir,
        backups_dir=backups_dir,
    )
