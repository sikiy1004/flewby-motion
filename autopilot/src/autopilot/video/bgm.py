"""BGM の選曲（assets/bgm/bgm.yaml）。

- 投稿の形式に合う雰囲気（mood）の曲から、直近 3 本で使っていない曲を選ぶ。
- 成績（保存・シェア率）を曲ごとに学習し、伸びる曲が選ばれやすくなる（planner の Thompson Sampling を共用）。
- `start` で曲のいちばん盛り上がる位置から使い始める。
- クレジット表記が必要な曲は、キャプションに自動で表記する。
- 1 曲も無ければ、自動生成のビートを使う。
"""
from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path
from typing import Any

import yaml

from ..config import Settings
from ..db import DB

MOOD_BY_FORMAT = {"ranking": ["upbeat", "cute"], "price_band": ["upbeat", "cute"],
                  "spotlight": ["cute", "upbeat", "chill"], "guide": ["chill", "cute"]}
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".ogg")


def load_tracks(settings: Settings) -> list[dict[str, Any]]:
    root = settings.assets_dir / "bgm"
    meta = root / "bgm.yaml"
    tracks: list[dict[str, Any]] = []
    listed: set[str] = set()
    if meta.exists():
        for t in (yaml.safe_load(meta.read_text(encoding="utf-8")) or {}).get("tracks", []) or []:
            p = root / t["file"]
            if p.exists():
                tracks.append({"mood": "upbeat", "start": 0, "credit": None, **t, "path": p})
                listed.add(str(p.resolve()))
    for p in sorted(root.rglob("*")):  # yaml に書き忘れた曲も、クレジット不要扱いで使う
        if p.suffix.lower() in AUDIO_EXT and str(p.resolve()) not in listed:
            mood = p.parent.name if p.parent != root else "upbeat"
            tracks.append({"file": str(p.relative_to(root)), "title": p.stem, "mood": mood, "start": 0, "credit": None, "path": p})
    return tracks


def choose_track(settings: Settings, fmt: str, rng: random.Random) -> dict[str, Any] | None:
    tracks = load_tracks(settings)
    if not tracks:
        return None
    moods = MOOD_BY_FORMAT.get(fmt, ["upbeat"])
    pool = [t for t in tracks if t.get("mood") in moods] or tracks
    db = DB(settings.db_path)
    try:
        recent = json.loads(db.kv_get("bgm_recent", "[]") or "[]")
        fresh = [t for t in pool if t["file"] not in recent[-3:]] or pool
        best, best_v = fresh[0], -1.0
        for t in fresh:
            row = db.one("SELECT alpha, beta FROM arm_stats WHERE arm_key=?", (f"bgm:{t['file']}",))
            a, b = (row["alpha"], row["beta"]) if row else (1.0, 1.0)
            v = rng.betavariate(a, b)
            if v > best_v:
                best, best_v = t, v
        db.kv_set("bgm_recent", json.dumps((recent + [best["file"]])[-10:]))
        return best
    finally:
        db.close()


def prepare(track: dict[str, Any], out: Path, seconds: float) -> Path:
    """曲の start 位置から必要な長さだけ切り出し、頭と終わりを軽くフェード。"""
    start = float(track.get("start") or 0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", str(track["path"]),
                    "-t", f"{seconds + 1:.2f}", "-af", f"afade=t=in:d=0.25,afade=t=out:st={max(0, seconds - 0.8):.2f}:d=1.6",
                    "-ac", "2", "-ar", "44100", str(out)], check=True, capture_output=True)
    return out
