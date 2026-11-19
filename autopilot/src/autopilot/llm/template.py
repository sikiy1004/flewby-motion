"""LLM を使わない決定論の文章生成（全LLMが落ちても投稿を止めないための最終フォールバック）。

ここに書く文言は人間が書いた「安全な言い回し」だけで構成する。
"""
from __future__ import annotations

import random
from typing import Any

from .schema import Copy

HOOKS: dict[str, dict[str, list[str]]] = {
    "ranking": {
        "number": ["{genre}売れ筋TOP{n}を比較", "人気{genre}{n}台を1枚で比較"],
        "loss": ["{genre}選びで後悔したくない人へ", "買う前に見て。{genre}比較"],
        "compare": ["{genre}、結局どれがいい？", "売れ筋{genre}を徹底比較"],
        "question": ["{genre}、何で選んでる？", "いま売れてる{genre}知ってる？"],
    },
    "price_band": {
        "number": ["予算別{genre}3選", "{genre}を価格帯別に3つ"],
        "loss": ["予算オーバーで後悔しない{genre}", "高ければいい？{genre}の選び方"],
        "compare": ["1万円以下vsハイエンド{genre}", "価格帯別{genre}の違い"],
        "question": ["{genre}の予算、いくらにする？", "{genre}にいくらかける？"],
    },
    "spotlight": {
        "number": ["注目の{genre}をスペックで解説", "いま気になる{genre}1台"],
        "loss": ["その{genre}、買う前に比較した？", "見落としがちな{genre}のポイント"],
        "compare": ["人気{genre}を他モデルと比較", "注目{genre}vs売れ筋2台"],
        "question": ["この{genre}、知ってた？", "話題の{genre}どう選ぶ？"],
    },
    "guide": {
        "number": ["{genre}選びのポイント4つ", "失敗しない{genre}の選び方4つ"],
        "loss": ["{genre}選びで失敗しないために", "買ってから気づく{genre}の盲点"],
        "compare": ["{genre}はここを比べればOK", "{genre}比較のチェックリスト"],
        "question": ["{genre}どうやって選ぶ？", "{genre}選びで迷ってない？"],
    },
}

SUBTITLES = {
    "ranking": "楽天ランキング上位を価格・レビューで比較",
    "price_band": "価格帯ごとにレビューの多い1台をピックアップ",
    "spotlight": "スペックと口コミの数字で比べてみた",
    "guide": "スペック表のどこを見る？をまとめました",
}


def yen_spoken(price: int | None) -> str:
    if not price:
        return ""
    man, rest = divmod(int(price), 10000)
    if man and rest:
        return f"{man}万{rest}円"
    if man:
        return f"{man}万円"
    return f"{rest}円"


def _note(p: dict[str, Any]) -> str:
    f = p.get("features") or []
    if len(f) >= 2:
        return f"「{f[0]}」「{f[1]}」を重視する人に"
    if f:
        return f"「{f[0]}」を重視する人に"
    return "シンプルな機能で選びたい人に"


def _narration(p: dict[str, Any], fmt: str, idx: int) -> str:
    """読み上げは短く（価格・評価は画面に出ているので、名前と特徴だけ話す）。"""
    if fmt == "ranking" and p.get("rank"):
        head = f"{p['rank']}位は"
    elif fmt == "price_band":
        price = int(p["price"])
        head = "1万円以下なら" if price < 10000 else ("1万円から2万5000円なら" if price < 25000 else "2万5000円以上なら")
    else:
        head = "注目は" if idx == 0 else "比べたいのは"
    feats = (p.get("features") or [])[:2]
    tail = f"{'と'.join(feats)}が特徴です。" if feats else "シンプルで使いやすいモデルです。"
    return f"{head}{p['name']}。{tail}"


def template_copy(plan: dict[str, Any], rng: random.Random | None = None) -> Copy:
    rng = rng or random.Random(plan.get("date"))
    fmt, genre = plan["format"], plan["genre_label"]
    products = plan["products"]
    n = len(products)
    hook = rng.choice(HOOKS[fmt][plan["hook_type"]]).format(genre=genre, n=n)
    season = plan.get("season")
    subtitle = SUBTITLES[fmt]
    if season:
        subtitle = f"{season}。{subtitle}"[:44]

    if fmt == "guide":
        summary = "スペック表の数字と、自分の使い方を照らし合わせて選ぶのがコツ"
        narr_products = {p["item_code"]: f"例えば{p['name']}は、{('、'.join(p['features'][:2]) or 'シンプルな機能')}が特徴。" for p in products}
    else:
        summary = "価格・レビュー・機能のバランスで、自分に合う1台を選んでね"
        narr_products = {p["item_code"]: _narration(p, fmt, i) for i, p in enumerate(products)}

    lines = [f"{genre}を{'選ぶポイントと一緒に' if fmt == 'guide' else '数字で'}比較しました。"]
    sig = plan.get("signal")
    if fmt == "spotlight" and sig and products:
        what = {"rank_up": "楽天ランキングで順位アップ", "price_drop": "直近で価格が下がった",
                "new_entry": "新しくランキング入りした"}.get(sig["kind"], "注目の")
        lines.append(f"注目は{what}「{products[0]['name']}」（{sig['detail']}）。")
    if season:
        lines.insert(0, f"{season}、{genre}を見直す人も多い時期。")
    for p in products:
        lines.append(f"・{p['name']}：{p['price']:,}円／★{p['review_avg']:.2f}（{p['review_count']:,}件）")
    lines.append("")
    lines.append("気になるものがあったら保存して、比べるときに見返してね。")
    tags_ig = list(plan.get("genre_hashtags", []))[:3] + ["#美容家電", "#比較"]
    tags_tt = list(plan.get("genre_hashtags", []))[:2] + ["#美容家電", "#おすすめ"]

    return Copy(
        hook=hook,
        subtitle=subtitle,
        product_notes={p["item_code"]: _note(p) for p in products},
        summary=summary,
        narration_hook=f"{hook}。" + ("最後にタイプ別のおすすめも紹介するね。" if fmt != "guide" else ""),
        narration_products=narr_products,
        narration_outro="詳しいリンクはプロフィールから。保存して見返してね。",
        caption_body="\n".join(lines),
        caption_tiktok=f"{hook}｜どれが気になる？コメントで教えてね",
        hashtags_instagram=tags_ig,
        hashtags_tiktok=tags_tt,
    )
