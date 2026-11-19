"""Product background removal (rembg) with clean-up and QA.

    .venv/bin/python pipeline/cutout.py                 # every product in data/products.json
    .venv/bin/python pipeline/cutout.py facial-ems      # selected ids
    .venv/bin/python pipeline/cutout.py --force         # redo even if up to date
    .venv/bin/python pipeline/cutout.py --model isnet-general-use   # force a model (default: auto)

Input : the product's "image" (data/products.json), e.g. assets/products/raw/<id>.jpg
Output: assets/products/cutout/<id>.png  (trimmed RGBA, edge colour decontaminated)
        assets/products/cutout/<id>.json (crop offset, model, timestamp)
        docs/previews/cutout-qa.jpg      (raw / on cream / on black / alpha, per product)

Manual override: put a hand-made cut-out (e.g. from Photoshop) at
assets/products/manual/<id>.png — the build then uses it instead and this script skips the id.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("U2NET_HOME", str(ROOT / ".cache/models"))  # rembg model cache inside the project
from rembg import new_session, remove  # noqa: E402

# "auto": birefnet-general (best edges, ~8 GB peak) when enough memory is free, else isnet-general-use (~1 GB).
DEFAULT_MODEL = "auto"
HQ_MODEL, LIGHT_MODEL = "birefnet-general", "isnet-general-use"
HQ_MIN_FREE_GB = float(os.environ.get("REMBG_HQ_MIN_GB", "10"))


def pick_model(requested: str) -> str:
    if requested != "auto":
        return requested
    import psutil
    free = psutil.virtual_memory().available / 2**30
    model = HQ_MODEL if free >= HQ_MIN_FREE_GB else LIGHT_MODEL
    print(f"model auto → {model} (available memory {free:.1f} GB, birefnet needs ≥ {HQ_MIN_FREE_GB:.0f} GB)")
    return model


def make_session(model: str):
    import onnxruntime as ort
    o = ort.SessionOptions()
    o.enable_cpu_mem_arena = False  # lowers birefnet peak memory from ~9.4 GB to ~8 GB
    o.enable_mem_pattern = False
    return new_session(model, sess_opts=o)
PAD = 16


def keep_main(alpha: np.ndarray, min_ratio=0.02) -> np.ndarray:
    """Drop specks: keep connected parts that are at least min_ratio of the largest part."""
    lab, n = ndimage.label(alpha > 0.5)
    if n <= 1:
        return alpha
    sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * min_ratio])
    keep = ndimage.binary_dilation(keep, iterations=3)  # keep the soft edge around kept parts
    return alpha * keep


def decontaminate(rgb: np.ndarray, alpha: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """Remove backdrop colour bleeding into semi-transparent edge pixels: F = (I - (1-a)B) / a."""
    a = alpha[..., None]
    fg = (rgb - (1 - a) * bg) / np.clip(a, 0.05, 1)
    edge = (alpha > 0.02) & (alpha < 0.98)
    out = rgb.copy()
    out[edge] = np.clip(fg[edge], 0, 1)
    return out


def backdrop_colour(rgb: np.ndarray) -> np.ndarray:
    border = np.concatenate([rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3), rgb[:, :8].reshape(-1, 3), rgb[:, -8:].reshape(-1, 3)])
    return np.median(border, axis=0)


def cut(src: Path, session) -> tuple[Image.Image, dict]:
    im = Image.open(src).convert("RGB")
    rgba = np.asarray(remove(im, session=session, post_process_mask=True)).astype(np.float32) / 255
    rgb, alpha = np.asarray(im).astype(np.float32) / 255, rgba[..., 3]
    alpha = keep_main(alpha)
    rgb = decontaminate(rgb, alpha, backdrop_colour(rgb))
    ys, xs = np.where(alpha > 0.02)
    y0, y1 = max(ys.min() - PAD, 0), min(ys.max() + PAD + 1, alpha.shape[0])
    x0, x1 = max(xs.min() - PAD, 0), min(xs.max() + PAD + 1, alpha.shape[1])
    out = np.dstack([rgb, alpha])[y0:y1, x0:x1]
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA"), {"x0": int(x0), "y0": int(y0), "src_size": im.size}


def iou_vs_mock(pid: str, cut_img: Image.Image, meta: dict) -> float | None:
    """If a ground-truth mock exists (generators/mock_products.py), score the mask overlap."""
    gt_png, gt_json = ROOT / f"assets/products/mock/{pid}.png", ROOT / f"assets/products/mock/{pid}.json"
    if not gt_png.exists() or not gt_json.exists():
        return None
    W, H = meta["src_size"]
    def place(img, x0, y0):
        canvas = np.zeros((H, W), bool)
        a = np.asarray(img)[..., 3] > 127
        canvas[y0 : y0 + a.shape[0], x0 : x0 + a.shape[1]] = a[: H - y0, : W - x0]
        return canvas
    g = json.loads(gt_json.read_text())
    A, B = place(Image.open(gt_png), g["x0"], g["y0"]), place(cut_img, meta["x0"], meta["y0"])
    return float((A & B).sum() / max((A | B).sum(), 1))


def qa_sheet(rows, out: Path):
    tile, pad, lab = 300, 12, 22
    sheet = Image.new("RGB", (pad + 4 * (tile + pad), pad + len(rows) * (tile + pad + lab)), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for r, (pid, raw, cutimg, score, source) in enumerate(rows):
        y = pad + r * (tile + pad + lab)
        tiles = []
        t = Image.open(raw).convert("RGB"); t.thumbnail((tile, tile)); tiles.append(t)
        for bg in [(245, 240, 230), (21, 20, 19)]:
            c = cutimg.copy(); c.thumbnail((tile, tile))
            b = Image.new("RGBA", c.size, bg + (255,)); b.alpha_composite(c); tiles.append(b.convert("RGB"))
        a = cutimg.getchannel("A").convert("RGB"); a.thumbnail((tile, tile)); tiles.append(a)
        for i, t in enumerate(tiles):
            x = pad + i * (tile + pad)
            sheet.paste(t, (x + (tile - t.width) // 2, y + (tile - t.height) // 2))
        label = f"{pid}  [{source}]" + (f"  IoU vs ground truth {score:.3f}" if score is not None else "")
        d.text((pad, y + tile + 5), label + "    raw / on cream / on black / alpha", fill=(230, 230, 230))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=90)


def process_one(pid: str, model: str):
    """Worker: cut one product (run in its own process so model memory is released after each)."""
    p = {x["id"]: x for x in json.loads((ROOT / "data/products.json").read_text())}[pid]
    raw = ROOT / p["image"]
    outdir = ROOT / "assets/products/cutout"
    t = time.time()
    img, meta = cut(raw, make_session(model))
    img.save(outdir / f"{pid}.png", optimize=True)
    score = iou_vs_mock(pid, img, meta)
    meta.update(model=model, iou=score, seconds=round(time.time() - t, 1))
    (outdir / f"{pid}.json").write_text(json.dumps(meta) + "\n")
    print(f"{pid}: {img.size} in {meta['seconds']}s" + (f", IoU {score:.3f}" if score is not None else ""), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default=os.environ.get("REMBG_MODEL", DEFAULT_MODEL))
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.worker:
        process_one(a.ids[0], a.model)
        return
    products = json.loads((ROOT / "data/products.json").read_text())
    outdir = ROOT / "assets/products/cutout"
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in products:
        pid = p["id"]
        if a.ids and pid not in a.ids:
            continue
        raw = ROOT / p["image"]
        manual = ROOT / f"assets/products/manual/{pid}.png"
        dst, meta_f = outdir / f"{pid}.png", outdir / f"{pid}.json"
        if manual.exists():
            print(f"{pid}: manual cut-out found (assets/products/manual), skipping rembg")
            rows.append((pid, raw, Image.open(manual).convert("RGBA"), None, "manual"))
            continue
        if a.force or not dst.exists() or dst.stat().st_mtime < raw.stat().st_mtime:
            model = pick_model(a.model)
            print(f"{pid}: removing background with '{model}'…", flush=True)
            r = subprocess.run([sys.executable, __file__, pid, "--worker", "--model", model])
            if r.returncode != 0 and model == HQ_MODEL:
                print(f"{pid}: {HQ_MODEL} failed (exit {r.returncode}, likely out of memory) → retrying with {LIGHT_MODEL}")
                r = subprocess.run([sys.executable, __file__, pid, "--worker", "--model", LIGHT_MODEL])
            if r.returncode != 0:
                raise SystemExit(f"{pid}: background removal failed")
        else:
            print(f"{pid}: up to date")
        meta = json.loads(meta_f.read_text()) if meta_f.exists() else {}
        rows.append((pid, raw, Image.open(dst).convert("RGBA"), meta.get("iou"), meta.get("model", "rembg")))
    if rows:
        qa_sheet(rows, ROOT / "docs/previews/cutout-qa.jpg")
        print("QA sheet → docs/previews/cutout-qa.jpg")


if __name__ == "__main__":
    main()
