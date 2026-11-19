"""無料素材（Pexels API）から冒頭シーン用の実写の縦動画を取得する。

- ジャンルごとの検索語（genres.yaml の stock_queries）からランダムに選び、同じ動画は 30 本空けるまで再利用しない。
- キーが無い・取得に失敗した場合は使わない（紙＋イラストの背景で成立する）。
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

import requests

from ..config import Settings
from ..db import DB

log = logging.getLogger(__name__)
FALLBACK_QUERIES = ["self care routine", "cozy home morning"]


def _load_used(settings: Settings) -> list[int]:
    db = DB(settings.db_path)
    try:
        return json.loads(db.kv_get("stock_used", "[]") or "[]")
    except ValueError:
        return []
    finally:
        db.close()


def _save_used(settings: Settings, used: list[int]) -> None:
    db = DB(settings.db_path)
    try:
        db.kv_set("stock_used", json.dumps(used[-30:]))
    finally:
        db.close()


def fetch_background_video(settings: Settings, plan: dict[str, Any], work: Path) -> Path | None:
    key = settings.env("PEXELS_API_KEY")
    if not key or settings.sample_mode or not settings.get("video.stock_background", True):
        return None
    used = _load_used(settings)
    queries = list(plan.get("stock_queries") or FALLBACK_QUERIES)
    random.shuffle(queries)
    try:
        for query in queries:
            r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key},
                             params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 30},
                             timeout=30)
            r.raise_for_status()
            videos = [v for v in r.json().get("videos", []) if v["id"] not in used and 4 <= v.get("duration", 0) <= 40]
            random.shuffle(videos)
            for v in videos:
                files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4"
                         and 1280 <= (f.get("height") or 0) <= 1920 and (f.get("width") or 0) < (f.get("height") or 0)]
                if not files:
                    continue
                url = sorted(files, key=lambda f: f["height"])[0]["link"]
                out = work / "stock.mp4"
                with requests.get(url, stream=True, timeout=120) as resp:
                    resp.raise_for_status()
                    with out.open("wb") as fh:
                        for chunk in resp.iter_content(1 << 16):
                            fh.write(chunk)
                _save_used(settings, used + [v["id"]])
                log.info("stock video: %s (%s)", v.get("url"), query)
                return out
    except (requests.RequestException, KeyError, ValueError) as e:
        log.warning("pexels skipped: %s", e)
    return None
