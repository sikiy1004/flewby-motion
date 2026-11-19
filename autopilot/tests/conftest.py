import os
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """毎テスト独立した DB / 出力先。外部 API キーは消しておく。"""
    monkeypatch.setenv("AUTOPILOT_HOME", str(ROOT))
    monkeypatch.setenv("AUTOPILOT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AUTOPILOT_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("AUTOPILOT_NOW", "2026-11-19T12:20")
    for k in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "OLLAMA_HOST", "PEXELS_API_KEY",
              "DISCORD_WEBHOOK_URL", "TIKTOK_ENABLED", "AUTOPILOT_DB"):
        monkeypatch.delenv(k, raising=False)
    return tmp_path


@pytest.fixture()
def settings(env):
    from autopilot.config import load_settings
    return load_settings(sample_mode=True)


@pytest.fixture()
def db(settings):
    from autopilot.db import DB
    d = DB(settings.db_path)
    yield d
    d.close()


def chromium_available() -> bool:
    if os.environ.get("CHROMIUM_EXECUTABLE"):
        return Path(os.environ["CHROMIUM_EXECUTABLE"]).exists()
    try:
        from autopilot.render import browser
        with browser():
            return True
    except Exception:
        return False


needs_chromium = pytest.mark.skipif(not chromium_available(), reason="Chromium がありません")
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg がありません")
