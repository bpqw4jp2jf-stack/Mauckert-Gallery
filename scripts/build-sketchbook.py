#!/usr/bin/env python3
"""Resize Scetchbook II images for the slideshow and emit a JSON list."""

import json
import re
import unicodedata
from pathlib import Path

from PIL import Image, ImageOps

SRC = Path("../../01 Kunstwerke/02 Bereits Hochgeladen/Scetchbook II").resolve()
ROOT = Path(__file__).resolve().parents[1]
PUB_DIR = ROOT / "public" / "images" / "sketchbook"
DATA = ROOT / "data" / "sketchbook.json"

MAX_LONG = 1600
THUMB_LONG = 400
QUALITY = 85

# Keywords that mean the work has color → exclude from "Zeichnungen" slideshow
COLOR_KEYWORDS = {
    "aquarell", "acryl", "pastell", "pastellkreide", "buntstift",
    "oelstift", "ölstift", "mixed", "öl", "leinwand", "steinpapier",
    "fineliner",
}
# Keywords confirming a pure drawing
DRAWING_KEYWORDS = {
    "graphit", "graphitstift", "bleistift", "kohle", "kohlestift",
    "sepia", "sepiakreide", "kreide", "rötelstift", "plate",
    "bargue", "zeichnung",
}


def is_drawing(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in COLOR_KEYWORDS):
        return False
    return any(kw in t for kw in DRAWING_KEYWORDS)


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def main() -> None:
    PUB_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    skipped = []
    files = sorted(p for p in SRC.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    for i, src in enumerate(files, 1):
        stem = src.stem.strip()
        if not is_drawing(stem):
            skipped.append(stem)
            continue
        slug = slugify(stem)
        out_main = PUB_DIR / f"{i:02d}-{slug}.jpg"
        out_thumb = PUB_DIR / f"{i:02d}-{slug}-thumb.jpg"
        if not (out_main.exists() and out_thumb.exists()):
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)
                im = im.convert("RGB")
                im.thumbnail((MAX_LONG, MAX_LONG), Image.Resampling.LANCZOS)
                im.save(out_main, "JPEG", quality=QUALITY, optimize=True)
                im.thumbnail((THUMB_LONG, THUMB_LONG), Image.Resampling.LANCZOS)
                im.save(out_thumb, "JPEG", quality=80, optimize=True)
        items.append({
            "title": stem,
            "src": f"/images/sketchbook/{out_main.name}",
            "thumb": f"/images/sketchbook/{out_thumb.name}",
        })
        print(f"[{i:2d}/{len(files)}] keep  {stem}")
    DATA.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    # Delete files for excluded items from previous runs
    expected = {Path(it["src"]).name for it in items} | {Path(it["thumb"]).name for it in items}
    for f in PUB_DIR.iterdir():
        if f.name not in expected:
            f.unlink()
            print(f"  removed {f.name}")
    print(f"\nKept {len(items)} drawings, excluded {len(skipped)} color works:")
    for s in skipped:
        print(f"  ✗  {s}")
    print(f"\nData: {DATA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
