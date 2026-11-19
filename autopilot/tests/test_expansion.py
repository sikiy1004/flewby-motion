"""ジャンル拡張（美容 + 暮らし家電）・商品画像・BGM 選曲のテスト。"""
import random

from PIL import Image

from autopilot import media, pipeline
from autopilot.collectors.sample import load_sample
from autopilot.llm.template import template_copy
from autopilot.planner import pick_group, plan_post
from autopilot.video import bgm


def test_group_ratio_converges_to_settings(settings, db):
    load_sample(settings, db)
    rng = random.Random(1)
    groups = []
    for _ in range(10):
        g = pick_group(settings, db, rng)
        groups.append(g)
        genre = next(x for x in settings.genres if x.get("group") == g)
        db.exec("INSERT INTO posts (post_no, kind, format, genre_key, hook_type, theme, status, content_hash, plan_json, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (len(groups), "carousel", "ranking", genre["key"], "number", "kraft",
                                                  "ready", f"h{len(groups)}", "{}", "2026-11-19", "2026-11-19"))
    assert 5 <= groups.count("beauty") <= 9 and groups.count("qol") >= 1


def test_qol_post_uses_qol_hashtag(settings, db):
    load_sample(settings, db)
    settings.data["content"]["group_weights"] = {"qol": 1.0, "beauty": 0.0001}
    post = plan_post(settings, db, "carousel", random.Random(3))
    assert post["plan"]["group"] == "qol" and post["genre_key"] == "humidifier"
    assert "#便利家電" in template_copy(post["plan"]).hashtags_instagram


def test_product_photos_attached_and_square(settings, db):
    load_sample(settings, db)
    plan = plan_post(settings, db, "carousel", random.Random(2))["plan"]
    plan = media.attach_photos(settings, plan)
    photos = [p["photo"] for p in plan["products"]]
    assert all(photos)
    assert Image.open(photos[0]).size == (media.SIZE, media.SIZE)


def test_missing_photo_falls_back(settings):
    assert media.fetch_image(settings, "sample/images/does-not-exist.jpg") is None
    assert media.fetch_image(settings, None) is None


def test_bgm_rotation_and_credit(settings, monkeypatch, tmp_path):
    root = tmp_path / "assets"
    (root / "bgm" / "upbeat").mkdir(parents=True)
    for n in ("a", "b", "c", "d"):
        (root / "bgm" / "upbeat" / f"{n}.wav").write_bytes(b"RIFF")
    (root / "bgm" / "bgm.yaml").write_text(
        "tracks:\n  - {file: upbeat/a.wav, mood: upbeat, start: 3, credit: 'BGM: A by X'}\n", encoding="utf-8")
    monkeypatch.setattr(type(settings), "assets_dir", property(lambda self: root))
    tracks = bgm.load_tracks(settings)
    assert len(tracks) == 4 and next(t for t in tracks if t["file"] == "upbeat/a.wav")["credit"] == "BGM: A by X"
    rng = random.Random(0)
    picks = [bgm.choose_track(settings, "ranking", rng)["file"] for _ in range(4)]
    assert len(set(picks)) == 4  # 直近 3 本は再利用しない


def test_caption_credits_lines(settings, db):
    load_sample(settings, db)
    plan = plan_post(settings, db, "reel", random.Random(2))["plan"]
    caps = pipeline.build_captions(settings, plan, template_copy(plan), 7, ["音声: VOICEVOX:冥鳴ひまり", "BGM: A by X"])
    assert "音声: VOICEVOX:冥鳴ひまり" in caps["instagram"] and "BGM: A by X" in caps["instagram"]
    assert "BGM: A by X" in caps["tiktok"]
