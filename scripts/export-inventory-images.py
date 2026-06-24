#!/usr/bin/env python3
"""Copy each work's website image into a human-named library for the inventory.

Source : website/public/images/artworks/<slug>__N.<ext>  (the live site images)
Target : ../05 Strategie/Inventar/Bilder/<Titel> - <MG-Nr>.<ext>

Non-destructive: the website's own slug-named files are left untouched. The MG
number is the row order of data/artworks_enriched.json, identical to the order
build-master-inventory.py uses, so MG-001 here == MG-001 in the Excel.

Multiple images for one work get a suffix:  "<Titel> - MG-007 (2).jpg".
"""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENRICHED = ROOT / "data" / "artworks_enriched.json"
PUBLIC = ROOT / "public"
OUT_DIR = ROOT.parent / "05 Strategie" / "Inventar" / "Bilder"

# characters not allowed / awkward in filenames
BAD = re.compile(r'[\\/:*?"<>|]+')


def safe(name: str) -> str:
    name = BAD.sub("-", name)          # path separators etc.
    name = re.sub(r"\s+", " ", name)   # collapse whitespace
    return name.strip().rstrip(".")    # no trailing dot/space


def main() -> None:
    works = json.loads(ENRICHED.read_text())
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    copied = missing = 0
    for idx, a in enumerate(works, 1):
        nr = f"MG-{idx:03d}"
        title = safe(a["name"])
        media = a.get("media") or []
        for mi, m in enumerate(media):
            lp = m.get("local_path") or ""
            src = PUBLIC / lp.lstrip("/")
            if not src.exists():
                print(f"  ! missing image for {nr} {a['name']}: {lp}")
                missing += 1
                continue
            ext = src.suffix.lower()
            suffix = "" if len(media) == 1 else f" ({mi + 1})"
            dest = OUT_DIR / f"{title} - {nr}{suffix}{ext}"
            shutil.copy2(src, dest)
            copied += 1

    print(f"Copied {copied} images → {OUT_DIR.relative_to(ROOT.parent)}")
    if missing:
        print(f"{missing} works had no local image on disk.")


if __name__ == "__main__":
    main()
