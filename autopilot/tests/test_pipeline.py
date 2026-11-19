"""パイプライン（ステートマシン・重複防止・リトライ・dry-run 投稿）のテスト。レンダリングはダミーに差し替え。"""
import pytest

from autopilot import pipeline
from autopilot.publish.instagram import InstagramPublisher


@pytest.fixture()
def fake_render(monkeypatch):
    def _render(settings, db, post):
        out = settings.output_dir / f"post_{post['post_no']:03d}"
        out.mkdir(parents=True, exist_ok=True)
        if post["kind"] == "carousel":
            names = []
            for i in range(3):
                (out / f"slide_{i + 1:02d}.jpg").write_bytes(b"jpg")
                names.append(f"slide_{i + 1:02d}.jpg")
            (out / "story.jpg").write_bytes(b"jpg")
            assets = {"slides": names, "story": "story.jpg"}
        else:
            (out / "reel.mp4").write_bytes(b"mp4" * 100)
            (out / "reel_cover.jpg").write_bytes(b"jpg")
            assets = {"video": "reel.mp4", "cover": "reel_cover.jpg", "seconds": 30, "voice": "silent"}
        from autopilot.llm.schema import Copy
        copy = Copy(**{k: v for k, v in post["script"].items() if k in Copy.model_fields})
        caps = pipeline.build_captions(settings, post["plan"], copy, post["post_no"], None)
        db.update_post(post["id"], script_json={**post["script"], "captions": caps, "assets": assets},
                       assets_dir=str(out), status="rendered")
    monkeypatch.setattr(pipeline, "stage_render", _render)


def test_generate_fills_buffer(settings, db, fake_render):
    summary = pipeline.generate(settings, db)
    assert summary["ready"] == {"carousel": 2, "reel": 2}
    # 2 回目はバッファが満タンなので新規企画しない
    assert pipeline.generate(settings, db)["planned"] == 0
    index = (settings.output_dir / "public" / "index.html").read_text(encoding="utf-8")
    assert "No.001" in index and "PR" in index


def test_captions_have_pr_and_post_number(settings, db, fake_render):
    pipeline.generate(settings, db)
    post = db.posts_by_status(["ready"], kind="carousel")[0]
    cap = post["script"]["captions"]
    assert cap["instagram"].startswith("PR｜")
    assert f"No.{post['post_no']:03d}" in cap["instagram"]
    assert cap["tiktok"].startswith("PR｜") and "#PR" in cap["tiktok"]


def test_publish_slots_and_no_duplicates(settings, db, fake_render, monkeypatch):
    pipeline.generate(settings, db)
    r1 = pipeline.publish(settings, db, "carousel")
    assert r1["kind"] == "carousel"
    # 同じスロットを同じ日にもう一度 → スキップ
    assert "skipped" in pipeline.publish(settings, db, "carousel")
    # force しても別の投稿が選ばれる（同じ投稿を二重に出さない）
    r2 = pipeline.publish(settings, db, "carousel", force=True)
    assert r2["post_no"] != r1["post_no"]
    # ストーリーは公開済みカルーセルを告知
    st = pipeline.publish(settings, db, "story")
    assert st["post_no"] in (r1["post_no"], r2["post_no"])
    rows = db.q("SELECT post_id, platform, kind, COUNT(*) c FROM publications GROUP BY 1,2,3")
    assert all(r["c"] == 1 for r in rows)


def test_tiktok_disabled_by_default_and_dry_run_when_enabled(settings, db, fake_render, monkeypatch):
    pipeline.generate(settings, db)
    assert "skipped" in pipeline.publish(settings, db, "tiktok")
    monkeypatch.setenv("TIKTOK_ENABLED", "true")
    r = pipeline.publish(settings, db, "tiktok")
    assert r["kind"] == "tiktok"


def test_auto_slot_resolution(settings, monkeypatch):
    monkeypatch.setenv("AUTOPILOT_NOW", "2026-11-19T12:40")
    assert pipeline.resolve_slot(settings, "auto")["name"] == "carousel"
    monkeypatch.setenv("AUTOPILOT_NOW", "2026-11-19T21:50")
    assert pipeline.resolve_slot(settings, "auto")["name"] == "reel"
    monkeypatch.setenv("AUTOPILOT_NOW", "2026-11-19T16:00")
    assert pipeline.resolve_slot(settings, "auto") is None


def test_failed_stage_is_retried_then_skipped(settings, db, monkeypatch):
    calls = {"n": 0}

    def boom(settings, db, post):
        calls["n"] += 1
        raise RuntimeError("render crashed")

    monkeypatch.setattr(pipeline, "stage_render", boom)
    settings.data["volume"]["buffer_days"] = 1
    pipeline.generate(settings, db)
    posts = db.posts_by_status(["scripted"])
    assert posts and all(p["attempts"] == 1 for p in posts)
    pipeline.generate(settings, db)
    pipeline.generate(settings, db)
    skipped = db.posts_by_status(["skipped"])
    assert len(skipped) == 2


def test_publish_failure_opens_breaker_after_three(settings, db, fake_render, monkeypatch):
    pipeline.generate(settings, db)

    def fail(*a, **k):
        raise RuntimeError("API down")

    monkeypatch.setattr(InstagramPublisher, "publish_reel", fail)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            pipeline.publish(settings, db, "reel", force=True)
    assert "サーキットブレーカー" in pipeline.publish(settings, db, "reel")["skipped"]


def test_instagram_carousel_request_sequence(settings):
    ig = InstagramPublisher(settings, None, dry_run=True)
    res = ig.publish_carousel(["https://x/1.jpg", "https://x/2.jpg"], "PR｜test")
    posts = [r for r in ig.requests_log if r["method"] == "POST"]
    assert [p["params"].get("is_carousel_item") for p in posts[:2]] == ["true", "true"]
    assert posts[2]["params"]["media_type"] == "CAROUSEL"
    assert posts[3]["path"].endswith("media_publish")
    assert res["media_id"]
