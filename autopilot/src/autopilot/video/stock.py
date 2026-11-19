"""無料素材（Pexels API）から冒頭シーン用の縦動画を取得。キーが無ければ使わない（図形背景で成立する）。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from ..config import Settings

log = logging.getLogger(__name__)

QUERIES = {
    "hair_dryer": "woman drying hair",
    "hair_iron": "hair styling",
    "facial_device": "skincare routine",
    "epilator": "skincare body care",
    "toothbrush": "bathroom morning routine",
    "body_scale": "healthy lifestyle morning",
}


def fetch_background_video(settings: Settings, plan: dict[str, Any], work: Path) -> Path | None:
    key = settings.env("PEXELS_API_KEY")
    if not key or settings.sample_mode:
        return None
    query = QUERIES.get(plan["genre_key"], "beauty skincare")
    try:
        r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key},
                         params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 15}, timeout=30)
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if not videos:
            return None
        v = videos[plan.get("date", "0")[-1:].isdigit() and int(plan["date"][-1]) % len(videos) or 0]
        files = [f for f in v["video_files"] if f.get("height", 0) >= 1280 and f.get("height", 0) <= 1920
                 and f.get("file_type") == "video/mp4"]
        if not files:
            return None
        url = sorted(files, key=lambda f: f["height"])[0]["link"]
        out = work / "stock.mp4"
        with requests.get(url, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with out.open("wb") as fh:
                for chunk in resp.iter_content(1 << 16):
                    fh.write(chunk)
        return out
    except (requests.RequestException, KeyError, ValueError) as e:
        log.warning("pexels skipped: %s", e)
        return None
