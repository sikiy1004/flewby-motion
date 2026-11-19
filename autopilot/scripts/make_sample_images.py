"""デモ用の架空商品写真（スタジオ撮影風のイラスト画像）を作る。本番では楽天の商品画像が使われる。

python scripts/make_sample_images.py
"""
import json
from pathlib import Path

from autopilot.render import screenshot_sections
from autopilot.render.illustrations import illustration

ROOT = Path(__file__).resolve().parents[1]
PALETTES = [("#C8553D", "#F4C84F"), ("#2F7A57", "#FF9A76"), ("#C9476B", "#FFE36E"), ("#3B5BA9", "#9AD1F5"),
            ("#2B2420", "#E9C46A"), ("#8E6CC4", "#F7B7D2")]

items = json.loads((ROOT / "sample" / "products.json").read_text(encoding="utf-8"))["items"]
sections, targets = [], []
for i, it in enumerate(items):
    acc, pop = PALETTES[i % len(PALETTES)]
    sections.append(f"""
<section id="p{i}" style="--ink:#2B2420;--accent:{acc};--pop:{pop};--soft:#FFFFFF;width:600px;height:600px;position:relative;
  background:radial-gradient(420px 320px at 50% 40%, #FFFFFF, #EEF0F2);display:flex;align-items:center;justify-content:center;overflow:hidden">
  <div style="position:absolute;left:150px;right:150px;bottom:92px;height:34px;border-radius:50%;background:rgba(0,0,0,.16);filter:blur(10px)"></div>
  <div style="transform:rotate({(-8, 6, -3, 9, -6, 4)[i % 6]}deg);position:relative">{illustration(it['genre_key'], 400)}</div>
  <div style="position:absolute;right:18px;bottom:12px;font:700 18px sans-serif;color:#9AA0A6;letter-spacing:.2em">SAMPLE</div>
</section>""")
    targets.append((f"#p{i}", ROOT / it["image"]))
html = "<!doctype html><html><body style='margin:0'>" + "".join(sections) + "</body></html>"
screenshot_sections(html, ROOT / "output" / "_sample_work", targets, width=600, height=600, jpeg=True)
print(f"{len(targets)} images")
