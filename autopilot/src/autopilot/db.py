"""SQLite による状態管理（商品・投稿ステートマシン・投稿実績・学習・トークン）。"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .config import now_jst

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  item_code TEXT NOT NULL UNIQUE,
  genre_key TEXT NOT NULL,
  name TEXT NOT NULL,
  short_name TEXT NOT NULL,
  shop TEXT,
  caption TEXT,
  image_url TEXT,
  affiliate_url TEXT,
  amazon_url TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product_snapshots (
  product_id INTEGER NOT NULL REFERENCES products(id),
  date TEXT NOT NULL,
  price INTEGER,
  rank INTEGER,
  review_count INTEGER,
  review_avg REAL,
  PRIMARY KEY (product_id, date)
);

CREATE TABLE IF NOT EXISTS genre_ids (
  genre_key TEXT PRIMARY KEY,
  rakuten_genre_id TEXT NOT NULL,
  resolved_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,            -- rank_up / price_drop / new_entry / trend / news
  genre_key TEXT,
  product_id INTEGER,
  strength REAL NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL,
  used INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY,
  post_no INTEGER NOT NULL UNIQUE,
  kind TEXT NOT NULL,            -- carousel / reel
  format TEXT NOT NULL,          -- ranking / price_band / spotlight / guide
  genre_key TEXT NOT NULL,
  hook_type TEXT NOT NULL,
  theme TEXT NOT NULL,
  status TEXT NOT NULL,          -- planned / scripted / rendered / ready / published / failed / skipped
  content_hash TEXT NOT NULL UNIQUE,
  plan_json TEXT NOT NULL,
  script_json TEXT,
  llm_provider TEXT,
  assets_dir TEXT,
  media_json TEXT,               -- 公開URLなど
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS post_products (
  post_id INTEGER NOT NULL REFERENCES posts(id),
  product_id INTEGER NOT NULL REFERENCES products(id),
  position INTEGER NOT NULL,
  PRIMARY KEY (post_id, product_id)
);

CREATE TABLE IF NOT EXISTS publications (
  id INTEGER PRIMARY KEY,
  post_id INTEGER NOT NULL REFERENCES posts(id),
  platform TEXT NOT NULL,        -- instagram / tiktok
  kind TEXT NOT NULL,            -- carousel / reel / story
  status TEXT NOT NULL,          -- publishing / published / failed / dry_run
  container_id TEXT,
  media_id TEXT,
  permalink TEXT,
  error TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  published_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (post_id, platform, kind)
);

CREATE TABLE IF NOT EXISTS metrics (
  publication_id INTEGER NOT NULL REFERENCES publications(id),
  fetched_at TEXT NOT NULL,
  reach INTEGER, views INTEGER, likes INTEGER, comments INTEGER, saves INTEGER, shares INTEGER,
  PRIMARY KEY (publication_id, fetched_at)
);

CREATE TABLE IF NOT EXISTS arm_stats (
  arm_key TEXT PRIMARY KEY,      -- format:ranking / hook:number / theme:milk
  alpha REAL NOT NULL DEFAULT 1,
  beta REAL NOT NULL DEFAULT 1,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS rewarded (
  publication_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS slot_runs (
  date TEXT NOT NULL,
  slot TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  PRIMARY KEY (date, slot)
);

CREATE TABLE IF NOT EXISTS secrets_store (
  name TEXT PRIMARY KEY,
  ciphertext TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY,
  job TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT,
  summary TEXT
);

CREATE TABLE IF NOT EXISTS kv (
  key TEXT PRIMARY KEY,
  value TEXT
);
"""


def _now() -> str:
    return now_jst().isoformat(timespec="seconds")


class DB:
    def __init__(self, path: Path | str):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        # WAL をメインファイルに書き戻してから閉じる（state ブランチに 1 ファイルで保存するため）
        try:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            self.conn.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def q(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def one(self, sql: str, params: tuple | dict = ()) -> sqlite3.Row | None:
        return self.conn.execute(sql, params).fetchone()

    def exec(self, sql: str, params: tuple | dict = ()) -> int:
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    # ---------------- products ----------------
    def upsert_product(self, p: dict[str, Any]) -> int:
        row = self.one("SELECT id FROM products WHERE item_code=?", (p["item_code"],))
        fields = ("source", "genre_key", "name", "short_name", "shop", "caption", "image_url", "affiliate_url", "amazon_url")
        if row:
            sets = ", ".join(f"{f}=?" for f in fields)
            self.exec(f"UPDATE products SET {sets}, updated_at=? WHERE id=?",
                      tuple(p.get(f) for f in fields) + (_now(), row["id"]))
            pid = row["id"]
        else:
            pid = self.exec(
                f"INSERT INTO products (item_code, {', '.join(fields)}, updated_at) VALUES (?{', ?' * len(fields)}, ?)",
                (p["item_code"],) + tuple(p.get(f) for f in fields) + (_now(),),
            )
        self.exec(
            "INSERT OR REPLACE INTO product_snapshots (product_id, date, price, rank, review_count, review_avg) VALUES (?,?,?,?,?,?)",
            (pid, p.get("date") or now_jst().date().isoformat(), p.get("price"), p.get("rank"),
             p.get("review_count"), p.get("review_avg")),
        )
        return pid

    def latest_products(self, genre_key: str, limit: int = 30) -> list[dict[str, Any]]:
        """ジャンルの最新スナップショット（最新日付のもの）を順位順で返す。"""
        rows = self.q(
            """
            SELECT p.*, s.price, s.rank, s.review_count, s.review_avg, s.date
            FROM products p
            JOIN product_snapshots s ON s.product_id = p.id
            WHERE p.genre_key = ?
              AND s.date = (SELECT MAX(date) FROM product_snapshots s2
                            JOIN products p2 ON p2.id = s2.product_id WHERE p2.genre_key = ?)
            ORDER BY COALESCE(s.rank, 9999), s.review_count DESC
            LIMIT ?
            """,
            (genre_key, genre_key, limit),
        )
        return [dict(r) for r in rows]

    def snapshot_history(self, product_id: int, limit: int = 14) -> list[dict[str, Any]]:
        return [dict(r) for r in self.q(
            "SELECT * FROM product_snapshots WHERE product_id=? ORDER BY date DESC LIMIT ?", (product_id, limit))]

    def recently_used_product_ids(self, days: int) -> set[int]:
        since = (now_jst().date().toordinal() - days)
        rows = self.q("SELECT pp.product_id, p.created_at FROM post_products pp JOIN posts p ON p.id = pp.post_id "
                      "WHERE p.status NOT IN ('failed','skipped')")
        out: set[int] = set()
        for r in rows:
            d = r["created_at"][:10]
            from datetime import date
            if date.fromisoformat(d).toordinal() >= since:
                out.add(r["product_id"])
        return out

    # ---------------- posts ----------------
    def next_post_no(self) -> int:
        row = self.one("SELECT MAX(post_no) AS m FROM posts")
        return (row["m"] or 0) + 1

    def hash_exists(self, h: str) -> bool:
        return self.one("SELECT 1 FROM posts WHERE content_hash=?", (h,)) is not None

    def create_post(self, *, kind: str, fmt: str, genre_key: str, hook_type: str, theme: str,
                    content_hash: str, plan: dict[str, Any], product_ids: list[int]) -> dict[str, Any]:
        with self.tx() as c:
            post_no = self.next_post_no()
            cur = c.execute(
                "INSERT INTO posts (post_no, kind, format, genre_key, hook_type, theme, status, content_hash, plan_json, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (post_no, kind, fmt, genre_key, hook_type, theme, "planned", content_hash,
                 json.dumps(plan, ensure_ascii=False), _now(), _now()),
            )
            pid = cur.lastrowid
            for i, prod in enumerate(product_ids):
                c.execute("INSERT OR IGNORE INTO post_products (post_id, product_id, position) VALUES (?,?,?)", (pid, prod, i))
        return self.get_post(pid)

    def get_post(self, post_id: int) -> dict[str, Any]:
        row = self.one("SELECT * FROM posts WHERE id=?", (post_id,))
        return _post_dict(row)

    def update_post(self, post_id: int, **fields: Any) -> None:
        if not fields:
            return
        for k in ("plan_json", "script_json", "media_json"):
            if k in fields and not isinstance(fields[k], (str, type(None))):
                fields[k] = json.dumps(fields[k], ensure_ascii=False)
        fields["updated_at"] = _now()
        sets = ", ".join(f"{k}=?" for k in fields)
        self.exec(f"UPDATE posts SET {sets} WHERE id=?", tuple(fields.values()) + (post_id,))

    def posts_by_status(self, statuses: list[str], kind: str | None = None) -> list[dict[str, Any]]:
        ph = ",".join("?" * len(statuses))
        sql = f"SELECT * FROM posts WHERE status IN ({ph})"
        params: list[Any] = list(statuses)
        if kind:
            sql += " AND kind=?"
            params.append(kind)
        sql += " ORDER BY post_no"
        return [_post_dict(r) for r in self.q(sql, tuple(params))]

    def recent_captions(self, limit: int = 50) -> list[str]:
        out = []
        for r in self.q("SELECT script_json FROM posts WHERE script_json IS NOT NULL ORDER BY id DESC LIMIT ?", (limit,)):
            try:
                out.append(json.loads(r["script_json"]).get("caption_body", ""))
            except Exception:
                pass
        return out

    def last_used_genre_day(self, genre_key: str) -> str | None:
        row = self.one("SELECT MAX(created_at) AS m FROM posts WHERE genre_key=? AND status NOT IN ('failed','skipped')", (genre_key,))
        return row["m"] if row else None

    # ---------------- publications ----------------
    def get_publication(self, post_id: int, platform: str, kind: str) -> dict[str, Any] | None:
        row = self.one("SELECT * FROM publications WHERE post_id=? AND platform=? AND kind=?", (post_id, platform, kind))
        return dict(row) if row else None

    def upsert_publication(self, post_id: int, platform: str, kind: str, **fields: Any) -> None:
        existing = self.get_publication(post_id, platform, kind)
        if existing:
            sets = ", ".join(f"{k}=?" for k in fields)
            if sets:
                self.exec(f"UPDATE publications SET {sets} WHERE id=?", tuple(fields.values()) + (existing["id"],))
        else:
            cols = ["post_id", "platform", "kind", "created_at", *fields.keys()]
            vals = [post_id, platform, kind, _now(), *fields.values()]
            self.exec(f"INSERT INTO publications ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", tuple(vals))

    # ---------------- kv / runs ----------------
    def kv_get(self, key: str, default: str | None = None) -> str | None:
        row = self.one("SELECT value FROM kv WHERE key=?", (key,))
        return row["value"] if row else default

    def kv_set(self, key: str, value: str) -> None:
        self.exec("INSERT OR REPLACE INTO kv (key, value) VALUES (?,?)", (key, value))

    def start_run(self, job: str) -> int:
        return self.exec("INSERT INTO runs (job, started_at, status) VALUES (?,?,?)", (job, _now(), "running"))

    def finish_run(self, run_id: int, status: str, summary: str) -> None:
        self.exec("UPDATE runs SET finished_at=?, status=?, summary=? WHERE id=?", (_now(), status, summary[:4000], run_id))


def _post_dict(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    d = dict(row)
    for k in ("plan_json", "script_json", "media_json"):
        if d.get(k):
            d[k[:-5]] = json.loads(d[k])
        else:
            d[k[:-5]] = None
    return d
