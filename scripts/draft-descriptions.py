#!/usr/bin/env python3
"""Generate first-draft artwork descriptions for ALL works, in Ute's voice.

Honest by design: only uses what's really known (title, technique, place hints,
honoree for Hommagen). Every draft ends with a [Utes Notiz: …] placeholder where
her real personal detail belongs. Varies phrasing deterministically per work.

Reads : 05 Strategie/Inventar/Mauckert_Inventar_master.csv  (Nr, Titel, Slug, Kategorie, Maße)
        website/data/artworks.json                          (existing description, by slug)
Writes: 05 Strategie/Texte/Entwuerfe_alle_Werke.md          (review/edit here)
        05 Strategie/Texte/Entwuerfe_alle_Werke.csv          (slug, draft → for later import)
"""

import csv
import json
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT.parent / "05 Strategie" / "Inventar" / "Mauckert_Inventar_master.csv"
ART = ROOT / "data" / "artworks.json"
OUT_MD = ROOT.parent / "05 Strategie" / "Texte" / "Entwuerfe_alle_Werke.md"
OUT_CSV = ROOT.parent / "05 Strategie" / "Texte" / "Entwuerfe_alle_Werke.csv"

# --- known places (Rheintal & beyond); first match wins, longer first ---
PLACES = [
    "Taunusanlage", "Mäuseturm", "Rüdesheim", "Rümmelsheim", "Waldalgesheim",
    "Weiler", "Loreley", "Rheingau", "Rheinland", "Rheinhessen", "Bingen",
    "Frankfurt", "Allgäu", "Austria", "Italien", "Italienische", "Rügen", "Binz",
    "Mäuseturm", "Klopp", "Rhein", "Meer", "Ostsee", "Weinberg", "Berg",
]
# technique keyword (also matched in old description) -> phrase. Order matters.
TECH = [
    ("aquarell", "im Aquarell, nass und durchscheinend"),
    ("pastell", "in Pastell, Schicht für Schicht aufgebaut"),
    ("acryl", "in Acryl, kräftig gesetzt"),
    ("öl", "in Öl"),
    ("sepiakreide", "in Sepiakreide"),
    ("kreide", "in Kreide"),
    ("graphit", "im Graphit, Linie für Linie"),
    ("bleistift", "im Bleistift, Linie für Linie"),
    ("kohle", "in Kohle"),
    ("rötelstift", "im Rötel"),
    ("rötel", "im Rötel"),
    ("tusche", "in Tusche"),
    ("zeichnung", "als Zeichnung"),
    ("urban sketching", "als Urban Sketch, schnell vor Ort"),
]
STILL = ["hagebutte", "pilz", "steinpilz", "blüte", "apfel", "apfelblüte",
         "knoblauch", "traube", "traubenhyazinthe", "eichel", "stillleben",
         "blume", "rose", "mohn", "kürbis", "zwiebel", "kastanie", "nuss"]


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").replace("\xa0", " ").strip()


def pick(variants, key):
    return variants[zlib.crc32(key.encode()) % len(variants)]


def find_place(text):
    for p in PLACES:
        if re.search(rf"\b{re.escape(p)}", text, re.I):
            return "Italien" if p == "Italienische" else p
    return None


def tech_phrase(kategorie, technik, desc=""):
    src = (kategorie + " " + technik + " " + desc).lower()
    for k, v in TECH:
        if k in src:
            return v
    return "mit sicherer Hand gearbeitet"


def clean_honoree(s):
    s = re.sub(r"\s+(plate|graphit|kreide|bleistift).*$", "", s, flags=re.I)
    s = re.sub(r"\s+(i{1,3}|iv|v|\d+)\s*$", "", s, flags=re.I)  # trailing numbering
    return s.strip()


def honoree(title):
    m = re.search(r"hommage an\s+([A-Za-zÄÖÜäöü\.\- ]+)", title, re.I)
    if m:
        return clean_honoree(m.group(1).strip())
    m = re.search(r"\bnach\s+([A-Za-zÄÖÜäöü\.\- ]+)", title, re.I)
    if m:
        return clean_honoree(m.group(1).strip())
    return None


def classify(title, cats, desc):
    t = (title + " " + desc).lower()
    c = cats.lower()
    if "hommage" in t or "plate" in t or "bargue" in t or re.search(r"\bnach\b", t):
        return "hommage"
    if "urban" in c or "urban sketch" in t:
        return "urban"
    if re.search(r"\b(akt|akte|rückenakt|porträt|portrait|nackt)\b", t) or "getöntem papier" in t:
        return "figur"
    if any(w in t for w in STILL):
        return "stillleben"
    if "abstrakt" in c or "abstrakt" in t or "rhapsodie" in t:
        return "abstrakt"
    if find_place(title + " " + desc) or "landschaft" in t:
        return "landschaft"
    return "sonstige"


def draft(row, desc):
    title, cats, technik = row["Titel"], row["Kategorie"], row["Technik"]
    kind = classify(title, cats, desc)
    # prefer a place from the TITLE (the motif); the description often names only
    # the exhibition venue, which would mislabel the motif's location.
    place = find_place(title) or find_place(desc)
    tp = tech_phrase(cats, technik, desc)
    key = row["Slug"] or title

    if kind == "hommage":
        h = honoree(title) or "den alten Meistern"
        v = [
            f"Eine Studie als Hommage an {h} — {tp}. Solche Arbeiten schulen mein Auge für Linie und Form. [Utes Notiz: was dich an {h} reizt.]",
            f"Hommage an {h}: {tp}, reines Sehen. Für mich ist das die klassische Schule, aus der alles kommt. [Utes Notiz: warum gerade diese Vorlage.]",
            f"Nach {h} gearbeitet, {tp}. Hier geht es nicht um Effekt, sondern um genaues Hinschauen. [Utes Notiz: was du dabei gelernt/gesucht hast.]",
        ]
    elif kind == "urban":
        loc = place or "die Szene"
        v = [
            f"{loc}, mit wenigen schnellen Strichen vor Ort festgehalten. Urban Sketching ist für mich das Gegenteil vom Atelier — nur der Moment, das Tempo. [Utes Notiz: wo genau du gesessen hast.]",
            f"Ein Urban Sketch von {loc}: kein Korrigieren, nur Beobachten und das Leben der Stadt. [Utes Notiz: was dir an dem Tag aufgefallen ist.]",
            f"{loc}, unterwegs gezeichnet. Ich mag das Unfertige daran — es trägt den Augenblick in sich. [Utes Notiz: die Situation vor Ort.]",
        ]
    elif kind == "figur":
        v = [
            f"Eine Aktstudie aus meiner Zeichengruppe Porträt & Akt bei Hetty Krist in Frankfurt, {tp}. [Utes Notiz: was dich an dieser Haltung interessiert hat.]",
            f"Entstanden in der Zeichengruppe bei Hetty Krist: {tp}. Das genaue Sehen des Körpers ist für mich nie zu Ende gelernt. [Utes Notiz: der Moment im Aktsaal.]",
            f"Eine Figur, {tp}. Mich reizt die Spannung zwischen Ruhe und Bewegung im Körper. [Utes Notiz: was dieses Modell/diese Pose besonders macht.]",
        ]
    elif kind == "stillleben":
        v = [
            f"Ein kleines Stillleben, {tp}. Mich reizt das Unspektakuläre — Form, Farbe, ein Stück Natur ganz nah. [Utes Notiz: woher das Motiv kam (Garten, Spaziergang).]",
            f"{title} — {tp}. Solche Motive finde ich oft am Wegrand und nehme sie mit ins Atelier. [Utes Notiz: wo du es gefunden hast.]",
            f"Ein stilles Motiv, {tp}, so frisch wie möglich gehalten. [Utes Notiz: was dich daran festgehalten hat.]",
        ]
    elif kind == "abstrakt":
        v = [
            f"Aus einer Stimmung heraus entstanden, {tp}. Ich habe die Farbe führen lassen und erst spät eingegriffen. [Utes Notiz: die Stimmung, aus der es kam.]",
            f"Eine freie, abstrakte Arbeit, {tp} — Gefühl vor Motiv. [Utes Notiz: was du beim Malen empfunden hast.]",
            f"{title} — {tp}, ganz aus der Farbe heraus gedacht. [Utes Notiz: der Ausgangspunkt.]",
        ]
    elif kind == "landschaft":
        loc = place or "meine Heimat im Rheintal"
        v = [
            f"{loc}, {tp}. Am liebsten male ich vor Ort, wo Licht und Landschaft das Bild lebendig machen. [Utes Notiz: Tageszeit/Licht oder der Moment vor Ort.]",
            f"Eine Landschaft rund um {loc}, {tp}. [Utes Notiz: was dich an diesem Ort immer wieder hinzieht.]",
            f"{loc} — für mich ein Stück Heimat, {tp}. [Utes Notiz: Stimmung/Wetter an dem Tag.]",
        ]
    else:
        v = [
            f"{title}, {tp}. [Utes Notiz: der Moment oder Gedanke hinter diesem Werk.]",
            f"Eine Arbeit {tp}. [Utes Notiz: was dieses Werk für dich besonders macht.]",
        ]
    return pick(v, key)


def main():
    master = list(csv.DictReader(MASTER.open(encoding="utf-8")))
    desc_by_slug = {a["slug"]: strip_html(a.get("description")) for a in json.loads(ART.read_text())}

    rows = []
    for r in master:
        existing = desc_by_slug.get(r["Slug"], "")
        d = draft(r, existing)
        rows.append({"Nr": r["Nr"], "Slug": r["Slug"], "Titel": r["Titel"],
                     "Technik": r["Technik"] or r["Kategorie"], "Maße": r["Maße (cm)"],
                     "Bisher": existing, "Entwurf": d})

    # CSV
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Nr", "Slug", "Titel", "Entwurf"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ("Nr", "Slug", "Titel", "Entwurf")})

    # MD
    lines = [
        "# Werkbeschreibungen — Erst-Entwürfe (alle 132 Werke)",
        "",
        "Erzeugt nach dem Muster aus `00_Werkbeschreibungen_Leitfaden.md`. **Bitte als",
        "Entwurf lesen** und vor allem die `[Utes Notiz: …]`-Stellen mit echtem Detail",
        "füllen — dann sind die Texte zu 100 % authentisch. Der bisherige Text steht",
        "(falls vorhanden) zum Vergleich darunter.",
        "",
        "---",
        "",
    ]
    for r in rows:
        meta = " · ".join(x for x in (r["Technik"], (r["Maße"] + " cm") if r["Maße"] else "") if x)
        lines.append(f"### {r['Nr']} · {r['Titel']}")
        lines.append(f"*{meta}*" if meta else "")
        if r["Bisher"]:
            lines.append(f"> *Bisher:* {r['Bisher']}")
        lines.append(r["Entwurf"])
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # quick stats
    from collections import Counter
    kinds = Counter(classify(r["Titel"], r["Technik"] or "", desc_by_slug.get(r["Slug"], "")) for r in master)
    print(f"{len(rows)} Entwürfe → {OUT_MD.name} / {OUT_CSV.name}")
    print("Motiv-Verteilung:", dict(kinds))


if __name__ == "__main__":
    main()
