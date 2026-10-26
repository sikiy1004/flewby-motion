#!/usr/bin/env python3
"""記事ファイルの機械的な品質チェック。

使い方:
  python3 scripts/check_article.py articles/drafts/<slug>.md          # 執筆後の自己点検
  python3 scripts/check_article.py articles/drafts/<slug>.md --final  # 投稿用出力の前（レビュー合格が条件）

内容の正しさは判定しない。形式・禁止表現・出典の書式・未解決の目印だけを見る。
エラーがあれば終了コード1を返す。
"""
import re
import sys
from pathlib import Path

from common import ARTICLES, PAYWALL, split_front_matter, to_int

REQUIRED_KEYS = ["slug", "idea_id", "genre_id", "title", "title_type", "price_yen", "status", "version"]
TITLE_TYPES = {"question", "verify", "classic", "concept"}

# (表現, 重さ)。error は必ず直す。warn は文脈を見て判断する。
BANNED = [
    ("いかがでしたか", "error"),
    ("について解説します", "error"),
    ("を徹底解説", "error"),
    ("衝撃の", "error"),
    ("9割が知らない", "error"),
    ("人生が変わる", "error"),
    ("科学的に証明された", "error"),
    ("脳科学的に正しい", "error"),
    ("完全版", "warn"),
    ("最強の", "warn"),
    ("結論から言うと", "warn"),
    ("と言っても過言ではない", "warn"),
    ("紐解", "warn"),
    ("深掘り", "warn"),
]
REPEATABLE = [("まとめると", 1), ("ではないでしょうか", 2), ("つまり", 4)]
UNRESOLVED = ["要確認", "TODO", "未確認", "（出典）", "[要出典]"]


def body_parts(body):
    """本文を (無料部分, 有料部分, 記事末の付録) に分ける。付録は「確度の一覧」以降。"""
    appendix_at = body.find("\n## 確度の一覧")
    main = body if appendix_at == -1 else body[:appendix_at]
    appendix = "" if appendix_at == -1 else body[appendix_at:]
    if PAYWALL in main:
        free, _, paid = main.partition(PAYWALL)
    else:
        free, paid = main, ""
    return free, paid, appendix


def visible_len(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return len(re.sub(r"\s", "", text))


def references(body):
    section = re.search(r"\n## 参考文献\n(.*?)(\n## |\Z)", body, flags=re.S)
    if not section:
        return None
    refs = {}
    for line in section.group(1).splitlines():
        m = re.match(r"\s*(\d+)\.\s+(.*)", line)
        if m:
            refs[int(m.group(1))] = m.group(2)
    return refs


def check(path, final):
    errors, warnings = [], []
    text = path.read_text(encoding="utf-8")
    meta, body = split_front_matter(text)

    for key in REQUIRED_KEYS:
        if not meta.get(key):
            errors.append(f"front matter に {key} がありません")
    if meta.get("title_type") and meta["title_type"] not in TITLE_TYPES:
        errors.append(f"title_type は {sorted(TITLE_TYPES)} のいずれかにしてください")

    price = to_int(meta.get("price_yen", "0"))
    paywalls = body.count(PAYWALL)
    if price > 0 and paywalls != 1:
        errors.append(f"有料記事には {PAYWALL} がちょうど1つ必要です（現在 {paywalls} 個）")
    if price == 0 and paywalls:
        errors.append(f"無料記事（price_yen: 0）に {PAYWALL} があります")

    free, paid, appendix = body_parts(body)
    total = visible_len(free) + visible_len(paid)
    if price > 0 and total:
        ratio = visible_len(free) / total
        print(f"文字数（記事末の付録を除く）: {total} / 無料部分 {ratio:.0%}")
        if not 0.25 <= ratio <= 0.40:
            warnings.append(f"無料部分の比率が {ratio:.0%} です（目安は25〜40%）")
    else:
        print(f"文字数（記事末の付録を除く）: {total}")

    if "## 確度の一覧" not in body:
        errors.append("「## 確度の一覧」がありません")
    refs = references(body)
    if refs is None:
        errors.append("「## 参考文献」がありません")
        refs = {}
    elif not refs:
        errors.append("参考文献が1件もありません（番号付きリスト `1. ...` で書いてください）")
    for n, ref in refs.items():
        if not re.search(r"https?://|doi\.org|DOI|ISBN", ref):
            errors.append(f"参考文献 {n} に URL・DOI・ISBN がありません")
        if "閲覧日" not in ref:
            errors.append(f"参考文献 {n} に閲覧日がありません")

    cited = {int(n) for n in re.findall(r"［(\d+)］", free + paid)}
    for n in sorted(cited - set(refs)):
        errors.append(f"本文の ［{n}］ に対応する参考文献がありません")
    for n in sorted(set(refs) - cited):
        warnings.append(f"参考文献 {n} は本文で参照されていません")

    prose = free + paid
    for phrase, level in BANNED:
        if phrase in prose:
            (errors if level == "error" else warnings).append(f"禁止表現「{phrase}」があります")
    for phrase, limit in REPEATABLE:
        count = prose.count(phrase)
        if count > limit:
            warnings.append(f"「{phrase}」が {count} 回あります（目安 {limit} 回以下）")

    for marker in UNRESOLVED:
        if marker in body:
            (errors if final else warnings).append(f"未解決の目印「{marker}」が残っています")

    if final:
        if to_int(meta.get("quality_score", "0")) < 80:
            errors.append("quality_score が80未満、または未記入です")
        review = ARTICLES / "review" / f"{meta.get('slug', path.stem)}.md"
        if not review.exists():
            errors.append(f"レビュー記録 {review.relative_to(ARTICLES.parent)} がありません")
        else:
            review_meta, _ = split_front_matter(review.read_text(encoding="utf-8"))
            if review_meta.get("result") != "pass":
                errors.append("レビュー記録の result が pass ではありません")
            if review_meta.get("version") != meta.get("version"):
                errors.append("レビュー記録の version が下書きの version と一致しません")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print("OK" if not errors else f"{len(errors)} 件のエラー")
    return not errors


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    final = "--final" in args
    paths = [Path(a) for a in args if a != "--final"]
    ok = all(check(p, final) for p in paths)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
