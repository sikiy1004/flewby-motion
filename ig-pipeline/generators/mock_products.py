"""Simple 'clay render' mock products for samples and background-removal tests.

Each product is a stack of shapes (signed distance fields) with bevelled height,
lit like a studio render. Two files per product:
  assets/products/raw/<id>.jpg      product on a studio backdrop (input for rembg)
  assets/products/mock/<id>.png     ground-truth transparent cut-out (for QA of rembg)

    .venv/bin/python generators/mock_products.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
S = 1400  # canvas px


def lin(h):
    c = np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


Y, X = np.mgrid[0:S, 0:S].astype(np.float32)


def rot(x, y, cx, cy, deg):
    a = np.deg2rad(deg)
    dx, dy = x - cx, y - cy
    return dx * np.cos(a) + dy * np.sin(a), -dx * np.sin(a) + dy * np.cos(a)


def sd_capsule(cx, cy, length, r, deg=0):
    u, v = rot(X, Y, cx, cy, deg)
    u = np.clip(np.abs(u) - length / 2, 0, None)
    return np.hypot(u, v) - r


def sd_rbox(cx, cy, w, h, r, deg=0):
    u, v = rot(X, Y, cx, cy, deg)
    qx, qy = np.abs(u) - w / 2 + r, np.abs(v) - h / 2 + r
    return np.hypot(np.clip(qx, 0, None), np.clip(qy, 0, None)) + np.minimum(np.maximum(qx, qy), 0) - r


def sd_circle(cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def sd_ellipse(cx, cy, rx, ry, deg=0):
    u, v = rot(X, Y, cx, cy, deg)
    k = np.hypot(u / rx, v / ry)
    return (k - 1) * min(rx, ry)


class Scene:
    def __init__(self):
        self.h = np.full((S, S), -1e9, np.float32)
        self.col = np.zeros((S, S, 3), np.float32)
        self.gloss = np.zeros((S, S), np.float32)
        self.mask = np.zeros((S, S), np.float32)

    def add(self, sd, color, z=0.0, bevel=40, gloss=0.3, dome=0.0):
        inside = np.clip(-sd / bevel, 0, 1)
        hp = np.sqrt(1 - (1 - inside) ** 2) * bevel + dome * np.clip(-sd, 0, None) ** 0.5
        hp = z + hp
        m = (sd < 0.5) & ((hp > self.h) | (self.mask < 0.5))
        self.h = np.where(m, hp, self.h)
        self.col = np.where(m[..., None], lin(color), self.col)
        self.gloss = np.where(m, gloss, self.gloss)
        aa = np.clip(0.5 - sd, 0, 1)
        self.mask = np.maximum(self.mask, aa)

    def render(self):
        h = np.where(self.mask > 0, self.h, 0)
        h = gaussian_filter(h, 1.2)
        gy, gx = np.gradient(h)
        N = np.stack([-gx, -gy, np.ones_like(gx)], -1)
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        L = np.array([-0.5, -0.65, 0.58], np.float32); L /= np.linalg.norm(L)
        Hv = L + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        ndl = np.clip((N * L).sum(-1), 0, 1)
        ndh = np.clip((N * Hv).sum(-1), 0, 1)
        # soft "studio" fill from the camera + rim from the right
        rim = np.clip((N * np.array([0.8, 0.1, 0.2])).sum(-1), 0, 1) ** 3
        shade = 0.38 + 0.55 * ndl / L[2] * 0.85 + 0.15 * rim
        spec = self.gloss * (0.9 * ndh ** 60 + 0.15 * ndh ** 8)
        rgb = self.col * shade[..., None] + spec[..., None]
        # subtle top-to-bottom falloff like a softbox
        rgb *= (1.05 - 0.12 * (Y / S))[..., None]
        return rgb, self.mask


def save(rid, scene: Scene, backdrop="#E9E7E3"):
    rgb, a = scene.render()
    ys, xs = np.where(a > 0.01)
    pad = 24
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + pad, S), max(xs.min() - pad, 0), min(xs.max() + pad, S)
    rgba = np.dstack([srgb(rgb), a])[y0:y1, x0:x1]
    (ROOT / "assets/products/mock").mkdir(parents=True, exist_ok=True)
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(ROOT / f"assets/products/mock/{rid}.png", optimize=True)
    # crop offset in the raw photo, so cut-out QA can compare masks in the same coordinates
    (ROOT / f"assets/products/mock/{rid}.json").write_text(f'{{"x0": {int(x0)}, "y0": {int(y0)}}}\n')

    # "photo": seamless backdrop with gradient, contact shadow, noise, slight blur
    bg = lin(backdrop) * (1.08 - 0.25 * ((Y - S * 0.35) / S) ** 2 * 2)[..., None]
    sh = gaussian_filter(np.roll(np.roll(a, 30, 0), 18, 1), 28) * 0.45
    floor = gaussian_filter((np.abs(Y - (ys.max() + 6)) < 10).astype(np.float32) * (np.abs(X - xs.mean()) < (xs.max() - xs.min()) * 0.4), 20) * 0.6
    bg = bg * (1 - np.clip(sh + floor, 0, 0.6))[..., None]
    photo = rgb * a[..., None] + bg * (1 - a[..., None])
    photo = srgb(photo) + np.random.default_rng(1).normal(0, 0.012, (S, S, 1))
    im = Image.fromarray((np.clip(photo, 0, 1) * 255).astype(np.uint8), "RGB")
    (ROOT / "assets/products/raw").mkdir(parents=True, exist_ok=True)
    im.save(ROOT / f"assets/products/raw/{rid}.jpg", quality=90)
    print("wrote", rid)


# ---------------------------------------------------------------- products
def facial_ems():  # handheld EMS / warm facial device
    sc = Scene()
    deg = -12
    sc.add(sd_capsule(700, 860, 520, 92, deg + 90), "#EEEBE6", z=0, bevel=70, gloss=0.25)        # handle
    sc.add(sd_rbox(640, 470, 400, 330, 150, deg), "#EEEBE6", z=8, bevel=80, gloss=0.25)          # head
    sc.add(sd_ellipse(640, 455, 150, 118, deg), "#C9A27E", z=100, bevel=28, gloss=0.9)             # warm plate (champagne)
    sc.add(sd_ellipse(640, 455, 108, 78, deg), "#D9B996", z=125, bevel=18, gloss=0.9)
    for i, yy in enumerate([700, 760, 820]):                                                     # buttons
        cx = 700 + (yy - 860) * np.sin(np.deg2rad(-deg)) * -1
        sc.add(sd_circle(cx - 8, yy, 15 if i else 20), "#B9B3AA" if i else "#C9A27E", z=72, bevel=8, gloss=0.6)
    save("facial-ems", sc)


def hair_dryer():
    sc = Scene()
    sc.add(sd_capsule(610, 900, 360, 72, 72), "#2C2B2A", z=0, bevel=55, gloss=0.35)              # handle
    sc.add(sd_capsule(640, 560, 430, 165, 0), "#2C2B2A", z=20, bevel=110, gloss=0.35)             # body
    sc.add(sd_rbox(1015, 560, 170, 250, 70), "#3A3937", z=26, bevel=60, gloss=0.4)                # nozzle
    sc.add(sd_rbox(1090, 560, 40, 210, 18), "#C9A27E", z=100, bevel=14, gloss=0.85)                # nozzle ring
    sc.add(sd_circle(395, 560, 118), "#3A3937", z=140, bevel=40, gloss=0.3)                        # intake
    for r in (95, 70, 45, 20):
        sc.add(sd_circle(395, 560, r) * 1.0 + 0, "#262524" if r % 2 else "#4A4845", z=180 + (100 - r) * 0.05, bevel=6, gloss=0.2)
    sc.add(sd_rbox(585, 830, 60, 16, 8, 72), "#C9A27E", z=75, bevel=6, gloss=0.8)                 # switch
    save("hair-dryer", sc)


def face_brush():
    sc = Scene()
    sc.add(sd_capsule(700, 950, 380, 88, 90), "#E6EEEA", z=0, bevel=70, gloss=0.3)                # handle
    sc.add(sd_circle(700, 470, 250), "#E6EEEA", z=10, bevel=90, gloss=0.3)                         # head housing
    sc.add(sd_circle(700, 470, 200), "#F2D6DA", z=60, bevel=30, gloss=0.2)                         # silicone pad
    rng = np.random.default_rng(3)
    for r in range(18, 190, 22):                                                                  # silicone nubs
        n = max(1, int(2 * np.pi * r / 26))
        off = rng.uniform(0, 2 * np.pi)
        for k in range(n):
            a = off + 2 * np.pi * k / n
            sc.add(sd_circle(700 + r * np.cos(a), 470 + r * np.sin(a), 7.5), "#ECC4CA", z=95, bevel=6, gloss=0.35)
    sc.add(sd_circle(700, 860, 26), "#C9A27E", z=72, bevel=10, gloss=0.8)                          # button
    save("face-brush", sc)


if __name__ == "__main__":
    facial_ems()
    hair_dryer()
    face_brush()
