#!/usr/bin/env python3
"""Scrape artworks from the live Wix Mauckert Gallery site.

Reads the sitemap, fetches every product page, extracts product data from the
embedded `wix-warmup-data` JSON blob, downloads original images, and writes a
single `artworks.json` we can drive the new site from.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMAGES_DIR = ROOT / "public" / "images" / "artworks"
ARTWORKS_JSON = DATA_DIR / "artworks.json"
CATEGORIES_JSON = DATA_DIR / "categories.json"

SITE = "https://www.mauckertgallery.com"
PRODUCTS_SITEMAP = f"{SITE}/store-products-sitemap.xml"
GRAPHIT_CATEGORY = f"{SITE}/category/graphit"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

WARMUP_RE = re.compile(r'<script[^>]*id="wix-warmup-data"[^>]*>(.+?)</script>', re.DOTALL)


SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


def fetch(url: str) -> str:
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def fetch_bytes(url: str) -> bytes:
    r = SESSION.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def parse_warmup(html: str) -> dict[str, Any] | None:
    m = WARMUP_RE.search(html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def find_product(o: Any) -> dict | None:
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
    return None


def find_categories(o: Any, found: dict[str, dict]) -> None:
    """Collect category objects {id, name, slug} from any page's warmup data."""
    if isinstance(o, dict):
        cid = o.get("id")
        slug = o.get("slug")
        name = o.get("name")
        if (
            isinstance(cid, str)
            and len(cid) == 36
            and isinstance(slug, str)
            and slug
            and name
        ):
            if cid not in found:
                found[cid] = {"id": cid, "name": name, "slug": slug}
        for v in o.values():
            find_categories(v, found)
    elif isinstance(o, list):
        for v in o:
            find_categories(v, found)


def list_product_urls() -> list[str]:
    xml = fetch(PRODUCTS_SITEMAP)
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def build_category_map() -> dict[str, dict]:
    """Hit one category page; the embedded warmup data lists every category."""
    html = fetch(GRAPHIT_CATEGORY)
    data = parse_warmup(html)
    found: dict[str, dict] = {}
    if data:
        find_categories(data, found)
    return found


def wix_image_full_url(media_id: str) -> str:
    """Reconstruct a high-resolution Wix image URL.

    Wix stores originals at `https://static.wixstatic.com/media/{id}` but the
    direct path serves the actual binary. To force a reasonable display size we
    use a 2000px-wide variant; downloading uses the raw path for the archive.
    """
    return f"https://static.wixstatic.com/media/{media_id}"


def wix_image_display_url(media_id: str, width: int = 1600) -> str:
    return (
        f"https://static.wixstatic.com/media/{media_id}/v1/fit/"
        f"w_{width},q_90/file.jpg"
    )


def extract_artwork(url: str, category_lookup: dict[str, dict]) -> dict | None:
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  ! fetch failed: {e}", file=sys.stderr)
        return None
    data = parse_warmup(html)
    if not data:
        return None
    # Capture any categories embedded on this page too (cheap, idempotent).
    find_categories(data, category_lookup)
    p = find_product(data)
    if not p:
        return None

    cat_ids = p.get("categoryIds") or []
    cat_names = []
    cat_slugs = []
    for cid in cat_ids:
        c = category_lookup.get(cid)
        if c:
            cat_names.append(c["name"])
            cat_slugs.append(c["slug"])

    media = []
    for m in p.get("media") or []:
        mid = m.get("id") or m.get("url")
        if not mid:
            continue
        media.append(
            {
                "id": mid,
                "title": m.get("title"),
                "width": m.get("width"),
                "height": m.get("height"),
                "original_url": wix_image_full_url(mid),
                "display_url": wix_image_display_url(mid, 1600),
            }
        )

    return {
        "slug": p.get("urlPart"),
        "name": p.get("name"),
        "description": (p.get("description") or "").strip(),
        "price": p.get("price"),
        "currency": p.get("currency"),
        "formatted_price": p.get("formattedPrice"),
        "category_ids": cat_ids,
        "categories": cat_names,
        "category_slugs": cat_slugs,
        "in_stock": p.get("isInStock"),
        "media": media,
        "source_url": url,
    }


def safe_name(s: str) -> str:
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE)
    return s.strip("_") or "image"


def download_images(artworks: list[dict]) -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for art in artworks:
        slug = art["slug"]
        for i, m in enumerate(art["media"]):
            ext = ".jpg"
            title = m.get("title") or ""
            mt = re.search(r"\.(jpe?g|png|webp)$", title, re.IGNORECASE)
            if mt:
                ext = "." + mt.group(1).lower().replace("jpeg", "jpg")
            fname = f"{slug}__{i}{ext}"
            out = IMAGES_DIR / fname
            m["local_path"] = f"/images/artworks/{fname}"
            if out.exists() and out.stat().st_size > 0:
                continue
            try:
                blob = fetch_bytes(m["original_url"])
                out.write_bytes(blob)
                print(f"    img {fname} ({len(blob)//1024} KB)")
                time.sleep(0.2)
            except Exception as e:
                print(f"    ! image failed {fname}: {e}", file=sys.stderr)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Building category map...")
    cat_lookup = build_category_map()
    print(f"  {len(cat_lookup)} categories found")

    print("Listing product URLs...")
    urls = list_product_urls()
    print(f"  {len(urls)} products in sitemap")

    artworks = []
    for i, u in enumerate(urls, 1):
        slug = u.rstrip("/").rsplit("/", 1)[-1]
        slug = urllib.parse.unquote(slug)
        print(f"[{i}/{len(urls)}] {slug}")
        art = extract_artwork(u, cat_lookup)
        if art:
            artworks.append(art)
        else:
            print(f"  ! could not extract product from {u}", file=sys.stderr)
        time.sleep(0.25)

    print(f"\nExtracted {len(artworks)} artworks")

    # Persist categories first so re-runs reuse them.
    CATEGORIES_JSON.write_text(
        json.dumps(sorted(cat_lookup.values(), key=lambda c: c["name"]), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nDownloading images...")
    download_images(artworks)

    ARTWORKS_JSON.write_text(
        json.dumps(artworks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {ARTWORKS_JSON.relative_to(ROOT)}")
    print(f"Wrote {CATEGORIES_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
