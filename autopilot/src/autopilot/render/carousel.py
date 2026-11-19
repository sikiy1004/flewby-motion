"""カルーセル（1080×1350 JPEG × 6〜10枚）とストーリー告知画像の生成。

デザイン: 雑誌（エディトリアル）× 方眼ノート × 比較データ。
  表紙 → ◎○△比較表 → 商品ページ（レーダー＋データスコア）→ 結論 → 保存CTA
"""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from markupsafe import Markup

from ..config import Settings
from ..llm.schema import Copy
from ..scoring import AXES
from . import FORMAT_LABEL, base_css, phrase_html, render_template, screenshot_sections
from .illustrations import arrow, icon, illustration, radar

ANNOTATIONS = ["ここ大事！", "見落としがち", "要チェック", "比べてみて"]


def price_band_label(price: int) -> str:
    return "〜1万円" if price < 10000 else ("1〜2.5万円" if price < 25000 else "2.5万円〜")


def product_labels(fmt: str, idx: int, p: dict[str, Any]) -> tuple[str, str, str, str]:
    """(大きい表記, 単位, 小見出し, 表の短い表記)"""
    if fmt == "ranking":
        r = str(p.get("rank") or idx + 1)
        return r, "位", "楽天ランキング", f"{r}位"
    if fmt == "price_band":
        band = price_band_label(p["price"])
        return band, "", "価格帯", band.replace("円", "")
    if fmt == "spotlight":
        return ("注目", "", "今回の主役", "注目") if idx == 0 else (f"比較{idx}", "", "比べたいモデル", f"比較{idx}")
    return f"例{idx + 1}", "", "選び方の例", f"例{idx + 1}"


def design_assets(settings: Settings) -> dict[str, Any]:
    design = (settings.assets_dir / "design" / "design.css").read_text(encoding="utf-8")
    return {
        "webfonts": (settings.assets_dir / "webfonts" / "webfonts.css").resolve().as_uri(),
        "design_css": Markup(design),
        "base_css": base_css(settings.fonts_dir),
    }


def _big_number(plan: dict[str, Any]) -> tuple[str, str]:
    n = len(plan["products"])
    return {
        "ranking": (str(n), "機種を<br>データで比較"),
        "price_band": ("3", "つの価格帯で<br>選んでみた"),
        "spotlight": ("1", "台を深掘り<br>＋2台と比較"),
        "guide": (str(len(plan["tips"]) or 4), "つの<br>チェックポイント"),
    }[plan["format"]]


def build_slides(plan: dict[str, Any], copy: Copy) -> list[dict[str, Any]]:
    fmt, products, genre = plan["format"], plan["products"], plan["genre_key"]
    n_chars = len(copy.hook)
    hook_size = 124 if n_chars <= 9 else (112 if n_chars <= 12 else (98 if n_chars <= 15 else 86))
    big_n, big_label = _big_number(plan)
    slides: list[dict[str, Any]] = [{
        "type": "cover", "hook_html": phrase_html(copy.hook), "subtitle": copy.subtitle, "hook_size": hook_size,
        "illust": illustration(genre, 330), "big_n": big_n, "big_label": big_label,
        "lineup_text": " / ".join(p["name"] for p in products[:5]),
    }]
    if fmt == "guide":
        for k, t in enumerate(plan["tips"], 1):
            slides.append({"type": "tip", "n": k, "title_html": phrase_html(t["title"]), "body": t["body"],
                           "icon": illustration(genre, 190), "anno": ANNOTATIONS[(k - 1) % len(ANNOTATIONS)]})
    table_products = []
    for i, p in enumerate(products):
        _, _, _, short = product_labels(fmt, i, p)
        table_products.append({**p, "label_short": short})
    best = next((p for p in products if p.get("best")), products[0])
    slides.append({
        "type": "table",
        "title_html": phrase_html({"ranking": "ひと目でわかる比較表", "price_band": "価格帯別の比較表",
                                   "spotlight": "3台の比較表", "guide": "ポイントで見る比較表"}[fmt]),
        "products": table_products, "n": len(products), "best_name": best["name"],
    })
    if fmt != "guide":
        for i, p in enumerate(products):
            big, suffix, chip, _ = product_labels(fmt, i, p)
            slides.append({
                "type": "product", "product": p, "label_main": big, "label_suffix": suffix, "label_chip": chip,
                "label_jp": not big.isdigit(),
                "note": copy.product_notes.get(p["item_code"], ""), "n": len(products),
                "illust": illustration(genre, 180),
                "radar": radar([p["axes"][k] for k, _ in AXES], [lab for _, lab in AXES], size=300),
            })
    icons_by_label = {"価格重視なら": icon("yen", 74), "評価重視なら": icon("star", 74), "定番を選ぶなら": icon("people", 74)}
    picks = [{**k, "icon": icons_by_label.get(k["label"], icon("check", 74))} for k in plan["picks"]]
    slides.append({"type": "picks", "title_html": phrase_html("結論：タイプ別に選ぶなら"), "picks": picks,
                   "summary": copy.summary})
    slides.append({"type": "cta", "title_html": "比べるときに<br>見返せるよう<br><em>保存</em>してね"})
    return slides[:10]  # Instagram API のカルーセル上限


def render_carousel(settings: Settings, plan: dict[str, Any], copy: Copy, post_no: int, out_dir: Path) -> list[Path]:
    slides = build_slides(plan, copy)
    month, day = plan["date"][5:7], plan["date"][8:10]
    html_text = render_template(
        "carousel.html.j2",
        **design_assets(settings),
        theme=plan["theme"],
        slides=slides,
        total=len(slides),
        post_no=post_no,
        genre=plan["genre_label"],
        format_label=FORMAT_LABEL[plan["format"]],
        date_label=plan["date_label"],
        date_short=f"{int(month)}.{int(day)}",
        account=html.escape(settings.get("account.name", "")),
        handle=settings.get("account.handle", ""),
        icons={"yen": icon("yen", 44), "star": icon("star", 44), "people": icon("people", 44), "spark": icon("spark", 44),
               "bookmark_big": icon("bookmark", 220)},
        arrow_up=arrow("curve", 120), arrow_down=arrow("down", 120),
    )
    targets = [(f"#slide-{i}", out_dir / f"slide_{i + 1:02d}.jpg") for i in range(len(slides))]
    return screenshot_sections(html_text, out_dir / "_work", targets, width=1080, height=1350, jpeg=True)


def render_story(settings: Settings, plan: dict[str, Any], copy: Copy, post_no: int, out_dir: Path) -> Path:
    html_text = render_template(
        "story.html.j2", **design_assets(settings), theme=plan["theme"], post_no=post_no,
        hook_html=phrase_html(copy.hook), genre=plan["genre_label"], illust=illustration(plan["genre_key"], 230),
        arrow_down=arrow("down", 130))
    path = out_dir / "story.jpg"
    screenshot_sections(html_text, out_dir / "_work", [("#story", path)], width=1080, height=1920, jpeg=True)
    return path
