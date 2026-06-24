#!/usr/bin/env python3
"""Seed a customer/collector list from known buyers (inventory + Werkverzeichnis).

Aggregates every known buyer into one row: which works, how many, total spend.
Output is a STARTING point — contact details etc. are then maintained by hand.

Writes: 05 Strategie/Verkauf/Kundenliste.csv   (only if it doesn't exist yet,
        so hand edits are never overwritten; use --force to rebuild)
"""

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT.parent / "05 Strategie" / "Inventar" / "Mauckert_Inventar_master.csv"
WV = ROOT / "data" / "werkverzeichnis.json"
OUT = ROOT.parent / "05 Strategie" / "Verkauf" / "Kundenliste.csv"

HEADERS = [
    "Name", "Typ", "Kontakt", "Quelle", "Gekaufte Werke", "Anzahl",
    "Summe (€)", "Stammkäufer", "Letzter Kontakt", "Nächster Schritt", "Notiz",
]

# buyers that are organisations / exhibition partners rather than private collectors
ORGS = {"amf capital", "kuku vaia", "lume"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


def norm_title(s):
    """Title key for dedup: drop accents, punctuation and leading articles."""
    t = norm(s)
    t = re.sub(r"[^a-z0-9 ]+", "", t)
    t = re.sub(r"^(der|die|das|den|dem|ein|eine)\s+", "", t)
    return t.strip()


def main():
    if OUT.exists() and "--force" not in sys.argv:
        print(f"{OUT.name} existiert schon — nicht überschrieben. Mit --force neu bauen.")
        return

    buyers = {}  # norm_name -> dict

    def add(name, work, price):
        name = name.strip().rstrip(".,")
        if not name:
            return
        key = norm(name)
        b = buyers.setdefault(key, {"name": name, "works": [], "seen": set(), "sum": 0.0})
        tk = norm_title(work)
        if tk and tk in b["seen"]:
            return  # same work from the other source — don't double-count
        b["seen"].add(tk)
        b["works"].append(work)
        if price:
            b["sum"] += price

    # 1. master inventory (sold + buyer note)
    for r in csv.DictReader(MASTER.open(encoding="utf-8")):
        if r["Status"] == "Verkauft" and r["Käufer / Notiz"].strip():
            try:
                p = float(r["Preis (€)"].replace(",", ".")) if r["Preis (€)"].strip() else 0
            except ValueError:
                p = 0
            add(r["Käufer / Notiz"], r["Titel"], p)

    # 2. Werkverzeichnis "verkauft <Name>"
    for r in json.loads(WV.read_text()):
        st = (r.get("status") or "")
        if "verkauf" in st.lower():
            name = re.sub(r".*verkauft", "", st, flags=re.I).strip()
            if name:
                add(name, r.get("titel") or "", r.get("preis") or 0)

    rows = []
    for b in sorted(buyers.values(), key=lambda x: -x["sum"]):
        is_org = norm(b["name"]) in ORGS
        n = len(b["works"])
        rows.append({
            "Name": b["name"],
            "Typ": "Firma / Partner" if is_org else "Privat",
            "Kontakt": "",
            "Quelle": "",
            "Gekaufte Werke": "; ".join(b["works"]),
            "Anzahl": n,
            "Summe (€)": int(b["sum"]) if b["sum"] else "",
            "Stammkäufer": "Ja" if n >= 2 else "",
            "Letzter Kontakt": "",
            "Nächster Schritt": "",
            "Notiz": "",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} Käufer → {OUT.name}  (Stammkäufer: "
          f"{sum(1 for r in rows if r['Stammkäufer']=='Ja')})")


if __name__ == "__main__":
    main()
