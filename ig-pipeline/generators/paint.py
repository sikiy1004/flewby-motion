"""Impasto paint-stroke sprite generator (B-plan accent assets).

A stroke is built in its own (along, across) coordinates: a mask with a rounded
loaded start and a dry-brush tail, a height map made of bristle streaks, edge
ridges and a paint lump, and a marbled colour field. It is then rotated and lit
(diffuse + glossy specular) so it reads as thick, wet acrylic.

    .venv/bin/python generators/paint.py              # all strokes
    .venv/bin/python generators/paint.py s01 s05      # selected
    .venv/bin/python generators/paint.py --seed 7 s01 # another variation

Output: assets/paint/<name>.png (RGBA, 2x, with a soft baked contact shadow)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates, rotate, shift

ROOT = Path(__file__).resolve().parents[1]
TOKENS = json.loads((ROOT / "tokens/tokens.json").read_text())
PRESETS = json.loads((ROOT / "generators/presets/paint.json").read_text())
SCALE = TOKENS["canvas"]["assetScale"]


def hex2lin(h):
    c = np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def norm(a):
    a = a - a.min()
    return a / (a.max() + 1e-6)


def streaks(rng, shape, across, along):
    """Noise stretched along the stroke direction (axis 1) = bristle marks."""
    return norm(gaussian_filter(rng.random(shape).astype(np.float32), (across, along)))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def make_stroke(spec, seed=None):
    rng = np.random.default_rng(spec["seed"] if seed is None else seed)
    L = int(spec["length"] * SCALE)
    T = int(spec["thickness"] * SCALE)
    pad = int(max(L, T) * 0.25)
    H, W = T + 2 * pad, L + 2 * pad
    v, u = np.mgrid[0:H, 0:W].astype(np.float32)
    s = (u - pad) / L                  # 0..1 along
    vc = (v - H / 2)                   # across, centred

    # --- outline: half-width varies along the stroke, ragged edges
    n1 = gaussian_filter(rng.normal(size=W).astype(np.float32), L * 0.05)
    n1 /= np.abs(n1).max() + 1e-6
    n2 = gaussian_filter(rng.normal(size=W).astype(np.float32), L * 0.008)
    n2 /= np.abs(n2).max() + 1e-6
    sc = np.clip(s[0], 0, 1)
    belly = 0.78 + 0.22 * np.sin(np.pi * np.clip(sc * 0.9 + 0.05, 0, 1)) ** 0.6
    hw = (T / 2) * belly * (1 + 0.16 * n1 + 0.03 * n2)
    curve = np.cumsum(gaussian_filter(rng.normal(size=W).astype(np.float32), L * 0.08))
    curve = (curve - curve.mean()) / (np.abs(curve - curve.mean()).max() + 1e-6) * T * 0.14
    vv = vc - curve[None, :]
    r = np.abs(vv) / hw[None, :]       # 0 centre .. 1 edge

    # rounded, loaded start cap; dry, broken tail
    cap = 0.10 * (1 - np.sqrt(np.clip(1 - r ** 2, 0, 1)))
    st_fine = streaks(rng, (H, W), 1.2 * SCALE, 25 * SCALE)
    st_dry = streaks(rng, (H, W), 3.0 * SCALE, 40 * SCALE)
    st_coarse = streaks(rng, (H, W), 4.0 * SCALE, 70 * SCALE)
    tail = 1.0 - 0.14 * st_coarse - 0.05 * rng.random((H, 1)).astype(np.float32)
    inside = (r < 1) & (s > cap) & (s < tail)
    # dry-brush: in the last ~25 %, a few thick bristle gaps open up
    dry = smoothstep(0.74, 1.0, s)
    inside &= st_dry > dry * 0.8
    mask = gaussian_filter(inside.astype(np.float32), 1.0 * SCALE)

    # --- height map: big smooth folds + lumps dominate; fine bristles only in the tail
    base = 1.0 - 0.4 * smoothstep(0.2, 1.0, s)
    dome = (1 - r ** 2.5).clip(0, 1)
    folds = streaks(rng, (H, W), 9 * SCALE, 40 * SCALE)
    lumps = norm(gaussian_filter(rng.random((H, W)).astype(np.float32), 16 * SCALE))
    ridge = np.exp(-((1 - r) / 0.12) ** 2) * (1 - dry) * 0.5
    lump_c = (rng.uniform(0.06, 0.25), rng.uniform(-0.3, 0.3))
    lump = 1.3 * np.exp(-(((s - lump_c[0]) / 0.11) ** 2 + ((vv / (T / 2) - lump_c[1]) / 0.55) ** 2))
    height = (base * dome * 1.1 + 1.0 * folds + 0.8 * lumps + ridge + lump + st_fine * (0.06 + 0.35 * dry)) * mask
    height = gaussian_filter(height, 1.3 * SCALE)

    # --- colour: marbling between pigments, following the streaks
    pig = TOKENS["color"]["pigment"]
    cols = [hex2lin(pig[c]) for c in spec["colors"]]
    col = np.broadcast_to(cols[0], (H, W, 3)).copy()
    mar = spec.get("marble", 0.0)
    if len(cols) > 1 and mar > 0:
        m = streaks(rng, (H, W), 14 * SCALE, 45 * SCALE)
        m = m + 0.25 * vv / (T / 2) * rng.choice([-1, 1])     # bias to one side, like a second loaded colour
        w2 = smoothstep(1 - mar - 0.025, 1 - mar + 0.025, norm(m))[..., None]
        col = col * (1 - w2) + cols[1] * w2
    if len(cols) > 2:
        m3 = streaks(rng, (H, W), 8 * SCALE, 35 * SCALE)
        w3 = smoothstep(0.80, 0.83, m3)[..., None]
        col = col * (1 - w3) + cols[2] * w3

    # --- organic swirl: warp the whole field so marbling and folds twist
    stack = np.concatenate([mask[..., None], height[..., None], col], -1)
    dx = gaussian_filter(rng.normal(size=(H, W)).astype(np.float32), T * 0.18)
    dy = gaussian_filter(rng.normal(size=(H, W)).astype(np.float32), T * 0.18)
    amp = T * spec.get("swirl", 0.07)
    dx *= amp / (dx.std() + 1e-6); dy *= amp / (dy.std() + 1e-6)
    stack = np.stack([map_coordinates(stack[..., c], [v + dy, u + dx], order=1, mode="constant") for c in range(stack.shape[-1])], -1)

    # --- rotate everything into place
    ang = spec["angle"]
    stack = rotate(stack, ang, axes=(1, 0), reshape=True, order=1, mode="constant", cval=0.0)
    mask, height, col = stack[..., 0].clip(0, 1), stack[..., 1], stack[..., 2:]

    # --- lighting (top-left key light, glossy acrylic)
    k = 0.11 / SCALE * T  # bump strength relative to stroke size
    gy, gx = np.gradient(height)
    sx, sy = -gx * k, -gy * k
    mag = np.hypot(sx, sy) + 1e-6
    lim = np.tanh(mag) / mag * 0.95           # cap the tilt so steep outer edges don't go black
    N = np.stack([sx * lim, sy * lim, np.ones_like(gx)], -1)
    N /= np.linalg.norm(N, axis=-1, keepdims=True)
    Ld = np.array([-0.45, -0.6, 0.66], np.float32); Ld /= np.linalg.norm(Ld)
    Hv = Ld + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
    ndl = np.clip((N * Ld).sum(-1), 0, 1)
    ndh = np.clip((N * Hv).sum(-1), 0, 1)
    flat = Ld[2]
    shade = 0.58 + 0.42 * ndl / flat
    spec_hi = 0.75 * ndh ** 70 + 0.16 * ndh ** 9
    lum = (col * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    spec_hi = spec_hi[..., None] * (0.55 + 0.45 * (1 - lum))   # gloss reads stronger on darks
    rgb = col * shade[..., None] + spec_hi

    # --- soft contact shadow (cast down-right), baked under the paint
    sh = shift(gaussian_filter(mask, 6 * SCALE), (5 * SCALE, 4 * SCALE), order=1) * 0.22
    a_out = mask + sh * (1 - mask)
    shadow_col = np.array([0.18, 0.15, 0.12], np.float32) * 0.15
    rgb_out = (rgb * mask[..., None] + shadow_col * (sh * (1 - mask))[..., None]) / (a_out[..., None] + 1e-6)

    out = np.dstack([lin2srgb(rgb_out), a_out])
    ys, xs = np.where(a_out > 0.004)
    out = out[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    out = ROOT / "assets/paint"
    out.mkdir(parents=True, exist_ok=True)
    for spec in PRESETS["strokes"]:
        if a.names and spec["name"] not in a.names:
            continue
        img = make_stroke(spec, a.seed)
        p = out / f"{spec['name']}{'-s%d' % a.seed if a.seed is not None else ''}.png"
        img.save(p, optimize=True)
        print("wrote", p.relative_to(ROOT), img.size)


if __name__ == "__main__":
    main()
