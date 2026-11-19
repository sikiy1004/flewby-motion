"""ジャンル別の商品イラスト・アイコン（自作 SVG。権利フリーで商品写真の代わりに使う）。

色は CSS 変数（--ink / --accent / --soft / --pop）を参照するので、テーマに自動で馴染む。
"""
from __future__ import annotations

S = 'stroke="var(--ink)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'

_ILLUST = {
    "hair_dryer": f"""
  <g {S}>
    <path d="M168 62 q10 6 0 12 q-10 6 0 12" fill="none" stroke-width="4"/>
    <path d="M182 56 q12 9 0 18 q-12 9 0 18" fill="none" stroke-width="4" opacity=".6"/>
    <rect x="84" y="112" width="30" height="72" rx="14" fill="var(--soft)" transform="rotate(-10 99 148)"/>
    <rect x="28" y="50" width="122" height="62" rx="31" fill="var(--soft)"/>
    <rect x="146" y="60" width="18" height="42" rx="6" fill="var(--pop)"/>
    <circle cx="62" cy="81" r="38" fill="var(--accent)"/>
    <circle cx="62" cy="81" r="18" fill="var(--soft)"/>
    <circle cx="62" cy="81" r="5" fill="var(--ink)" stroke="none"/>
    <circle cx="96" cy="160" r="4" fill="var(--ink)" stroke="none"/>
  </g>""",
    "hair_iron": f"""
  <g {S}>
    <path d="M60 182 L92 30 L112 34 L84 186 Z" fill="var(--accent)"/>
    <path d="M140 182 L108 30 L88 34 L116 186 Z" fill="var(--soft)"/>
    <rect x="92" y="22" width="18" height="34" rx="6" fill="var(--pop)"/>
    <path d="M70 140 L130 140" stroke-width="4"/>
    <circle cx="100" cy="164" r="7" fill="var(--pop)"/>
    <path d="M100 186 q-6 10 4 16" fill="none" stroke-width="4"/>
  </g>""",
    "facial_device": f"""
  <g {S}>
    <rect x="86" y="96" width="30" height="96" rx="15" fill="var(--soft)"/>
    <circle cx="101" cy="62" r="46" fill="var(--accent)"/>
    <circle cx="101" cy="62" r="26" fill="var(--soft)"/>
    <circle cx="101" cy="62" r="9" fill="var(--pop)"/>
    <circle cx="101" cy="140" r="6" fill="var(--pop)"/>
    <path d="M160 26 l0 18 M151 35 l18 0" stroke-width="4"/>
    <path d="M38 118 l0 12 M32 124 l12 0" stroke-width="4"/>
  </g>""",
    "epilator": f"""
  <g {S}>
    <path d="M70 88 Q70 40 112 40 L150 40 Q166 40 166 58 L166 92 Q166 108 150 108 L118 108 L108 186 L78 186 Z" fill="var(--accent)"/>
    <rect x="128" y="50" width="30" height="50" rx="8" fill="var(--pop)"/>
    <path d="M176 60 l18 -8 M178 76 l20 0 M176 92 l18 8" stroke-width="4"/>
    <circle cx="94" cy="120" r="7" fill="var(--soft)"/>
    <path d="M86 150 l18 0" stroke-width="4"/>
  </g>""",
    "toothbrush": f"""
  <g {S}>
    <rect x="84" y="78" width="34" height="116" rx="17" fill="var(--accent)"/>
    <rect x="94" y="22" width="14" height="64" rx="7" fill="var(--soft)"/>
    <rect x="88" y="14" width="26" height="22" rx="6" fill="var(--pop)"/>
    <circle cx="101" cy="122" r="8" fill="var(--soft)"/>
    <circle cx="146" cy="40" r="10" fill="none" stroke-width="4"/>
    <circle cx="160" cy="68" r="6" fill="none" stroke-width="4"/>
    <circle cx="52" cy="54" r="7" fill="none" stroke-width="4"/>
  </g>""",
    "body_scale": f"""
  <g {S}>
    <rect x="26" y="40" width="150" height="150" rx="30" fill="var(--soft)"/>
    <rect x="62" y="62" width="78" height="36" rx="10" fill="var(--accent)"/>
    <path d="M78 80 l12 0 M98 80 l26 0" stroke="var(--soft)" stroke-width="6"/>
    <ellipse cx="72" cy="146" rx="18" ry="26" fill="var(--pop)"/>
    <ellipse cx="130" cy="146" rx="18" ry="26" fill="var(--pop)"/>
  </g>""",
    "humidifier": f"""
  <g {S}>
    <path d="M70 26 q-10 -14 2 -22 M100 22 q-10 -14 2 -22 M130 26 q-10 -14 2 -22" fill="none" stroke-width="4" opacity=".7"/>
    <rect x="58" y="40" width="88" height="22" rx="11" fill="var(--pop)"/>
    <path d="M50 62 L154 62 L146 182 Q146 194 132 194 L72 194 Q58 194 58 182 Z" fill="var(--accent)"/>
    <rect x="76" y="92" width="52" height="64" rx="12" fill="var(--soft)"/>
    <path d="M84 138 q18 -14 36 0" fill="none" stroke-width="4"/>
    <circle cx="102" cy="176" r="6" fill="var(--soft)"/>
  </g>""",
    "futon_dryer": f"""
  <g {S}>
    <rect x="18" y="104" width="174" height="62" rx="20" fill="var(--soft)"/>
    <path d="M18 128 Q105 112 192 128" fill="none" stroke-width="4"/>
    <rect x="34" y="150" width="66" height="44" rx="12" fill="var(--accent)"/>
    <path d="M100 168 Q130 168 136 140" fill="none" stroke-width="8"/>
    <circle cx="56" cy="172" r="7" fill="var(--pop)"/>
    <path d="M150 74 q8 -10 0 -20 M166 78 q8 -10 0 -20 M134 78 q8 -10 0 -20" fill="none" stroke-width="4" opacity=".7"/>
  </g>""",
    "massager": f"""
  <g {S}>
    <path d="M40 84 Q40 168 104 168 Q168 168 168 84" fill="none" stroke="var(--ink)" stroke-width="34"/>
    <path d="M40 84 Q40 168 104 168 Q168 168 168 84" fill="none" stroke="var(--accent)" stroke-width="22"/>
    <circle cx="40" cy="78" r="20" fill="var(--pop)"/>
    <circle cx="168" cy="78" r="20" fill="var(--pop)"/>
    <circle cx="104" cy="168" r="10" fill="var(--soft)"/>
    <path d="M86 34 l0 18 M77 43 l18 0" stroke-width="4"/>
  </g>""",
    "smart_watch": f"""
  <g {S}>
    <rect x="76" y="10" width="54" height="52" rx="10" fill="var(--pop)"/>
    <rect x="76" y="148" width="54" height="52" rx="10" fill="var(--pop)"/>
    <rect x="52" y="52" width="102" height="106" rx="30" fill="var(--accent)"/>
    <rect x="66" y="66" width="74" height="78" rx="20" fill="var(--soft)"/>
    <path d="M76 108 l12 0 l6 -14 l10 28 l7 -14 l14 0" fill="none" stroke-width="4"/>
    <rect x="154" y="88" width="10" height="26" rx="5" fill="var(--soft)"/>
  </g>""",
    "electric_blanket": f"""
  <g {S}>
    <path d="M28 52 Q104 34 180 52 L180 160 Q104 142 28 160 Z" fill="var(--accent)"/>
    <path d="M44 78 Q104 64 164 78 M44 104 Q104 90 164 104 M44 130 Q104 116 164 130" fill="none" stroke="var(--soft)" stroke-width="5"/>
    <path d="M180 140 Q196 150 186 172 Q178 190 194 196" fill="none" stroke-width="4"/>
    <rect x="164" y="170" width="30" height="26" rx="7" fill="var(--pop)"/>
  </g>""",
}

_ICONS = {
    "yen": f'<g {S}><circle cx="50" cy="50" r="40" fill="var(--pop)"/><path d="M34 28 L50 50 L66 28 M50 50 L50 76 M36 54 L64 54 M36 66 L64 66" fill="none"/></g>',
    "star": f'<g {S}><path d="M50 10 L62 38 L92 40 L68 60 L76 90 L50 73 L24 90 L32 60 L8 40 L38 38 Z" fill="var(--pop)"/></g>',
    "people": f'<g {S}><circle cx="36" cy="36" r="16" fill="var(--pop)"/><circle cx="66" cy="40" r="13" fill="var(--soft)"/><path d="M8 88 Q10 58 36 58 Q62 58 64 88 Z" fill="var(--pop)"/><path d="M60 88 Q60 64 72 62 Q92 62 92 88 Z" fill="var(--soft)"/></g>',
    "bookmark": f'<g {S}><path d="M24 10 L76 10 L76 92 L50 72 L24 92 Z" fill="var(--pop)"/></g>',
    "check": f'<g {S}><circle cx="50" cy="50" r="40" fill="var(--pop)"/><path d="M30 52 L45 66 L72 36" fill="none" stroke-width="8"/></g>',
    "spark": f'<g {S}><path d="M50 6 Q56 44 94 50 Q56 56 50 94 Q44 56 6 50 Q44 44 50 6 Z" fill="var(--pop)"/></g>',
}


def illustration(genre_key: str, size: int = 200) -> str:
    body = _ILLUST.get(genre_key, _ILLUST["facial_device"])
    return f'<svg class="illust" viewBox="0 0 210 210" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def icon(name: str, size: int = 64) -> str:
    return f'<svg class="icon" viewBox="0 0 100 100" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">{_ICONS[name]}</svg>'


def arrow(kind: str = "curve", size: int = 140) -> str:
    """手描き風の矢印。"""
    paths = {
        "curve": "M10 20 C 60 0, 120 30, 120 100 M100 80 L120 104 L138 78",
        "down": "M30 10 C 10 60, 70 70, 60 120 M40 100 L60 124 L78 100",
        "left": "M130 30 C 90 10, 40 20, 20 70 M14 46 L18 74 L44 68",
    }
    return (f'<svg class="arrow" viewBox="0 0 150 130" width="{size}" height="{int(size * .87)}">'
            f'<path d="{paths[kind]}" fill="none" stroke="var(--ink)" stroke-width="5" stroke-linecap="round" '
            f'stroke-linejoin="round"/></svg>')


def radar(values: list[float], labels: list[str], size: int = 360) -> str:
    """0〜1 の値のレーダーチャート（4〜5軸）。"""
    import math

    n = len(values)
    cx = cy = size / 2
    r = size * 0.34

    def pt(i: int, k: float) -> tuple[float, float]:
        a = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * k * math.cos(a), cy + r * k * math.sin(a)

    grid = ""
    for k in (0.33, 0.66, 1.0):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, k) for i in range(n)))
        grid += f'<polygon points="{pts}" fill="none" stroke="var(--line)" stroke-width="2"/>'
    axes = "".join(f'<line x1="{cx}" y1="{cy}" x2="{pt(i, 1)[0]:.1f}" y2="{pt(i, 1)[1]:.1f}" stroke="var(--line)" stroke-width="2"/>'
                   for i in range(n))
    vals = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, max(0.08, v)) for i, v in enumerate(values)))
    shape = (f'<polygon points="{vals}" fill="var(--accent)" fill-opacity=".28" stroke="var(--accent)" '
             f'stroke-width="5" stroke-linejoin="round"/>')
    dots = "".join(f'<circle cx="{pt(i, max(0.08, v))[0]:.1f}" cy="{pt(i, max(0.08, v))[1]:.1f}" r="7" fill="var(--accent)"/>'
                   for i, v in enumerate(values))
    texts = ""
    for i, lab in enumerate(labels):
        x, y = pt(i, 1.28)
        texts += (f'<text x="{x:.1f}" y="{y + 8:.1f}" text-anchor="middle" font-size="24" font-weight="700" '
                  f'fill="var(--sub)" font-family="Zen Kaku Gothic New, NotoJP">{lab}</text>')
    return f'<svg class="radar" viewBox="0 0 {size} {size}" width="{size}" height="{size}">{grid}{axes}{shape}{dots}{texts}</svg>'
