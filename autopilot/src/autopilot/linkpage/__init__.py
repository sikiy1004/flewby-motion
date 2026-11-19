"""プロフィールに貼るリンク集ページ（投稿番号 No.xxx → 商品リンク）を生成する。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import Settings, now_jst
from ..db import DB

_env = Environment(loader=FileSystemLoader(Path(__file__).parent), autoescape=select_autoescape(["j2", "html"]))


def build_linkpage(settings: Settings, db: DB, limit: int = 200) -> str:
    posts = db.posts_by_status(["ready", "published"])
    posts = sorted(posts, key=lambda p: p["post_no"], reverse=True)[:limit]
    entries: list[dict[str, Any]] = []
    for p in posts:
        plan, script = p["plan"], p["script"] or {}
        offers = [o for o in settings.offers if p["genre_key"] in (o.get("genres") or [])]
        entries.append({
            "no": p["post_no"],
            "title": script.get("hook") or plan["genre_label"],
            "genre": plan["genre_label"],
            "date": plan["date_label"],
            "products": [{"name": x["name"], "price": x["price"], "rakuten": x.get("affiliate_url"),
                          "amazon": x.get("amazon_url")} for x in plan["products"]],
            "offers": offers,
        })
    return _env.get_template("page.html.j2").render(
        account=settings.get("account.name", ""),
        concept=settings.get("account.concept", ""),
        entries=entries,
        pinned=[o for o in settings.offers if o.get("pinned")],
        updated=now_jst().strftime("%Y-%m-%d %H:%M"),
    )
