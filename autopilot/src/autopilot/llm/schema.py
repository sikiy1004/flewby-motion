from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Copy(BaseModel):
    """LLM（またはテンプレ）が作る「文章だけ」。数値はテンプレ側で実データを差し込む。"""

    hook: str = Field(description="表紙・動画冒頭3秒の一文（24字以内）")
    subtitle: str = Field(description="表紙のサブコピー（40字以内）")
    product_notes: dict[str, str] = Field(description="item_code -> 『こんな人に』の一文（40字以内）")
    summary: str = Field(description="まとめスライドの一文（60字以内）")
    narration_hook: str = Field(description="動画冒頭の読み上げ（40字以内）")
    narration_products: dict[str, str] = Field(description="item_code -> 商品紹介の読み上げ（70字以内）")
    narration_outro: str = Field(description="動画の締めの読み上げ（50字以内）")
    caption_body: str = Field(description="Instagram キャプション本文（PR表記・リンク案内・ハッシュタグは除く）")
    caption_tiktok: str = Field(description="TikTok 用の短いキャプション（120字以内）")
    hashtags_instagram: list[str] = Field(default_factory=list)
    hashtags_tiktok: list[str] = Field(default_factory=list)

    @field_validator("hashtags_instagram", "hashtags_tiktok")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        out = []
        for t in v:
            t = t.strip().replace(" ", "")
            if not t:
                continue
            if not t.startswith("#"):
                t = "#" + t
            if t not in out:
                out.append(t)
        return out

    def clipped(self) -> "Copy":
        lim = {"hook": 26, "subtitle": 44, "summary": 70, "narration_hook": 50, "narration_outro": 60,
               "caption_body": 900, "caption_tiktok": 150}
        d = self.model_dump()
        for k, n in lim.items():
            d[k] = d[k].strip()[:n]
        d["product_notes"] = {k: v.strip()[:44] for k, v in d["product_notes"].items()}
        d["narration_products"] = {k: v.strip()[:60] for k, v in d["narration_products"].items()}
        return Copy(**d)
