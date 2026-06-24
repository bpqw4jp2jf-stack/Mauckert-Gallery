#!/usr/bin/env python3
"""Recommend new, higher prices per artwork using the linear-index method.

Method (see 05 Strategie/Preisstrategie/00_Preisstrategie.md):
    Index price = (Höhe + Breite cm) × Index × Masterpiece-Faktor
The index is the lever. Benchmark for NEW emerging artists (cm/EUR):
    paintings on canvas 14-18, works on paper 12-16.
Ute currently sits at index ~4, so we raise in stages — each stage still below
the benchmark, so it stays defensible.

    Cost floor (safety net only) = (material + hours × rate) × markup

Final price per stage = round_to_point( max(index_price, cost_floor) ), min 120.

Reads : 05 Strategie/Inventar/Mauckert_Inventar_master.csv
Writes: 05 Strategie/Preisstrategie/Preisliste_neu.csv  (per-work, both stages)
        05 Strategie/Preisstrategie/Preisliste_neu.md   (summary)
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT.parent / "05 Strategie" / "Inventar" / "Mauckert_Inventar_master.csv"
OUT_DIR = ROOT.parent / "05 Strategie" / "Preisstrategie"
OUT_CSV = OUT_DIR / "Preisliste_neu.csv"
OUT_MD = OUT_DIR / "Preisliste_neu.md"

# --- knobs -----------------------------------------------------------------
# index by support and stage. Benchmark new-emerging: canvas 14-18, paper 12-16.
INDEX = {
    "stage1": {"canvas": 9, "paper": 8},
    "stage2": {"canvas": 14, "paper": 12},
}
MP_FACTOR = 1.15      # masterpiece (Hommage / Bargue) premium
MIN_PRICE = 120       # no original below this
HOURLY_RATE = 25.0    # EUR per artistic work-hour (cost floor only)
MARKUP = 2.0          # cost multiplier for the floor
# canvas if the technique/category mentions any of these, else "paper":
CANVAS_KW = ("acryl", "öl", "oel", "leinwand")
# ---------------------------------------------------------------------------


def num(s):
    if not s:
        return None
    try:
        return float(str(s).replace(",", ".").replace("€", "").strip())
    except ValueError:
        return None


def hw_sum(size):
    m = re.findall(r"\d+(?:\.\d+)?", (size or "").replace(",", "."))
    return float(m[0]) + float(m[1]) if len(m) >= 2 else None


def support(text):
    t = (text or "").lower()
    return "canvas" if any(k in t for k in CANVAS_KW) else "paper"


def price_point(x):
    """Round to a clean art price point (up)."""
    if x <= 0:
        return 0
    if x < 300:
        base = -(-x // 10) * 10
    elif x < 1000:
        base = -(-x // 25) * 25
    else:
        base = -(-x // 50) * 50
    return int(base)


def stage_price(hw, supp, mp, floor, stage, current=None):
    idx = INDEX[stage]["canvas" if supp == "canvas" else "paper"]
    index_price = hw * idx * (MP_FACTOR if mp else 1.0)
    candidates = [index_price] + ([floor] if floor else [])
    price = max(MIN_PRICE, price_point(max(candidates)))
    # never lower an existing price (Grundsatz: Preise nur erhöhen)
    return max(price, int(current)) if current else price


def main():
    rows = list(csv.DictReader(MASTER.open(encoding="utf-8")))
    out, no_size = [], 0

    for r in rows:
        hw = hw_sum(r.get("Maße (cm)"))
        supp = support((r.get("Technik") or "") + " " + (r.get("Kategorie") or ""))
        mp = r.get("Masterpiece") == "Ja"
        material = num(r.get("Materialkosten (€)"))
        hours = num(r.get("Arbeitsstunden"))
        floor = (material + hours * HOURLY_RATE) * MARKUP if (material is not None and hours is not None) else None
        current = num(r.get("Preis (€)"))

        if not hw:
            no_size += 1
            s1 = s2 = ""
            uplift = ""
        else:
            s1 = stage_price(hw, supp, mp, floor, "stage1", current)
            s2 = stage_price(hw, supp, mp, floor, "stage2", current)
            uplift = round(s1 / current, 2) if current else ""

        out.append({
            "Nr": r["Nr"],
            "Titel": r["Titel"],
            "Medium": supp,
            "Technik": r.get("Technik", ""),
            "Maße (cm)": r.get("Maße (cm)", ""),
            "H+W": int(hw) if hw else "",
            "Aktuell (€)": int(current) if current else "",
            "Stufe 1 (€)": s1,
            "Stufe 2 (€)": s2,
            "Faktor S1": uplift,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    import statistics as st
    sized = [o for o in out if o["Stufe 1 (€)"] != ""]
    cur = [o["Aktuell (€)"] for o in sized if o["Aktuell (€)"] != ""]
    s1 = [o["Stufe 1 (€)"] for o in sized]
    s2 = [o["Stufe 2 (€)"] for o in sized]

    lines = [
        "# Neue Preisliste (Index-Methode)",
        "",
        f"Berechnet für **{len(sized)} von {len(out)}** Werken mit Maßen "
        f"(Rest: erst Maße im Inventar ergänzen).",
        "",
        "| | Median | Min | Max |",
        "|---|--:|--:|--:|",
        f"| Aktuell | {st.median(cur):.0f} € | {min(cur)} € | {max(cur)} € |",
        f"| **Stufe 1** (Index Papier 8 / Leinwand 9) | {st.median(s1):.0f} € | {min(s1)} € | {max(s1)} € |",
        f"| **Stufe 2** (Index Papier 12 / Leinwand 14) | {st.median(s2):.0f} € | {min(s2)} € | {max(s2)} € |",
        "",
        f"- Median-Anhebung Stufe 1: **×{st.median(s1)/st.median(cur):.1f}**, "
        f"Stufe 2: **×{st.median(s2)/st.median(cur):.1f}** ggü. heute.",
        f"- Selbst Stufe 2 bleibt am unteren Rand der Einsteiger-Benchmark (Papier 12–16).",
        "",
        "## Beispiele",
        "",
        "| Nr | Titel | Maße | Aktuell | Stufe 1 | Stufe 2 |",
        "|---|---|---|--:|--:|--:|",
    ]
    examples = [o for o in sized if o["Aktuell (€)"] != ""]
    examples.sort(key=lambda o: -o["Aktuell (€)"])
    for o in examples[:6] + examples[-6:]:
        lines.append(f"| {o['Nr']} | {o['Titel'][:34]} | {o['Maße (cm)']} | "
                     f"{o['Aktuell (€)']} € | {o['Stufe 1 (€)']} € | {o['Stufe 2 (€)']} € |")
    lines += ["", "Volle Liste: `Preisliste_neu.csv`. Methode: `00_Preisstrategie.md`."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"{len(sized)}/{len(out)} Werke bepreist.")
    print(f"Median: heute {st.median(cur):.0f}€ → Stufe1 {st.median(s1):.0f}€ → Stufe2 {st.median(s2):.0f}€")
    print(f"→ {OUT_CSV.name} / {OUT_MD.name}")


if __name__ == "__main__":
    main()
