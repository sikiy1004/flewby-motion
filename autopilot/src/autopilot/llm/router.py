"""LLM ルーター：無料枠プロバイダーを順に試し、検証に通った最初の結果を採用。

全滅したらテンプレート（決定論）にフォールバックするので、投稿は止まらない。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from .. import compliance
from ..config import Settings
from .providers import PROVIDERS, ProviderUnavailable
from .schema import Copy
from .template import template_copy

log = logging.getLogger(__name__)

SYSTEM = """あなたは日本の Instagram / TikTok で美容家電の比較情報を発信する編集者です。
読者は20〜30代女性。親しみやすく、でも誠実なトーンで書きます。

【絶対に守るルール】
- 出力は指定キーを持つ JSON オブジェクトのみ。
- 数値（価格・順位・レビュー数・評価）は、与えられたデータの値以外を書かない。割引率や「◯%」も書かない。
- 効能・効果を断定しない（例: 治る、シミが消える、若返る、痩せる、永久脱毛、医療級、サロン級、安全、副作用なし）。
- 根拠のない最上級表現（No.1、日本一、最安、業界初）や、断定（必ず、絶対）、煽り（今だけ、残りわずか）を使わない。
- 「〜を重視する人に」「〜が特徴」のように、スペック・機能・使い方の事実ベースで書く。
- 絵文字は控えめに（キャプション内で最大3個）。"""

USER_TMPL = """# 投稿の企画
- 形式: {kind}（{format_desc}）
- ジャンル: {genre}
- フックの型: {hook_desc}
- 季節の文脈: {season}
- 注目シグナル: {signal}

# 商品データ（これ以外の数値は使わない）
{products}

# 出力する JSON のキー
- hook: 表紙／動画冒頭3秒の一文。24字以内。スクロールを止める強さで。
- subtitle: 表紙のサブコピー。40字以内。
- product_notes: {{item_code: 「こんな人に」の一文（40字以内）}} を全商品分。
- summary: まとめの一文。60字以内。
- narration_hook: 動画冒頭の読み上げ。40字以内。
- narration_products: {{item_code: 読み上げ（40字以内。商品名と特徴だけを自然な話し言葉で。価格や評価の数字は画面に出るので読まない）}} を全商品分。
- narration_outro: 締めの読み上げ。「プロフィールのリンク」「保存」に触れる。50字以内。
- caption_body: Instagram キャプション本文（300〜500字）。冒頭2行で続きを読みたくなる工夫。PR表記・リンク案内・ハッシュタグは書かない（システムが付ける）。
- caption_tiktok: TikTok 用。問いかけで終わる120字以内。
- hashtags_instagram: 5個まで。
- hashtags_tiktok: 5個まで。
"""

FORMAT_DESC = {
    "ranking": "楽天ランキング上位の比較",
    "price_band": "価格帯別のおすすめ",
    "spotlight": "注目の1台をほかの2台と比較",
    "guide": "選び方のポイント解説（例として3商品）",
}
HOOK_DESC = {
    "number": "数字型（例: ◯選、TOP◯）",
    "loss": "損失回避型（例: 買う前に見て、後悔しない）",
    "compare": "比較型（例: AとBどっち？）",
    "question": "問いかけ型（例: ◯◯で選んでる？）",
}


def build_prompt(plan: dict[str, Any]) -> str:
    lines = []
    for p in plan["products"]:
        lines.append(json.dumps({k: p[k] for k in ("item_code", "name", "price", "rank", "review_avg", "review_count", "features")},
                                ensure_ascii=False))
    if plan.get("tips"):
        lines.append("選び方のポイント: " + " / ".join(t["title"] for t in plan["tips"]))
    sig = plan.get("signal")
    return USER_TMPL.format(
        kind="カルーセル投稿" if plan["kind"] == "carousel" else "縦型ショート動画",
        format_desc=FORMAT_DESC[plan["format"]],
        genre=plan["genre_label"],
        hook_desc=HOOK_DESC[plan["hook_type"]],
        season=plan.get("season") or "なし",
        signal=f"{sig['kind']}: {sig['detail']}" if sig else "なし",
        products="\n".join(lines),
    )


def _parse(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    m = re.search(r"\{.*\}", raw, flags=re.S)
    return json.loads(m.group(0) if m else raw)


def generate_copy(settings: Settings, plan: dict[str, Any], recent_captions: list[str]) -> tuple[Copy, str, list[str]]:
    """(copy, provider_name, log_messages) を返す。"""
    notes: list[str] = []
    fallback = template_copy(plan)
    order = list(settings.get("llm.order", ["template"]))
    attempts = int(settings.get("llm.max_attempts_per_provider", 2))
    temperature = float(settings.get("llm.temperature", 0.8))
    if settings.sample_mode and not settings.env("AUTOPILOT_SAMPLE_USE_LLM"):
        order = ["template"]
    prompt = build_prompt(plan)
    for name in order:
        if name == "template":
            break
        fn = PROVIDERS.get(name)
        if not fn:
            continue
        for i in range(attempts):
            try:
                data = _parse(fn(SYSTEM, prompt, temperature))
                # 欠けた商品分はテンプレで補完
                data.setdefault("product_notes", {})
                data.setdefault("narration_products", {})
                for p in plan["products"]:
                    c = p["item_code"]
                    data["product_notes"].setdefault(c, fallback.product_notes[c])
                    data["narration_products"].setdefault(c, fallback.narration_products[c])
                copy = Copy(**data).clipped()
                problems = compliance.check_copy(settings, plan, copy, recent_captions)
                if problems:
                    notes.append(f"{name}#{i + 1}: 不合格 {problems[:3]}")
                    continue
                return copy, name, notes
            except ProviderUnavailable as e:
                notes.append(f"{name}: スキップ（{e}）")
                break
            except (ValidationError, ValueError, KeyError) as e:
                notes.append(f"{name}#{i + 1}: 出力不正 {str(e)[:120]}")
            except Exception as e:  # ネットワーク等
                notes.append(f"{name}#{i + 1}: エラー {str(e)[:120]}")
    problems = compliance.check_copy(settings, plan, fallback, recent_captions)
    if problems and any("似すぎ" not in p for p in problems):
        raise ValueError(f"テンプレ文もコンプライアンス検査に不合格: {problems}")
    if problems:  # 類似のみ → 本文の順序を変えて回避
        lines = fallback.caption_body.split("\n")
        fallback = fallback.model_copy(update={"caption_body": "\n".join([lines[0], *reversed(lines[1:])])})
    return fallback, "template", notes
