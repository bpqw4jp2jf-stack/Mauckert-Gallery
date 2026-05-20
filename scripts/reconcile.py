#!/usr/bin/env python3
"""Compare the Werkverzeichnis spreadsheet to what we scraped from the live site.

Outputs a markdown report flagging:
  - Works on the website that don't seem to be in the Werkverzeichnis
  - Works in the Werkverzeichnis that don't appear on the website

Title normalisation is conservative; treat results as hints, not gospel.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART_JSON = ROOT / "data" / "artworks.json"
WV_JSON = ROOT / "data" / "werkverzeichnis.json"
REPORT = ROOT / "data" / "reconciliation.md"


def norm(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def keywords(s: str) -> set[str]:
    return {w for w in norm(s).split() if len(w) >= 4}


def main() -> None:
    artworks = json.loads(ART_JSON.read_text())
    wv = json.loads(WV_JSON.read_text())

    wv_titles = [(r["titel"], norm(r["titel"])) for r in wv if r.get("titel")]
    art_titles = [(a["name"], norm(a["name"])) for a in artworks if a.get("name")]

    wv_norm_set = {n for _, n in wv_titles}
    art_norm_set = {n for _, n in art_titles}

    only_on_site = []
    for orig, n in art_titles:
        if n in wv_norm_set:
            continue
        # Try keyword overlap fallback
        kw = keywords(orig)
        match = None
        for wv_orig, wv_n in wv_titles:
            if kw and len(kw & keywords(wv_orig)) >= max(1, len(kw) // 2):
                match = wv_orig
                break
        only_on_site.append((orig, match))

    only_in_wv = []
    for orig, n in wv_titles:
        if n in art_norm_set:
            continue
        kw = keywords(orig)
        match = None
        for art_orig, art_n in art_titles:
            if kw and len(kw & keywords(art_orig)) >= max(1, len(kw) // 2):
                match = art_orig
                break
        only_in_wv.append((orig, match))

    lines = []
    lines.append("# Abgleich Website ↔ Werkverzeichnis\n")
    lines.append(f"- Werke auf Website: **{len(artworks)}**")
    lines.append(f"- Einträge im Werkverzeichnis: **{len(wv)}**\n")

    lines.append(f"## Werke auf der Website, die nicht eindeutig im Werkverzeichnis stehen ({len(only_on_site)})\n")
    lines.append("Stichwort-Match in Klammern = möglicher Treffer mit anderer Schreibweise.\n")
    for orig, match in sorted(only_on_site, key=lambda x: x[0].lower()):
        if match:
            lines.append(f"- {orig}  _(möglich: {match})_")
        else:
            lines.append(f"- {orig}")

    lines.append(f"\n## Werke im Werkverzeichnis, die nicht eindeutig auf der Website sind ({len(only_in_wv)})\n")
    for orig, match in sorted(only_in_wv, key=lambda x: x[0].lower()):
        if match:
            lines.append(f"- {orig}  _(möglich: {match})_")
        else:
            lines.append(f"- {orig}")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT}")
    print(f"  only on site: {len(only_on_site)}")
    print(f"  only in WV:   {len(only_in_wv)}")


if __name__ == "__main__":
    main()
