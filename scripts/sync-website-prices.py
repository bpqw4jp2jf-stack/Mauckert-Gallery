#!/usr/bin/env python3
"""Sync website artwork prices to the master inventory (today's Stufe-1 prices).

For each artwork in data/artworks.json, look up the matching master row by slug
and copy its price into `price` + `formatted_price`. Available works get the new
Stufe-1 price; sold works keep their historical price (already so in the master),
so this is safe. Backs up artworks.json first.
"""

import json
import csv
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data" / "artworks.json"
MASTER = ROOT.parent / "05 Strategie" / "Inventar" / "Mauckert_Inventar_master.csv"


def de_money(v):
    s = f"{v:,.2f}"                       # 1,350.00
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")  # -> 1.350,00
    return s + "€"


def main():
    artworks = json.loads(ART.read_text(encoding="utf-8"))
    master = {r["Slug"]: r for r in csv.DictReader(MASTER.open(encoding="utf-8")) if r["Slug"]}

    changed = []
    for a in artworks:
        r = master.get(a.get("slug"))
        if not r or not r["Preis (€)"].strip():
            continue
        try:
            new = int(float(r["Preis (€)"].replace(",", ".")))
        except ValueError:
            continue
        if a.get("price") != new:
            changed.append((a["name"], a.get("price"), new))
            a["price"] = new
            a["formatted_price"] = de_money(new)

    if changed:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(ART, ART.with_name(f"artworks.backup-{ts}.json"))
        ART.write_text(json.dumps(artworks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(changed)} Preise auf der Website aktualisiert (Backup: artworks.backup-*.json)")
    for n, old, new in changed[:8]:
        print(f"  {n[:34]:34} {old}€ -> {new}€")


if __name__ == "__main__":
    main()
