"""オーケストレーター：generate（収集→企画→台本→検査→レンダリング→公開URL化）/ publish / maintain。

投稿はステートマシンで管理し、失敗した段階から次回の実行で再開する。
  planned → scripted → rendered → ready → published
  （各段階で失敗 → attempts+1。3回失敗で skipped にして通知）
"""
from __future__ import annotations

import json
import logging
import random
import secrets
import shutil
import tempfile
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from . import compliance
from .collectors import rakuten, trends
from .collectors.sample import load_sample
from .config import Settings, now_jst
from .db import DB
from .linkpage import build_linkpage
from .llm.router import generate_copy
from .llm.schema import Copy
from .notify import notify
from .planner import NoCandidate, plan_post, reward_arm
from .publish.instagram import InstagramPublisher
from .publish.media_host import get_host
from .publish.tiktok import TikTokPublisher
from .tokens import TokenStore

log = logging.getLogger(__name__)
MAX_ATTEMPTS = 3


# ======================================================================
# captions
# ======================================================================
def build_captions(settings: Settings, plan: dict[str, Any], copy: Copy, post_no: int, credit: str | None) -> dict[str, str]:
    req = settings.ng.get("required", {})
    disclaimer = req.get("price_disclaimer", "").format(date=plan["date_label"])
    no = f"No.{post_no:03d}"
    n_tags = int(settings.get("content.hashtags_max", 5))
    tags_ig = " ".join(copy.hashtags_instagram[:n_tags])
    tags_tt = " ".join(["#PR", *copy.hashtags_tiktok[: n_tags - 1]])
    lines = [f"{req.get('caption_prefix', 'PR')}｜{copy.hook}", "", copy.caption_body.strip(), "",
             f"📌 紹介した商品のリンクはプロフィールのリンク → {no}", disclaimer]
    if credit:
        lines.append(f"音声: {credit}")
    lines += ["", tags_ig]
    ig = "\n".join(lines).strip()
    tt = f"PR｜{copy.caption_tiktok.strip()} 商品はプロフのリンク {no} {tags_tt}"
    if credit:
        tt += f" 音声:{credit}"
    return {"instagram": ig, "tiktok": tt[:2200]}


# ======================================================================
# generate
# ======================================================================
def collect(settings: Settings, db: DB, force: bool = False) -> dict[str, Any]:
    today = now_jst().date().isoformat()
    if not force and db.kv_get("last_collect") == today:
        return {"skipped": "already collected today"}
    if settings.sample_mode:
        stats: dict[str, Any] = {"sample": load_sample(settings, db)}
    else:
        stats = {"rakuten": rakuten.collect(settings, db), "rss": trends.collect_rss(settings, db)}
    stats["signals"] = trends.detect_product_signals(settings, db)
    db.kv_set("last_collect", today)
    return stats


def _fail(db: DB, post: dict[str, Any], stage: str, err: Exception) -> None:
    attempts = post["attempts"] + 1
    msg = f"[{stage}] {type(err).__name__}: {err}"
    log.error("post No.%03d %s", post["post_no"], msg)
    log.debug(traceback.format_exc())
    status = "skipped" if attempts >= MAX_ATTEMPTS else post["status"]
    db.update_post(post["id"], attempts=attempts, last_error=msg[:2000], status=status)
    if status == "skipped":
        notify(f"No.{post['post_no']:03d} をスキップしました", msg[:1500], "warn")


def stage_script(settings: Settings, db: DB, post: dict[str, Any]) -> None:
    plan = post["plan"]
    copy, provider, notes = generate_copy(settings, plan, db.recent_captions())
    script = copy.model_dump()
    script["llm_notes"] = notes
    db.update_post(post["id"], script_json=script, llm_provider=provider, status="scripted")


def stage_render(settings: Settings, db: DB, post: dict[str, Any]) -> None:
    from .render.carousel import render_carousel, render_story
    from .video.composer import render_video

    plan, copy = post["plan"], Copy(**{k: v for k, v in post["script"].items() if k in Copy.model_fields})
    out = settings.output_dir / f"post_{post['post_no']:03d}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    credit = None
    assets: dict[str, Any] = {}
    if post["kind"] == "carousel":
        slides = render_carousel(settings, plan, copy, post["post_no"], out)
        story = render_story(settings, plan, copy, post["post_no"], out)
        assets = {"slides": [s.name for s in slides], "story": story.name}
    else:
        v = render_video(settings, plan, copy, post["post_no"], out, rng=random.Random(post["post_no"]))
        credit = v["credit"]
        assets = {"video": v["video"].name, "cover": v["cover"].name, "seconds": v["seconds"], "voice": v["voice"]}
    captions = build_captions(settings, plan, copy, post["post_no"], credit)
    problems = compliance.check_final_caption(settings, captions["instagram"])
    problems += compliance.ng_violations(settings, [captions["instagram"], captions["tiktok"]])
    if problems:
        raise ValueError(f"キャプション検査に不合格: {problems}")
    (out / "caption_instagram.txt").write_text(captions["instagram"], encoding="utf-8")
    (out / "caption_tiktok.txt").write_text(captions["tiktok"], encoding="utf-8")
    script = {**post["script"], "captions": captions, "assets": assets}
    db.update_post(post["id"], script_json=script, assets_dir=str(out), status="rendered")


def stage_host(settings: Settings, db: DB, posts: list[dict[str, Any]]) -> None:
    """rendered の投稿のメディアとリンク集ページを、まとめて 1 回で公開する。"""
    host = get_host(settings)
    files: dict[str, Any] = {}
    media_by_post: dict[int, dict[str, Any]] = {}
    for post in posts:
        out = Path(post["assets_dir"])
        assets = post["script"]["assets"]
        rel = f"m/{post['post_no']:03d}-{secrets.token_hex(4)}"
        media: dict[str, Any] = {"dir": rel}
        if post["kind"] == "carousel":
            media["slides"] = []
            for name in assets["slides"]:
                files[f"{rel}/{name}"] = out / name
                media["slides"].append(host.url(f"{rel}/{name}"))
            files[f"{rel}/{assets['story']}"] = out / assets["story"]
            media["story"] = host.url(f"{rel}/{assets['story']}")
        else:
            for key in ("video", "cover"):
                files[f"{rel}/{assets[key]}"] = out / assets[key]
                media[key] = host.url(f"{rel}/{assets[key]}")
        media_by_post[post["id"]] = media
    for pid, media in media_by_post.items():
        db.update_post(pid, media_json=media, status="ready")
    files["index.html"] = build_linkpage(settings, db)
    try:
        host.sync(files, message=f"autopilot: {len(posts)} posts")
    except Exception:
        for pid in media_by_post:  # 公開に失敗したら rendered に戻して次回再試行
            db.update_post(pid, status="rendered", media_json=None)
        raise


def generate(settings: Settings, db: DB, *, max_new: int | None = None) -> dict[str, Any]:
    run = db.start_run("generate")
    summary: dict[str, Any] = {}
    status = "error"
    try:
        summary["collect"] = collect(settings, db)
        buffer_days = int(settings.get("volume.buffer_days", 2))
        created = 0
        for kind, per_day in (("carousel", settings.get("volume.carousel_per_day", 1)),
                              ("reel", settings.get("volume.reel_per_day", 1))):
            target = int(per_day) * buffer_days
            pending = db.posts_by_status(["planned", "scripted", "rendered", "ready"], kind=kind)
            for _ in range(max(0, target - len(pending))):
                if max_new is not None and created >= max_new:
                    break
                try:
                    plan_post(settings, db, kind)
                    created += 1
                except NoCandidate as e:
                    summary.setdefault("notes", []).append(f"{kind}: {e}")
                    break
        summary["planned"] = created

        for stage, fn in (("planned", stage_script), ("scripted", stage_render)):
            for post in db.posts_by_status([stage]):
                try:
                    fn(settings, db, post)
                except Exception as e:
                    _fail(db, post, stage, e)

        rendered = db.posts_by_status(["rendered"])
        if rendered:
            try:
                stage_host(settings, db, rendered)
            except Exception as e:
                for post in rendered:
                    _fail(db, db.get_post(post["id"]), "host", e)
        summary["ready"] = {k: len(db.posts_by_status(["ready"], kind=k)) for k in ("carousel", "reel")}
        status = "ok"
        if summary["ready"]["carousel"] == 0 or summary["ready"]["reel"] == 0:
            notify("投稿バッファが空です", json.dumps(summary, ensure_ascii=False)[:1500], "warn")
        return summary
    except Exception as e:
        notify("generate が失敗しました", f"{type(e).__name__}: {e}", "error")
        raise
    finally:
        db.finish_run(run, status, json.dumps(summary, ensure_ascii=False, default=str))


# ======================================================================
# publish
# ======================================================================
def resolve_slot(settings: Settings, name: str) -> dict[str, Any] | None:
    slots = settings.get("slots", [])
    if name != "auto":
        return next((s for s in slots if s["name"] == name), None)
    now = now_jst()
    tol = int(settings.get("slot_tolerance_minutes", 90))
    best, best_diff = None, None
    for s in slots:
        hh, mm = map(int, s["time"].split(":"))
        t = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        diff = (now - t).total_seconds() / 60
        if -10 <= diff <= tol and (best_diff is None or abs(diff) < best_diff):
            best, best_diff = s, abs(diff)
    return best


def _breaker_open(db: DB) -> bool:
    until = db.kv_get("breaker_until")
    return bool(until and datetime.fromisoformat(until) > now_jst())


def _record_result(db: DB, ok: bool, msg: str) -> None:
    if ok:
        db.kv_set("consecutive_failures", "0")
        return
    n = int(db.kv_get("consecutive_failures", "0") or 0) + 1
    db.kv_set("consecutive_failures", str(n))
    if n >= 3:
        until = now_jst() + timedelta(hours=24)
        db.kv_set("breaker_until", until.isoformat())
        notify("投稿を24時間停止しました（3回連続失敗）", msg, "error")


def _local_video(post: dict[str, Any]) -> Path:
    if post.get("assets_dir"):
        p = Path(post["assets_dir"]) / post["script"]["assets"]["video"]
        if p.exists():
            return p
    url = post["media"]["video"]
    tmp = Path(tempfile.mkdtemp()) / "reel.mp4"
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(1 << 16):
                fh.write(chunk)
    return tmp


def publish(settings: Settings, db: DB, slot_name: str = "auto", *, force: bool = False) -> dict[str, Any]:
    slot = resolve_slot(settings, slot_name)
    if not slot:
        return {"skipped": f"該当する投稿スロットがありません（{slot_name}）"}
    today = now_jst().date().isoformat()
    if not force and db.one("SELECT 1 FROM slot_runs WHERE date=? AND slot=? AND status='done'", (today, slot["name"])):
        return {"skipped": f"{slot['name']} は本日実行済み"}
    if not settings.platform_enabled(slot["platform"]):
        return {"skipped": f"{slot['platform']} は無効です"}
    if _breaker_open(db) and not force:
        return {"skipped": "サーキットブレーカー作動中"}

    tokens = TokenStore(db)
    dry = settings.dry_run
    result: dict[str, Any] = {"slot": slot["name"], "dry_run": dry}
    post: dict[str, Any] | None = None
    try:
        if slot["platform"] == "instagram":
            ig = InstagramPublisher(settings, tokens, dry_run=dry)
            if slot["kind"] == "story":
                rows = db.q("SELECT p.id FROM posts p JOIN publications pub ON pub.post_id=p.id "
                            "WHERE pub.platform='instagram' AND pub.kind='carousel' AND pub.status IN ('published','dry_run') "
                            "AND NOT EXISTS (SELECT 1 FROM publications s WHERE s.post_id=p.id AND s.kind='story') "
                            "ORDER BY p.post_no DESC LIMIT 1")
                if not rows:
                    return {**result, "skipped": "告知するカルーセルがありません"}
                post = db.get_post(rows[0]["id"])
            else:
                cands = [p for p in db.posts_by_status(["ready"], kind=slot["kind"])
                         if not db.get_publication(p["id"], "instagram", slot["kind"])
                         or db.get_publication(p["id"], "instagram", slot["kind"])["status"] in ("failed", "publishing")]
                if not cands:
                    notify("投稿できるコンテンツがありません", f"slot={slot['name']}", "warn")
                    return {**result, "skipped": "ready の投稿がありません"}
                post = cands[0]
            kind = slot["kind"]
            media = post["media"]
            urls = media["slides"] if kind == "carousel" else ([media["story"]] if kind == "story" else [media["video"]])
            if not dry and not get_host(settings).wait_available(urls[:1], timeout=240):
                raise RuntimeError("メディア URL がまだ公開されていません（GitHub Pages の反映待ち）")
            if not dry and ig.quota_left() < 1:
                raise RuntimeError("Instagram の24時間あたりの投稿上限に達しています")
            marker = f"No.{post['post_no']:03d}"
            prev = db.get_publication(post["id"], "instagram", kind)
            existing = ig.find_existing(marker) if (prev and prev["status"] == "publishing" and kind != "story") else None
            if existing:
                res = existing
            else:
                db.upsert_publication(post["id"], "instagram", kind, status="publishing",
                                      attempts=(prev or {}).get("attempts", 0) + 1)
                caption = post["script"]["captions"]["instagram"]
                if kind == "carousel":
                    res = ig.publish_carousel(media["slides"], caption)
                elif kind == "reel":
                    res = ig.publish_reel(media["video"], caption, media.get("cover"))
                else:
                    res = ig.publish_story(media["story"])
            db.upsert_publication(post["id"], "instagram", kind, status="dry_run" if dry else "published",
                                  container_id=res.get("container_id"), media_id=res.get("media_id"),
                                  permalink=res.get("permalink"), published_at=now_jst().isoformat(), error=None)
            if kind != "story":
                db.update_post(post["id"], status="published")
            if dry:
                _dump_dry(settings, post, f"instagram_{kind}", ig.requests_log)
            result.update({"post_no": post["post_no"], "kind": kind, **{k: res.get(k) for k in ("media_id", "permalink")}})
        else:  # tiktok
            tt = TikTokPublisher(settings, tokens, dry_run=dry)
            since = (now_jst() - timedelta(days=5)).isoformat()
            cands = [p for p in db.posts_by_status(["ready", "published"], kind="reel")
                     if p["created_at"] >= since and p.get("media")
                     and (not db.get_publication(p["id"], "tiktok", "reel")
                          or db.get_publication(p["id"], "tiktok", "reel")["status"] == "failed")]
            if not cands:
                return {**result, "skipped": "TikTok に投稿する動画がありません"}
            post = cands[0]
            db.upsert_publication(post["id"], "tiktok", "reel", status="publishing")
            res = tt.publish_video(_local_video(post), post["script"]["captions"]["tiktok"])
            db.upsert_publication(post["id"], "tiktok", "reel", status="dry_run" if dry else "published",
                                  container_id=res.get("container_id"), media_id=res.get("media_id"),
                                  published_at=now_jst().isoformat(), error=None)
            if dry:
                _dump_dry(settings, post, "tiktok", tt.requests_log)
            result.update({"post_no": post["post_no"], "kind": "tiktok", "privacy": res.get("privacy")})
        db.exec("INSERT OR REPLACE INTO slot_runs (date, slot, status, detail) VALUES (?,?,?,?)",
                (today, slot["name"], "done", json.dumps(result, ensure_ascii=False)))
        _record_result(db, True, "")
        return result
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        if post:
            kind = slot["kind"] if slot["platform"] == "instagram" else "reel"
            pub = db.get_publication(post["id"], slot["platform"], kind)
            # API 呼び出し前後どちらで落ちたか不明なので publishing のまま残し、次回 find_existing で照合
            db.upsert_publication(post["id"], slot["platform"], kind,
                                  status="publishing" if pub and pub["status"] == "publishing" else "failed",
                                  error=msg[:1000])
            pub = db.get_publication(post["id"], slot["platform"], kind)
            if pub and pub["attempts"] >= MAX_ATTEMPTS and slot["platform"] == "instagram" and kind != "story":
                db.update_post(post["id"], status="skipped", last_error=msg[:2000])
                notify(f"No.{post['post_no']:03d} の投稿を諦めました（{MAX_ATTEMPTS}回失敗）", msg[:1500], "warn")
        db.exec("INSERT OR REPLACE INTO slot_runs (date, slot, status, detail) VALUES (?,?,?,?)",
                (today, slot["name"], "failed", msg[:1000]))
        _record_result(db, False, msg)
        notify(f"投稿失敗: {slot['name']}", msg[:1500], "error")
        raise


def _dump_dry(settings: Settings, post: dict[str, Any], name: str, log_: list[dict[str, Any]]) -> None:
    out = Path(post.get("assets_dir") or settings.output_dir) / f"dryrun_{name}.json"
    out.write_text(json.dumps(log_, ensure_ascii=False, indent=2), encoding="utf-8")


# ======================================================================
# maintain
# ======================================================================
def maintain(settings: Settings, db: DB) -> dict[str, Any]:
    run = db.start_run("maintain")
    tokens = TokenStore(db)
    now = now_jst()
    out: dict[str, Any] = {"insights": 0, "rewards": 0, "cleaned": 0}
    ig = InstagramPublisher(settings, tokens, dry_run=settings.dry_run)

    # 1) インサイト取得（直近14日）
    since = (now - timedelta(days=14)).isoformat()
    pubs = db.q("SELECT * FROM publications WHERE platform='instagram' AND status='published' AND kind!='story' "
                "AND published_at >= ?", (since,))
    for pub in pubs:
        try:
            m = ig.insights(pub["media_id"], pub["kind"])
        except Exception as e:
            log.warning("insights %s: %s", pub["media_id"], e)
            continue
        db.exec("INSERT OR REPLACE INTO metrics VALUES (?,?,?,?,?,?,?,?)",
                (pub["id"], now.date().isoformat(), m.get("reach"), m.get("views"), m.get("likes"),
                 m.get("comments"), m.get("saved"), m.get("shares")))
        out["insights"] += 1

    # 2) 学習（公開から3日以上経った投稿の成績で arm を更新）
    rows = db.q("""SELECT pub.id, p.format, p.hook_type, p.theme, m.reach, m.saves, m.shares
                   FROM publications pub JOIN posts p ON p.id = pub.post_id
                   JOIN metrics m ON m.publication_id = pub.id
                   WHERE pub.platform='instagram' AND pub.kind!='story' AND pub.published_at <= ?
                     AND pub.id NOT IN (SELECT publication_id FROM rewarded)
                   GROUP BY pub.id HAVING m.fetched_at = MAX(m.fetched_at)""", ((now - timedelta(days=3)).isoformat(),))
    for r in rows:
        reach = r["reach"] or 0
        if reach < 50:
            continue
        rate = ((r["saves"] or 0) + 1.5 * (r["shares"] or 0)) / reach
        reward = min(1.0, rate / 0.03)  # 保存+シェア率 3% を満点とする
        for dim, opt in (("format", r["format"]), ("hook", r["hook_type"]), ("theme", r["theme"])):
            reward_arm(db, dim, opt, reward)
        db.exec("INSERT INTO rewarded VALUES (?)", (r["id"],))
        out["rewards"] += 1

    # 3) トークン更新（Instagram: 6日ごと）
    last = db.kv_get("ig_token_refreshed")
    if settings.platform_enabled("instagram") and not settings.dry_run and \
            (not last or datetime.fromisoformat(last) < now - timedelta(days=6)):
        try:
            if ig.refresh_token():
                db.kv_set("ig_token_refreshed", now.isoformat())
                out["ig_token"] = "refreshed"
        except Exception as e:
            notify("Instagram トークンの更新に失敗", str(e), "error")

    # 4) 公開済みメディアの削除（リンク集ページは残す）
    keep = int(settings.get("media_host.keep_days_after_publish", 7))
    old = [p for p in db.posts_by_status(["published", "skipped"])
           if p.get("media") and not p["media"].get("deleted") and p["updated_at"] < (now - timedelta(days=keep)).isoformat()]
    if old:
        try:
            host = get_host(settings)
            host.sync({"index.html": build_linkpage(settings, db)}, deletes=[p["media"]["dir"] for p in old],
                      message=f"autopilot: cleanup {len(old)}")
            for p in old:
                db.update_post(p["id"], media_json={**p["media"], "deleted": True})
            out["cleaned"] = len(old)
        except Exception as e:
            log.warning("cleanup failed: %s", e)

    # 5) 週次レポート
    if now.weekday() == int(settings.get("notify.weekly_report_weekday", 0)) and db.kv_get("weekly_report") != now.date().isoformat():
        notify("週次レポート", weekly_report(db), "info")
        db.kv_set("weekly_report", now.date().isoformat())

    db.finish_run(run, "ok", json.dumps(out, ensure_ascii=False))
    return out


def weekly_report(db: DB) -> str:
    since = (now_jst() - timedelta(days=7)).isoformat()
    pubs = db.q("SELECT platform, kind, status, COUNT(*) c FROM publications WHERE created_at >= ? GROUP BY 1,2,3", (since,))
    lines = [f"- {r['platform']}/{r['kind']} {r['status']}: {r['c']}" for r in pubs] or ["- 投稿なし"]
    top = db.q("""SELECT p.post_no, p.format, MAX(m.reach) reach, MAX(m.saves) saves FROM metrics m
                  JOIN publications pub ON pub.id=m.publication_id JOIN posts p ON p.id=pub.post_id
                  WHERE m.fetched_at >= ? GROUP BY p.id ORDER BY saves DESC LIMIT 3""", (since[:10],))
    if top:
        lines.append("上位（保存数）:")
        lines += [f"  No.{r['post_no']:03d} {r['format']} reach={r['reach']} saves={r['saves']}" for r in top]
    ready = db.one("SELECT COUNT(*) c FROM posts WHERE status='ready'")["c"]
    skipped = db.one("SELECT COUNT(*) c FROM posts WHERE status='skipped' AND updated_at >= ?", (since,))["c"]
    lines.append(f"バッファ: {ready}件 / 今週スキップ: {skipped}件")
    return "\n".join(lines)
