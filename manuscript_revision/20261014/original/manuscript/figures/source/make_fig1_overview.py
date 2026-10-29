"""Build manuscript/figures/fig1_overview.pdf from the authors' Canva export.

Source (unchanged): figures/source/fig1_overview_original_canva.pdf
Changes, all label-level, made because they contradicted the dataset documentation
(Electrodelocation.pdf; reports/grabmyo_electrode_geometry.md):
  1. inter-ring distance "3 cm" -> "2 cm"
  2. ring numbering swapped so the proximal ring (nearer the elbow) is F1-F8 and the distal ring
     F9-F16, as in the dataset's electrode-location diagram (ring 1 = electrodes 1-8, elbow side)
  3. the page is cropped to the artwork (the export has wide blank margins)
Everything else in the artwork is untouched.
"""
from pathlib import Path

import fitz
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE / "fig1_overview_original_canva.pdf"
OUT = HERE.parent / "fig1_overview.pdf"
FIXES = {"3 cm": "2 cm", "F9 - F16": "F1 - F8", "F1 - F8": "F9 - F16"}

doc = fitz.open(SRC)
pg = doc[0]
hi = pg.get_pixmap(dpi=144)


def background(r):
    c = hi.pixel(int((r.x0 - 1) * 2), int((r.y0 + r.y1) * 1))
    return tuple(v / 255 for v in c[:3])


spans = [s for b in pg.get_text("dict")["blocks"] for l in b.get("lines", [])
         for s in l["spans"] if s["text"].strip() in FIXES]
assert len(spans) == 3, [s["text"] for s in spans]
for s in spans:
    r = fitz.Rect(s["bbox"])
    pg.draw_rect(r + (-0.5, -0.5, 0.5, 0.5), color=None, fill=background(r), overlay=True)
    col = s["color"]
    rgb = (((col >> 16) & 255) / 255, ((col >> 8) & 255) / 255, (col & 255) / 255)
    # embedded font (IOP requires all fonts embedded); Arial Italic is close to Garet Italic
    pg.insert_text((r.x0, r.y1 - 2.4), FIXES[s["text"].strip()], fontname="ArialItalic",
                   fontfile="C:/Windows/Fonts/ariali.ttf", fontsize=s["size"] * 0.95, color=rgb,
                   overlay=True)

# crop box from rendered pixels (the export has a full-page white background)
lo = pg.get_pixmap(dpi=72)
a = np.frombuffer(lo.samples, dtype=np.uint8).reshape(lo.h, lo.w, lo.n)[:, :, :3]
ys, xs = np.where((a < 245).any(2))
clip = fitz.Rect(xs.min() - 6, ys.min() - 6, xs.max() + 7, ys.max() + 7) & pg.rect

tmp = fitz.open()
tmp.insert_pdf(doc)
out = fitz.open()
page = out.new_page(width=clip.width, height=clip.height)
page.show_pdf_page(page.rect, tmp, 0, clip=clip)
out.save(OUT, garbage=3, deflate=True)
print("wrote", OUT, "size", round(clip.width), "x", round(clip.height), "pt")
