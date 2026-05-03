"""Download WeChat/OpenClaw usage screenshots and arrange into a uniform collage."""
from __future__ import annotations
import urllib.request
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

URLS = [
    ("wechat_01", "https://github.com/user-attachments/assets/d035cdd9-7d0e-425a-9370-498c4a43400d"),
    ("wechat_02", "https://github.com/user-attachments/assets/10d3d91a-edec-4ce2-8f6d-e069076665db"),
    ("wechat_03", "https://github.com/user-attachments/assets/ca72c234-3121-4806-ae32-6822f7c22734"),
    ("wechat_04", "https://github.com/user-attachments/assets/94f5d829-a5dd-4070-9917-554ae28b057b"),
]

OUT_DIR = Path("docs/images")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CELL_W = 360
CELL_H = 720
COLS = 4
GAP = 24
BG_COLOR = (245, 245, 241)
LABEL_H = 28
LABEL_COLOR = (96, 113, 127)

def download_image(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGBA")

def fit_into(img: Image.Image, w: int, h: int) -> Image.Image:
    """Scale image to fit within w×h, maintaining aspect ratio, then paste on white bg."""
    img.thumbnail((w, h), Image.LANCZOS)
    bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    x = (w - img.width) // 2
    y = (h - img.height) // 2
    bg.paste(img, (x, y), img if img.mode == "RGBA" else None)
    return bg.convert("RGB")

# Download and crop
frames: list[tuple[str, Image.Image]] = []
for name, url in URLS:
    print(f"Downloading {name} ...")
    try:
        img = download_image(url)
        cell = fit_into(img, CELL_W, CELL_H)
        frames.append((name, cell))
        cell.save(OUT_DIR / f"{name}.png")
        print(f"  saved {OUT_DIR / name}.png  {cell.width}x{cell.height}")
    except Exception as e:
        print(f"  FAILED: {e}")

if not frames:
    print("No images downloaded; exiting.")
    raise SystemExit(1)

# Build collage
ncols = min(COLS, len(frames))
nrows = (len(frames) + ncols - 1) // ncols
total_w = ncols * CELL_W + (ncols + 1) * GAP
total_h = nrows * (CELL_H + LABEL_H) + (nrows + 1) * GAP

canvas = Image.new("RGB", (total_w, total_h), BG_COLOR)
try:
    font = ImageFont.truetype("arial.ttf", 14)
except Exception:
    font = ImageFont.load_default()

draw = ImageDraw.Draw(canvas)

for i, (name, img) in enumerate(frames):
    row = i // ncols
    col = i % ncols
    x = GAP + col * (CELL_W + GAP)
    y = GAP + row * (CELL_H + LABEL_H + GAP)
    canvas.paste(img, (x, y))
    label = f"Step {i+1}"
    draw.text((x + CELL_W // 2, y + CELL_H + 6), label, font=font, fill=LABEL_COLOR, anchor="mt")

out_path = OUT_DIR / "usage_flow_collage.png"
canvas.save(out_path, optimize=True)
print(f"\nCollage saved: {out_path}  ({total_w}x{total_h})")
