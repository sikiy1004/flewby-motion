"""設定の読み込み（config/*.yaml + 環境変数 / .env）。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

JST = timezone(timedelta(hours=9))


def project_root() -> Path:
    """autopilot/ ディレクトリ（AUTOPILOT_HOME で上書き可）。"""
    env = os.environ.get("AUTOPILOT_HOME")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[2]


def now_jst() -> datetime:
    override = os.environ.get("AUTOPILOT_NOW")  # テスト用: 2026-11-19T12:15
    if override:
        return datetime.fromisoformat(override).replace(tzinfo=JST)
    return datetime.now(JST)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class Settings:
    root: Path
    data: dict[str, Any]
    genres: list[dict[str, Any]]
    ng: dict[str, Any]
    calendar: list[dict[str, Any]]
    offers: list[dict[str, Any]]
    sample_mode: bool = False
    dry_run: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    # ---- paths ----
    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def data_dir(self) -> Path:
        p = Path(os.environ.get("AUTOPILOT_DATA_DIR", self.root / "data"))
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_dir(self) -> Path:
        p = Path(os.environ.get("AUTOPILOT_OUTPUT_DIR", self.root / "output"))
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        return Path(os.environ.get("AUTOPILOT_DB", self.data_dir / "autopilot.db"))

    @property
    def fonts_dir(self) -> Path:
        return self.root / "assets" / "fonts"

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    # ---- helpers ----
    def get(self, dotted: str, default: Any = None) -> Any:
        cur: Any = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def genre(self, key: str) -> dict[str, Any]:
        for g in self.genres:
            if g["key"] == key:
                return g
        raise KeyError(key)

    def platform_enabled(self, name: str) -> bool:
        env = os.environ.get(f"{name.upper()}_ENABLED")
        if env not in (None, ""):
            return env.strip().lower() in ("1", "true", "yes", "on")
        return bool(self.get(f"platforms.{name}", False))

    @staticmethod
    def env(name: str, default: str | None = None) -> str | None:
        v = os.environ.get(name)
        return v if v not in (None, "") else default


def load_settings(root: Path | None = None, *, sample_mode: bool = False, dry_run: bool = False) -> Settings:
    root = root or project_root()
    if load_dotenv is not None:
        load_dotenv(root / ".env", override=False)
    cfg = root / "config"
    return Settings(
        root=root,
        data=_load_yaml(cfg / "settings.yaml"),
        genres=_load_yaml(cfg / "genres.yaml").get("genres", []),
        ng=_load_yaml(cfg / "ng_words.yaml"),
        calendar=_load_yaml(cfg / "calendar.yaml").get("events", []),
        offers=_load_yaml(cfg / "offers.yaml").get("offers", []) or [],
        sample_mode=sample_mode,
        dry_run=dry_run or sample_mode or os.environ.get("AUTOPILOT_DRY_RUN", "").lower() in ("1", "true"),
    )
