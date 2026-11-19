"""Make a labelled contact sheet: contact_sheet.py OUT.png W H COLS img1 img2 ..."""
import sys
from PIL import Image, ImageDraw
out, w, h, cols, *files = sys.argv[1:]
w, h, cols = int(w), int(h), int(cols)
rows = (len(files) + cols - 1) // cols
pad, lab = 12, 26
sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + lab) + pad), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGBA")
    im.thumbnail((w, h), Image.LANCZOS)
    x, y = pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad + lab)
    bg = Image.new("RGBA", (w, h), (245, 240, 230, 255)); bg.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2))
    sheet.paste(bg.convert("RGB"), (x, y))
    d.text((x, y + h + 6), f.split("/")[-1], fill=(230, 230, 230))
sheet.save(out)
