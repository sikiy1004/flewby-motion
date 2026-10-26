"""スクリプト共通の小さなユーティリティ（標準ライブラリのみ）。"""
import csv
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
INDEX = ARTICLES / "index.csv"
IDEAS = ROOT / "ideas" / "backlog" / "ideas.csv"
SALES = ROOT / "analytics" / "sales" / "sales.csv"
REPORTS = ROOT / "analytics" / "reports"

PAYWALL = "<!-- PAYWALL -->"
PAYWALL_NOTE_LINE = "――――― ここから有料 ―――――"
INDEX_FIELDS = [
    "slug", "idea_id", "genre_id", "title", "title_type", "status", "price_yen",
    "created", "production_minutes", "quality_score", "approved_by", "approved_at",
    "published_at", "note_url",
]
STATUSES = ["draft", "in_review", "awaiting_approval", "approved", "published", "needs_human", "rejected"]


def today():
    return datetime.date.today().isoformat()


def read_csv(path):
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def split_front_matter(text):
    """'---' で囲まれた front matter を (dict, 本文) に分ける。値は文字列のまま扱う。"""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, text[end + 5:]


def set_front_matter(text, updates):
    """front matter の既存キーを書き換え、無いキーは末尾に足す。"""
    if not text.startswith("---\n"):
        raise ValueError("front matter がありません")
    end = text.find("\n---\n", 4)
    lines = text[4:end].splitlines()
    remaining = dict(updates)
    for i, line in enumerate(lines):
        key = line.partition(":")[0].strip()
        if key in remaining and not line.startswith((" ", "-")):
            lines[i] = f"{key}: {remaining.pop(key)}"
    lines += [f"{k}: {v}" for k, v in remaining.items()]
    return "---\n" + "\n".join(lines) + text[end:]


def to_int(value, default=0):
    try:
        return int(str(value).replace(",", "").strip())
    except ValueError:
        return default
