"""商品画像の取得と整形（楽天 API の画像 URL → ローカルの正方形 JPEG）。

- 取得できない・小さすぎる画像は使わず、自作イラストで代替する（投稿は止めない）。
- 一度取得した画像は data/img_cache にキャッシュする。
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageOps

from .config import Settings

log = logging.getLogger(__name__)
SIZE = 800


def _normalize(src: Path, dst: Path) -> Path | None:
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            if min(im.size) < 200:
                return None
            # 余白の白を詰めてから正方形の白背景に配置（商品が小さく写るのを防ぐ）
            diff = ImageOps.invert(im.convert("L"))
            bbox = diff.point(lambda v: 255 if v > 18 else 0).getbbox()
            if bbox and (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) > 0.2 * im.size[0] * im.size[1]:
                im = im.crop(bbox)
            side = int(max(im.size) * 1.08)
            canvas = Image.new("RGB", (side, side), (255, 255, 255))
            canvas.paste(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2))
            canvas.resize((SIZE, SIZE), Image.LANCZOS).save(dst, "JPEG", quality=90)
            return dst
    except Exception as e:  # 壊れた画像など
        log.warning("image normalize failed %s: %s", src, e)
        return None


def fetch_image(settings: Settings, url: str | None) -> Path | None:
    if not url:
        return None
    cache = settings.data_dir / "img_cache"
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()[:16]
    out = cache / f"{key}.jpg"
    if out.exists():
        return out
    raw = cache / f"{key}.raw"
    if url.startswith(("http://", "https://")):
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (autopilot)"})
            r.raise_for_status()
            if not r.headers.get("content-type", "image").startswith("image") or len(r.content) < 2048:
                return None
            raw.write_bytes(r.content)
        except requests.RequestException as e:
            log.warning("image download failed: %s", e)
            return None
    else:
        p = Path(url.replace("file://", ""))
        if not p.is_absolute():
            p = settings.root / p
        if not p.exists():
            return None
        raw.write_bytes(p.read_bytes())
    res = _normalize(raw, out)
    raw.unlink(missing_ok=True)
    return res


def attach_photos(settings: Settings, plan: dict[str, Any]) -> dict[str, Any]:
    """plan の各商品に photo（ローカル JPEG のパス）を付けたコピーを返す。"""
    if not settings.get("content.use_product_images", False):
        return plan
    products = []
    for p in plan["products"]:
        path = fetch_image(settings, p.get("image_url"))
        products.append({**p, "photo": str(path) if path else None})
    return {**plan, "products": products}
