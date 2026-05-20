#!/usr/bin/env python3
"""Re-fetch each product page from Wix and pull richer metadata.

Captures ribbon, comparePrice, discountedPrice, additionalInfoSections,
plain-text description, isInStock and any 'Masterpiece' or 'verkauft' hints.
Writes data/artworks_enriched.json with the merged result.
"""

import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "artworks.json"
OUT = ROOT / "data" / "artworks_enriched.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})

WARMUP = re.compile(r'<script[^>]*id="wix-warmup-data"[^>]*>(.+?)</script>', re.DOTALL)


def find_product(o):
    if isinstance(o, dict):
        if "name" in o and "urlPart" in o and "media" in o and "price" in o:
            return o
        for v in o.values():
            r = find_product(v)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = find_product(v)
            if r:
                return r


def strip_html(html: str) -> str:
    if not html:
        return ""
    txt = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    txt = re.sub(r"</p>", "\n", txt, flags=re.IGNORECASE)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\n{2,}", "\n", txt)
    return txt.strip()


YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
SIZE_RE = re.compile(r"(\d{1,3}[.,]?\d{0,2})\s*[x×]\s*(\d{1,3}[.,]?\d{0,2})\s*(?:cm|mm)?", re.IGNORECASE)
FRAMED_HINT = re.compile(r"\bgerahmt|gerahmtes|im Rahmen\b", re.IGNORECASE)
SOLD_HINT = re.compile(r"\bverkauft|sold\b", re.IGNORECASE)
MP_HINT = re.compile(r"\bMP\b|masterpiece|hommage", re.IGNORECASE)


def enrich_one(art):
    url = art["source_url"]
    try:
        html = S.get(url, timeout=30).text
    except Exception as e:
        print(f"  ! fetch failed: {e}", file=sys.stderr)
        return None
    m = WARMUP.search(html)
    if not m:
        return None
    data = json.loads(m.group(1))
    p = find_product(data)
    if not p:
        return None
    desc_raw = p.get("description") or ""
    desc_text = strip_html(desc_raw)
    # Search filename titles too (e.g. "Foo 2024.jpeg")
    media_titles = " ".join(m.get("title") or "" for m in p.get("media") or [])
    blob = " ".join([art["name"], desc_text, media_titles])

    year_match = YEAR_RE.search(blob)
    size_match = SIZE_RE.search(blob)
    return {
        "ribbon": p.get("ribbon") or "",
        "additionalRibbons": p.get("additionalRibbons") or [],
        "comparePrice": p.get("comparePrice"),
        "formattedComparePrice": p.get("formattedComparePrice") or "",
        "discountedPrice": p.get("discountedPrice"),
        "isInStock": p.get("isInStock"),
        "inventory_status": (p.get("inventory") or {}).get("status"),
        "description_raw": desc_raw,
        "description_text": desc_text,
        "year_guess": int(year_match.group(0)) if year_match else None,
        "size_guess": f"{size_match.group(1)} x {size_match.group(2)} cm" if size_match else "",
        "framed_hint": bool(FRAMED_HINT.search(blob)),
        "sold_hint": bool(SOLD_HINT.search(blob)),
        "mp_hint": bool(MP_HINT.search(art["name"])) or "hommage" in art["name"].lower(),
    }


def main() -> int:
    artworks = json.loads(SRC.read_text())
    out = []
    for i, a in enumerate(artworks, 1):
        extra = enrich_one(a)
        merged = {**a}
        if extra:
            merged["enrichment"] = extra
        out.append(merged)
        if i % 10 == 0 or i == len(artworks):
            print(f"[{i}/{len(artworks)}]")
        time.sleep(0.15)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT.relative_to(ROOT)}")
    # Summary
    ribbons = {}
    for a in out:
        r = (a.get("enrichment") or {}).get("ribbon", "")
        if r:
            ribbons[r] = ribbons.get(r, 0) + 1
    print(f"Ribbons seen: {ribbons or 'none'}")
    n_sold = sum(1 for a in out if (a.get("enrichment") or {}).get("sold_hint"))
    n_oos = sum(1 for a in out if (a.get("enrichment") or {}).get("isInStock") is False)
    n_mp = sum(1 for a in out if (a.get("enrichment") or {}).get("mp_hint"))
    print(f"sold hints: {n_sold} · not in stock: {n_oos} · MP/Hommage hints: {n_mp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
