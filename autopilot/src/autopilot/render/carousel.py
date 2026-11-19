"""カルーセル（1080×1350 JPEG × 6〜8枚）とストーリー告知画像の生成。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import Settings
from ..llm.schema import Copy
from . import FORMAT_LABEL, base_css, phrase_html, render_template, screenshot_sections


def price_band_label(price: int) -> str:
    return "〜1万円" if price < 10000 else ("1〜2.5万円" if price < 25000 else "2.5万円〜")


def product_labels(fmt: str, idx: int, p: dict[str, Any]) -> tuple[str, str, str, str]:
    """(大きい表記, 単位, チップ, 表の短い表記)"""
    if fmt == "ranking":
        return str(p.get("rank") or idx + 1), "位", "楽天ランキング", str(p.get("rank") or idx + 1)
    if fmt == "price_band":
        band = price_band_label(p["price"])
        return band, "", "価格帯別", band.replace("円", "")
    if fmt == "spotlight":
        return ("注目", "", "比較の主役", "注目") if idx == 0 else (f"比較{idx}", "", "比べたい1台", f"比{idx}")
    return f"例{idx + 1}", "", "選び方の例", f"例{idx + 1}"


def build_slides(plan: dict[str, Any], copy: Copy) -> list[dict[str, Any]]:
    fmt, products = plan["format"], plan["products"]
    n_chars = len(copy.hook)
    hook_size = 112 if n_chars <= 9 else (100 if n_chars <= 12 else (88 if n_chars <= 16 else 78))
    slides: list[dict[str, Any]] = [{
        "type": "cover", "hook_html": phrase_html(copy.hook), "subtitle": copy.subtitle, "hook_size": hook_size,
        "lineup_title": "このページで比較するのは" if fmt != "guide" else "例に挙げるモデル",
        "lineup": products[:5],
    }]
    if fmt == "guide":
        for n, t in enumerate(plan["tips"], 1):
            slides.append({"type": "tip", "n": n, "title": t["title"], "body": t["body"]})
    table_products = []
    for i, p in enumerate(products):
        big, suffix, chip, short = product_labels(fmt, i, p)
        table_products.append({**p, "label_short": short})
    table = {
        "type": "table",
        "title": {"ranking": "ひと目で比較", "price_band": "価格帯別に比較", "spotlight": "3台を比較",
                  "guide": "ポイントを押さえた例"}[fmt],
        "caption": f"{plan['genre_label']}｜価格・評価・レビュー数",
        "products": table_products,
        "ranked": fmt == "ranking",
        "best_price": min(products, key=lambda p: p["price"])["id"],
        "best_avg": max(products, key=lambda p: p["review_avg"])["id"],
        "best_count": max(products, key=lambda p: p["review_count"])["id"],
    }
    slides.append(table)
    max_price = max(p["price"] for p in products) or 1
    max_count = max(p["review_count"] for p in products) or 1
    if fmt != "guide":
        for i, p in enumerate(products):
            big, suffix, chip, _ = product_labels(fmt, i, p)
            slides.append({"type": "product", "product": p, "label_main": big, "label_suffix": suffix,
                           "label_chip": chip, "note": copy.product_notes.get(p["item_code"], ""),
                           "n": len(products), "max_price": max_price, "max_count": max_count})
        slides.append({"type": "picks", "title": "タイプ別に選ぶなら", "picks": plan["picks"], "summary": copy.summary})
    slides.append({"type": "cta"})
    return slides[:10]  # Instagram API のカルーセル上限


def render_carousel(settings: Settings, plan: dict[str, Any], copy: Copy, post_no: int, out_dir: Path) -> list[Path]:
    slides = build_slides(plan, copy)
    html_text = render_template(
        "carousel.html.j2",
        base_css=base_css(settings.fonts_dir),
        theme=plan["theme"],
        slides=slides,
        total=len(slides),
        post_no=post_no,
        genre=plan["genre_label"],
        format_label=FORMAT_LABEL[plan["format"]],
        date_label=plan["date_label"],
        account=settings.get("account.name", ""),
        handle=settings.get("account.handle", ""),
    )
    targets = [(f"#slide-{i}", out_dir / f"slide_{i + 1:02d}.jpg") for i in range(len(slides))]
    return screenshot_sections(html_text, out_dir / "_work", targets, width=1080, height=1350, jpeg=True)


def render_story(settings: Settings, plan: dict[str, Any], copy: Copy, post_no: int, out_dir: Path) -> Path:
    html_text = render_template(
        "story.html.j2", base_css=base_css(settings.fonts_dir), theme=plan["theme"], post_no=post_no,
        hook_html=phrase_html(copy.hook), genre=plan["genre_label"])
    path = out_dir / "story.jpg"
    screenshot_sections(html_text, out_dir / "_work", [("#story", path)], width=1080, height=1920, jpeg=True)
    return path
