import random

from autopilot import compliance
from autopilot.collectors import clean_name, extract_features
from autopilot.collectors.sample import load_sample
from autopilot.collectors.trends import detect_product_signals
from autopilot.llm.router import generate_copy
from autopilot.llm.template import template_copy
from autopilot.planner import plan_post
from autopilot.video.subtitles import split_caption


def test_clean_name_removes_marketing_noise():
    name = "【楽天1位】ドライヤー 大風量 速乾 送料無料 ポイント10倍 マイナスイオン ★レビュー特典"
    s = clean_name(name)
    assert "送料無料" not in s and "楽天1位" not in s and "ポイント" not in s
    assert len(s) <= 26


def test_extract_features():
    feats = extract_features("大風量 マイナスイオン 軽量", {"大風量": "大風量", "マイナスイオン": "マイナスイオン", "温冷": "温冷切替"})
    assert feats == ["大風量", "マイナスイオン"]


def test_ng_words_detected(settings):
    bad = ["これでシミが消える！", "医療レベルの仕上がり", "必ずキレイに", "業界No.1の実力", "今だけ30%OFF"]
    for t in bad:
        assert compliance.ng_violations(settings, [t]), t
    ok = ["No.042 はプロフのリンクから", "「大風量」「速乾」を重視する人に"]
    assert compliance.ng_violations(settings, ok) == []


def test_number_fabrication_detected(settings, db):
    load_sample(settings, db)
    post = plan_post(settings, db, "carousel", random.Random(1))
    plan = post["plan"]
    p = plan["products"][0]
    assert compliance.number_violations(plan, [f"{p['name']}は{p['price']:,}円"]) == []
    assert compliance.number_violations(plan, ["今なら12,345円"])


def test_final_caption_requires_pr(settings):
    assert compliance.check_final_caption(settings, "PR｜比較しました") == []
    assert compliance.check_final_caption(settings, "比較しました #PR")


def test_template_copy_passes_compliance_for_all_formats(settings, db):
    load_sample(settings, db)
    detect_product_signals(settings, db)
    rng = random.Random(0)
    seen = set()
    for _ in range(12):
        for kind in ("carousel", "reel"):
            try:
                post = plan_post(settings, db, kind, rng)
            except Exception:
                continue
            plan = post["plan"]
            for hook in ("number", "loss", "compare", "question"):
                copy = template_copy({**plan, "hook_type": hook})
                assert compliance.check_copy(settings, plan, copy, []) == [], (plan["format"], hook)
            seen.add(plan["format"])
    assert {"ranking", "price_band", "spotlight", "guide"} <= seen


def test_router_falls_back_to_template_without_keys(settings, db):
    load_sample(settings, db)
    post = plan_post(settings, db, "carousel", random.Random(2))
    copy, provider, _ = generate_copy(settings, post["plan"], [])
    assert provider == "template"
    assert set(copy.narration_products) == {p["item_code"] for p in post["plan"]["products"]}


def test_planner_never_duplicates(settings, db):
    load_sample(settings, db)
    hashes = set()
    rng = random.Random(5)
    for _ in range(8):
        try:
            post = plan_post(settings, db, "carousel", rng)
        except Exception:
            break
        assert post["content_hash"] not in hashes
        hashes.add(post["content_hash"])
    nos = [r["post_no"] for r in db.q("SELECT post_no FROM posts ORDER BY id")]
    assert nos == list(range(1, len(nos) + 1))


def test_price_drop_and_rank_up_signals(settings, db):
    load_sample(settings, db)
    assert detect_product_signals(settings, db) >= 2
    kinds = {r["kind"] for r in db.q("SELECT kind FROM signals")}
    assert {"rank_up", "price_drop"} <= kinds


def test_subtitle_split_is_short():
    chunks = split_caption("1万円以下なら、Pureskin イオン導入美顔器。イオン導入と温冷が特徴です。")
    assert chunks and all(len(c) <= 17 for c in chunks)
    assert all(not c.endswith("。") for c in chunks)
