"""Aurora (blurred, bleeding gradient) background generator.

Reads colors from tokens/tokens.json and presets from generators/presets/aurora.json.
Every output is deterministic for a given (preset, seed), so assets can be regenerated.

    .venv/bin/python generators/aurora.py            # all presets
    .venv/bin/python generators/aurora.py dawn tide  # selected presets
    .venv/bin/python generators/aurora.py --seed 99 dawn   # try another variation

Output: assets/aurora/<name>.jpg  (2x canvas, e.g. 2160x2700 for carousel)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates

ROOT = Path(__file__).resolve().parents[1]
TOKENS = json.loads((ROOT / "tokens/tokens.json").read_text())
PRESETS = json.loads((ROOT / "generators/presets/aurora.json").read_text())

COMPUTE_SCALE = 4  # field is computed at 1/4 of the output size, then upscaled


def hex2rgb(h: str) -> np.ndarray:
    return np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)], dtype=np.float32) / 255.0


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


# ---------------------------------------------------------------- geometry
def catmull(points: np.ndarray, n: int) -> np.ndarray:
    p = np.vstack([points[0], points, points[-1]])
    out = []
    segs = len(points) - 1
    for i in range(segs):
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        for t in np.linspace(0, 1, n // segs, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(
                0.5
                * (
                    2 * p1
                    + (-p0 + p2) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )
            )
    out.append(points[-1])
    return np.array(out)


def strand(pts, widths, rng, jitter=0.02, n=700, gain=1.0, t_range=(0.0, 1.0)):
    """A soft stroke along a spline. pts are (x, y) in canvas-width units (y down)."""
    pts = np.array(pts, dtype=np.float32)
    pts = pts + rng.normal(0, jitter, pts.shape).astype(np.float32)
    path = catmull(pts, n)
    w = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(widths)), widths)
    t = np.linspace(t_range[0], t_range[1], len(path))
    return {"path": path, "w": w, "t": t, "gain": gain}


def shape_strands(shape: str, rng: np.random.Generator, aspect: float):
    """Return strands for a named shape. aspect = height / width."""
    H = aspect
    S = []
    if shape == "wave":  # FLOW-like: heavy mass top-left, tail sweeping down-right
        S.append(strand([(-0.15, 0.20 * H), (0.12, 0.17 * H), (0.38, 0.30 * H), (0.62, 0.40 * H), (0.82, 0.43 * H), (0.98, 0.58 * H)],
                        [0.20, 0.19, 0.14, 0.09, 0.07, 0.04], rng, gain=1.25))
        S.append(strand([(-0.05, 0.30 * H), (0.30, 0.36 * H), (0.60, 0.42 * H), (0.86, 0.50 * H)],
                        [0.10, 0.07, 0.05, 0.03], rng, gain=0.45, t_range=(0.2, 0.95)))
    elif shape == "scurve":  # SHIFT-like: vertical S ribbon
        S.append(strand([(0.66, -0.02 * H), (0.58, 0.12 * H), (0.64, 0.25 * H), (0.46, 0.37 * H), (0.40, 0.47 * H), (0.56, 0.60 * H), (0.62, 0.70 * H)],
                        [0.05, 0.07, 0.075, 0.08, 0.085, 0.06, 0.03], rng, jitter=0.012, gain=1.15))
        S.append(strand([(0.70, 0.02 * H), (0.62, 0.15 * H), (0.67, 0.27 * H), (0.50, 0.38 * H)],
                        [0.025, 0.03, 0.03, 0.02], rng, jitter=0.01, gain=0.55, t_range=(0.0, 0.4)))
    elif shape == "scurve2":  # BALANCE-like: drop from top-left, swing right, sweep back left
        S.append(strand([(0.12, -0.05 * H), (0.22, 0.12 * H), (0.40, 0.27 * H), (0.70, 0.38 * H), (0.62, 0.50 * H), (0.35, 0.58 * H), (0.14, 0.66 * H)],
                        [0.12, 0.13, 0.12, 0.10, 0.10, 0.09, 0.05], rng, jitter=0.015, gain=1.2))
    elif shape == "swirl":  # CYCLE-like: open spiral
        cx, cy = 0.52, 0.36 * H
        th = np.linspace(0, 2.3 * math.pi, 9)
        r = np.linspace(0.36, 0.04, 9)
        pts = [(cx + rr * math.cos(a + 2.6), cy + rr * math.sin(a + 2.6) * 0.92) for a, rr in zip(th, r)]
        S.append(strand(pts, [0.09, 0.11, 0.12, 0.11, 0.095, 0.08, 0.06, 0.045, 0.03], rng, jitter=0.01, gain=0.7, n=900))
    elif shape == "smoke":  # ECHO-like: rising wisps
        S.append(strand([(0.58, 0.72 * H), (0.48, 0.58 * H), (0.62, 0.45 * H), (0.50, 0.30 * H), (0.64, 0.16 * H), (0.56, -0.05 * H)],
                        [0.025, 0.045, 0.06, 0.07, 0.08, 0.09], rng, jitter=0.015, gain=1.1, t_range=(0.55, 0.0)))
        S.append(strand([(0.74, 0.55 * H), (0.80, 0.40 * H), (0.70, 0.26 * H), (0.82, 0.10 * H)],
                        [0.05, 0.08, 0.09, 0.08], rng, jitter=0.02, gain=0.4, t_range=(0.85, 1.0)))
        S.append(strand([(0.40, 0.66 * H), (0.36, 0.52 * H), (0.46, 0.40 * H)],
                        [0.03, 0.05, 0.04], rng, jitter=0.02, gain=0.2, t_range=(0.8, 0.95)))
    elif shape == "orb":
        S = "orb"
    else:
        raise ValueError(f"unknown shape: {shape}")
    return S


# ---------------------------------------------------------------- field
def stop_color(stops_lin: np.ndarray, t: np.ndarray) -> np.ndarray:
    x = np.clip(t, 0, 1) * (len(stops_lin) - 1)
    i = np.clip(np.floor(x).astype(int), 0, len(stops_lin) - 2)
    f = (x - i)[..., None]
    return stops_lin[i] * (1 - f) + stops_lin[i + 1] * f


def render_strands(strands, stops_lin, w, h):
    """Each strand is drawn as a dense core plus a wide, faint halo (the 'bleed')."""
    layered = []
    for s in strands:
        layered.append(dict(s, w=s["w"] * 0.55, gain=s["gain"] * 1.0))
        layered.append(dict(s, w=s["w"] * 1.45, gain=s["gain"] * 0.12))
    strands = layered
    W = np.zeros((h, w), np.float32)
    C = np.zeros((h, w, 3), np.float32)
    # bin samples by width so each bin is a single gaussian_filter pass
    allw = np.concatenate([s["w"] for s in strands]) * w
    bins = np.geomspace(max(allw.min(), 2), allw.max() + 1e-3, 10)
    for s in strands:
        px = s["path"] * w
        sig = s["w"] * w
        col = stop_color(stops_lin, s["t"])
        for b0, b1 in zip(bins[:-1], bins[1:]):
            m = (sig >= b0) & (sig < b1 + 1e-6)
            if not m.any():
                continue
            # samples outside the canvas still bleed in: render on a padded canvas
            sigma = (b0 + b1) / 2
            pad = int(sigma * 3)
            imp_w = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
            imp_c = np.zeros((h + 2 * pad, w + 2 * pad, 3), np.float32)
            xs2 = np.clip(px[m, 0].astype(int) + pad, 0, w + 2 * pad - 1)
            ys2 = np.clip(px[m, 1].astype(int) + pad, 0, h + 2 * pad - 1)
            g = s["gain"] * sigma  # wider = proportionally more mass, keeps density similar
            np.add.at(imp_w, (ys2, xs2), g)
            for k in range(3):
                np.add.at(imp_c[..., k], (ys2, xs2), g * col[m, k])
            imp_w = gaussian_filter(imp_w, sigma)[pad:-pad or None, pad:-pad or None]
            for k in range(3):
                C[..., k] += gaussian_filter(imp_c[..., k], sigma)[pad:-pad or None, pad:-pad or None]
            W += imp_w
    return W, C


def render_orb(stops_lin, w, h, rng):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy, r = w * 0.70, h * 0.31, w * 0.36
    cx += rng.normal(0, w * 0.01)
    d = np.hypot(xx - cx, (yy - cy) * 1.02) / r
    # offset rim: bright stop leaks toward lower-left
    ang = np.arctan2(yy - cy, xx - cx)
    rim_bias = np.clip(np.cos(ang - 2.3), 0, 1) ** 2
    # dark core sits off-centre (toward the right edge) so the gradient is asymmetric, not a target
    dc = np.hypot(xx - (cx + r * 0.22), (yy - cy + r * 0.05)) / r
    t = np.clip(dc * 0.55 + rim_bias * np.clip(d - 0.45, 0, 1) * 1.2, 0, 1)
    W = np.exp(-np.clip(d - 0.45, 0, None) ** 2 / 0.12) * 1.6
    C = stop_color(stops_lin, t) * W[..., None]
    return W, C


def warp(arr, rng, amp, scale):
    h, w = arr.shape[:2]
    dx = gaussian_filter(rng.normal(size=(h, w)).astype(np.float32), scale)
    dy = gaussian_filter(rng.normal(size=(h, w)).astype(np.float32), scale)
    dx *= amp / (dx.std() + 1e-6)
    dy *= amp / (dy.std() + 1e-6)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    coords = [yy + dy, xx + dx]
    if arr.ndim == 2:
        return map_coordinates(arr, coords, order=1, mode="nearest")
    return np.stack([map_coordinates(arr[..., k], coords, order=1, mode="nearest") for k in range(arr.shape[2])], -1)


def generate(preset: dict, seed: int | None = None, canvas_key: str = "carousel") -> Image.Image:
    seed = preset["seed"] if seed is None else seed
    rng = np.random.default_rng(seed)
    cv = TOKENS["canvas"][canvas_key]
    S = TOKENS["canvas"]["assetScale"]
    OW, OH = cv["width"] * S, cv["height"] * S
    w, h = OW // COMPUTE_SCALE, OH // COMPUTE_SCALE
    pig = TOKENS["color"]["pigment"]
    stops_lin = srgb_to_lin(np.stack([hex2rgb(pig[c]) for c in preset["stops"]]))

    strands = shape_strands(preset["shape"], rng, OH / OW)
    if strands == "orb":
        Wf, Cf = render_orb(stops_lin, w, h, rng)
    else:
        Wf, Cf = render_strands(strands, stops_lin, w, h)

    # organic bleed: two scales of domain warping + soft blur
    stack = np.concatenate([Wf[..., None], Cf], -1)
    warp_amt = preset.get("warp", 1.0)
    stack = warp(stack, rng, amp=w * 0.014 * warp_amt, scale=w * 0.12)
    stack = warp(stack, rng, amp=w * 0.004 * warp_amt, scale=w * 0.03)
    stack = gaussian_filter(stack, sigma=(w * 0.006, w * 0.006, 0))
    Wf, Cf = stack[..., 0], stack[..., 1:]

    col = Cf / (Wf[..., None] + 1e-6)
    k = preset.get("density", 3.6) / (np.percentile(Wf, 99.5) + 1e-6)
    alpha = 1 - np.exp(-k * Wf)

    # upscale field to output size
    def up(a):
        im = Image.fromarray(a.astype(np.float32), mode="F") if a.ndim == 2 else None
        return np.asarray(im.resize((OW, OH), Image.BICUBIC))

    alpha_u = np.clip(up(alpha), 0, 1)
    col_u = np.stack([up(col[..., c]) for c in range(3)], -1)

    # stochastic edge grain (2px clusters so it survives downsampling to 1x)
    tex = TOKENS["texture"]
    gr = rng.random((OH // 2, OW // 2)).astype(np.float32)
    gr = np.repeat(np.repeat(gr, 2, 0), 2, 1)
    edge = np.sqrt(np.clip(alpha_u * (1 - alpha_u), 0, 0.25)) * 2
    alpha_g = np.clip(alpha_u + (gr - 0.5) * tex["grain"]["auroraEdge"] * edge * 1.6, 0, 1)

    paper = srgb_to_lin(hex2rgb(TOKENS["color"]["paper"]["cream"]))
    out = paper * (1 - alpha_g[..., None]) + np.clip(col_u, 0, 1) * alpha_g[..., None]
    out = lin_to_srgb(out)

    # global paper grain
    n = rng.normal(0, 1, (OH // 2, OW // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)
    out = out + n[..., None] * tex["paper"]["amount"]
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out", default=str(ROOT / "assets/aurora"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for p in PRESETS["presets"]:
        if a.names and p["name"] not in a.names:
            continue
        img = generate(p, a.seed, PRESETS.get("size", "carousel"))
        suffix = f"-s{a.seed}" if a.seed is not None else ""
        path = out / f"{p['name']}{suffix}.jpg"
        img.save(path, quality=93, subsampling=0)
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
