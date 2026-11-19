"""自動更新されるアクセストークンの保管（DB に Fernet で暗号化して保存）。

初回は環境変数（GitHub Secrets）の値を使い、更新後は DB の値を優先する。
暗号鍵は AUTOPILOT_SECRET_KEY（`autopilot keygen` で生成）。
"""
from __future__ import annotations

import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from .config import now_jst
from .db import DB


def new_key() -> str:
    return Fernet.generate_key().decode()


class TokenStore:
    def __init__(self, db: DB):
        self.db = db
        key = os.environ.get("AUTOPILOT_SECRET_KEY")
        self.fernet = Fernet(key.encode()) if key else None

    def get(self, name: str) -> dict[str, Any] | None:
        if not self.fernet:
            return None
        row = self.db.one("SELECT ciphertext FROM secrets_store WHERE name=?", (name,))
        if not row:
            return None
        try:
            return json.loads(self.fernet.decrypt(row["ciphertext"].encode()))
        except InvalidToken:
            return None

    def put(self, name: str, value: dict[str, Any]) -> bool:
        if not self.fernet:
            return False
        value = {**value, "saved_at": now_jst().isoformat()}
        ct = self.fernet.encrypt(json.dumps(value).encode()).decode()
        self.db.exec("INSERT OR REPLACE INTO secrets_store (name, ciphertext, updated_at) VALUES (?,?,?)",
                     (name, ct, now_jst().isoformat()))
        return True
