"""外部 API 部分（LLM / 楽天）を通信なしで検証する。"""
import json
import random

from autopilot.collectors import rakuten
from autopilot.collectors.sample import load_sample
from autopilot.llm import providers, router
from autopilot.planner import plan_post


def _good(plan):
    codes = [p["item_code"] for p in plan["products"]]
    return {
        "hook": "迷ったらこの比較", "subtitle": "スペックで見比べよう",
        "product_notes": {c: "毎日手軽に使いたい人に" for c in codes},
        "summary": "使い方に合わせて選んでね", "narration_hook": "迷ったらこの比較を見て。",
        "narration_products": {c: "機能のバランスが良いモデル。" for c in codes},
        "narration_outro": "リンクはプロフィールから。保存してね。",
        "caption_body": "今回はスペックの違いに注目して比べました。", "caption_tiktok": "どれが好き？",
        "hashtags_instagram": ["美容家電", "#比較"], "hashtags_tiktok": ["#美容家電"],
    }


def test_llm_output_used_when_compliant(settings, db, monkeypatch):
    load_sample(settings, db)
    plan = plan_post(settings, db, "carousel", random.Random(1))["plan"]
    monkeypatch.setenv("AUTOPILOT_SAMPLE_USE_LLM", "1")
    monkeypatch.setitem(providers.PROVIDERS, "gemini", lambda s, u, t: json.dumps(_good(plan), ensure_ascii=False))
    copy, provider, _ = router.generate_copy(settings, plan, [])
    assert provider == "gemini" and copy.hook == "迷ったらこの比較"
    assert copy.hashtags_instagram[0] == "#美容家電"


def test_llm_output_with_ng_words_falls_back(settings, db, monkeypatch):
    load_sample(settings, db)
    plan = plan_post(settings, db, "carousel", random.Random(1))["plan"]
    bad = _good(plan) | {"caption_body": "これを使えばシミが消える！しかも業界No.1"}
    monkeypatch.setenv("AUTOPILOT_SAMPLE_USE_LLM", "1")
    monkeypatch.setitem(providers.PROVIDERS, "gemini", lambda s, u, t: json.dumps(bad, ensure_ascii=False))
    copy, provider, notes = router.generate_copy(settings, plan, [])
    assert provider == "template"
    assert any("不合格" in n for n in notes)


def test_rakuten_collect_with_mocked_api(settings, db, monkeypatch):
    items = [{"rank": i, "itemName": f"【送料無料】テスト ドライヤー {i}号 大風量 速乾", "itemPrice": 5000 + i * 1000,
              "itemCode": f"shop:item{i}", "affiliateUrl": f"https://hb.afl.rakuten.co.jp/x{i}",
              "reviewCount": 100 * i, "reviewAverage": 4.2, "shopName": "s", "itemCaption": "マイナスイオン",
              "mediumImageUrls": [f"https://img/{i}.jpg?_ex=128x128"], "genreId": "123"} for i in range(1, 8)]
    items.append({**items[0], "itemCode": "shop:nozzle", "itemName": "ドライヤー 交換用ノズル 互換", "itemPrice": 1200})
    monkeypatch.setenv("RAKUTEN_APP_ID", "dummy")
    monkeypatch.setenv("AMAZON_ASSOCIATE_TAG", "me-22")
    monkeypatch.setattr(rakuten.RakutenClient, "_get", lambda self, path, params: {"Items": items})
    settings.genres = settings.genres[:1]
    stats = rakuten.collect(settings, db)
    assert stats["hair_dryer"] == 7  # 付属品・安価品は除外
    rows = db.latest_products("hair_dryer")
    assert rows[0]["short_name"].startswith("テスト ドライヤー")
    assert "tag=me-22" in rows[0]["amazon_url"]
    assert db.one("SELECT rakuten_genre_id FROM genre_ids WHERE genre_key='hair_dryer'")["rakuten_genre_id"] == "123"
