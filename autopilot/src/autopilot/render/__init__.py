"""HTML/CSS テンプレート → Playwright（Chromium）で PNG/JPEG にレンダリング。"""
from __future__ import annotations

import html
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

TEMPLATES = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]))

try:
    import budoux
    _parser = budoux.load_default_japanese_parser()
except Exception:  # pragma: no cover
    _parser = None

FORMAT_LABEL = {"ranking": "売れ筋比較", "price_band": "価格帯別", "spotlight": "注目モデル", "guide": "選び方"}


def phrase_html(text: str, emphasize: bool = True) -> str:
    """日本語の自然な位置で改行できるよう <wbr> を入れ、数字やキーワードを強調する。"""
    chunks = _parser.parse(text) if _parser else [text]
    out = "<wbr>".join(html.escape(c) for c in chunks)
    if emphasize:
        out = re.sub(r"(TOP\d+|\d+(選|つ|台)|比較|後悔|選び方|どれ)", r"<em>\1</em>", out, count=1)
    return f'<span style="word-break:keep-all;overflow-wrap:anywhere">{out}</span>'


def jp_filter(text: str) -> Markup:
    return Markup(phrase_html(str(text), emphasize=False))


_env.filters["jp"] = jp_filter


def base_css(fonts_dir: Path) -> Markup:
    return Markup(_env.get_template("base.css.j2").render(fonts=fonts_dir.resolve().as_uri()))


def render_template(name: str, **ctx: Any) -> str:
    return _env.get_template(name).render(**ctx)


def _chromium_path() -> str | None:
    p = os.environ.get("CHROMIUM_EXECUTABLE")
    return p if p and Path(p).exists() else None


@contextmanager
def browser() -> Iterator[Any]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        kwargs: dict[str, Any] = {"args": ["--no-sandbox", "--font-render-hinting=none"]}
        exe = _chromium_path()
        if exe:
            kwargs["executable_path"] = exe
        b = pw.chromium.launch(**kwargs)
        try:
            yield b
        finally:
            b.close()


def screenshot_sections(html_text: str, work: Path, selectors: list[tuple[str, Path]], *,
                        width: int, height: int, transparent: bool = False, jpeg: bool = False) -> list[Path]:
    """1 枚の HTML を開き、各 section を個別に画像化する。"""
    work.mkdir(parents=True, exist_ok=True)
    src = work / "_page.html"
    src.write_text(html_text, encoding="utf-8")
    out: list[Path] = []
    with browser() as b:
        page = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        page.goto(src.resolve().as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(150)
        for sel, path in selectors:
            el = page.locator(sel)
            if jpeg:
                el.screenshot(path=str(path), type="jpeg", quality=92)
            else:
                el.screenshot(path=str(path), type="png", omit_background=transparent)
            out.append(path)
        page.close()
    return out
