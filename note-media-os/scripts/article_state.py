#!/usr/bin/env python3
"""記事の登録とステータス管理（articles/index.csv と下書きの front matter を同期する）。

使い方:
  python3 scripts/article_state.py register <slug> <idea_id> <genre_id> <title_type> <price_yen> "<title>"
  python3 scripts/article_state.py status <slug> <draft|in_review|needs_human|rejected>
  python3 scripts/article_state.py score <slug> <quality_score>
  python3 scripts/article_state.py minutes <slug> <制作時間（分）>
  python3 scripts/article_state.py approve <slug> "<承認者名>"      # 人間の承認（/approve-article から呼ぶ）
  python3 scripts/article_state.py published <slug> <note_url> [YYYY-MM-DD]  # 公開済みの記録（/mark-published から呼ぶ）
  python3 scripts/article_state.py list [status]

awaiting_approval への変更は export_note.py が行う。approved と published は、
人間の操作（approve / published サブコマンド）でしか設定できない。
"""
import shutil
import sys

from common import (ARTICLES, IDEAS, INDEX, INDEX_FIELDS, read_csv, set_front_matter,
                    split_front_matter, to_int, today, write_csv)

MANUAL_STATUSES = {"draft", "in_review", "needs_human", "rejected"}


def load_index():
    _, rows = read_csv(INDEX)
    return rows


def find(rows, slug):
    for row in rows:
        if row["slug"] == slug:
            return row
    sys.exit(f"{slug} は articles/index.csv に登録されていません")


def draft_path(slug):
    return ARTICLES / "drafts" / f"{slug}.md"


def sync_draft(slug, updates):
    path = draft_path(slug)
    if path.exists():
        path.write_text(set_front_matter(path.read_text(encoding="utf-8"), updates), encoding="utf-8")


def set_idea_status(idea_id, status):
    fields, rows = read_csv(IDEAS)
    for row in rows:
        if row["id"] == idea_id:
            row["status"] = status
    if rows:
        write_csv(IDEAS, fields, rows)


def cmd_register(slug, idea_id, genre_id, title_type, price, title):
    rows = load_index()
    if any(r["slug"] == slug for r in rows):
        sys.exit(f"{slug} は登録済みです")
    rows.append({
        "slug": slug, "idea_id": idea_id, "genre_id": genre_id, "title": title,
        "title_type": title_type, "status": "draft", "price_yen": price, "created": today(),
    })
    write_csv(INDEX, INDEX_FIELDS, rows)
    if idea_id and idea_id != "-":
        set_idea_status(idea_id, "in_production")
    print(f"登録しました: {slug}")


def cmd_status(slug, status):
    if status not in MANUAL_STATUSES:
        sys.exit(f"status で設定できるのは {sorted(MANUAL_STATUSES)} だけです")
    rows = load_index()
    find(rows, slug)["status"] = status
    write_csv(INDEX, INDEX_FIELDS, rows)
    sync_draft(slug, {"status": status, "updated": today()})
    print(f"{slug}: {status}")


def cmd_field(slug, field, value):
    rows = load_index()
    find(rows, slug)[field] = value
    write_csv(INDEX, INDEX_FIELDS, rows)
    if field == "quality_score":
        sync_draft(slug, {"quality_score": value})
    print(f"{slug}: {field}={value}")


def cmd_approve(slug, approver):
    rows = load_index()
    row = find(rows, slug)
    if row["status"] != "awaiting_approval":
        sys.exit(f"{slug} は承認待ちではありません（現在: {row['status']}）")
    if not (ARTICLES / "ready_to_publish" / f"{slug}.note.md").exists():
        sys.exit("投稿用ファイルがありません。先に export_note.py を実行してください")
    row.update(status="approved", approved_by=approver, approved_at=today())
    write_csv(INDEX, INDEX_FIELDS, rows)
    sync_draft(slug, {"status": "approved", "approved_by": approver, "approved_at": today()})
    print(f"{slug} を承認しました（{approver}、{today()}）。noteへの公開は人間が手動で行ってください")


def cmd_published(slug, url, date=None):
    rows = load_index()
    row = find(rows, slug)
    if row["status"] != "approved" or not row.get("approved_by"):
        sys.exit(f"{slug} は承認されていません。公開済みとして記録できません")
    if "note.com" not in url:
        sys.exit("note の記事URLを指定してください")
    row.update(status="published", published_at=date or today(), note_url=url)
    write_csv(INDEX, INDEX_FIELDS, rows)
    sync_draft(slug, {"status": "published"})
    dest = ARTICLES / "published" / slug
    dest.mkdir(parents=True, exist_ok=True)
    for src in [draft_path(slug), *(ARTICLES / "ready_to_publish").glob(f"{slug}.*")]:
        if src.exists():
            shutil.move(str(src), dest / src.name)
    set_idea_status(row["idea_id"], "published")
    print(f"{slug} を公開済みとして記録し、ファイルを {dest.relative_to(ARTICLES.parent)} に移しました")


def cmd_list(status=None):
    for row in load_index():
        if status is None or row["status"] == status:
            print(f"{row['status']:<18} {row['slug']:<16} {to_int(row['price_yen']):>4}円  {row['title']}")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd = a[0]
    if cmd == "register" and len(a) == 7:
        cmd_register(*a[1:])
    elif cmd == "status" and len(a) == 3:
        cmd_status(a[1], a[2])
    elif cmd == "score" and len(a) == 3:
        cmd_field(a[1], "quality_score", a[2])
    elif cmd == "minutes" and len(a) == 3:
        cmd_field(a[1], "production_minutes", a[2])
    elif cmd == "approve" and len(a) == 3:
        cmd_approve(a[1], a[2])
    elif cmd == "published" and len(a) in (3, 4):
        cmd_published(*a[1:])
    elif cmd == "list":
        cmd_list(a[1] if len(a) > 1 else None)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
