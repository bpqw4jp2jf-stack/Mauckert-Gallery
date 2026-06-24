#!/usr/bin/env python3
"""Generate brand-styled Certificates of Authenticity (Echtheitszertifikate).

Self-contained, print-ready A5 HTML (open in browser → Cmd/Ctrl+P → Save as PDF).
Brand optics: navy/cream, Cormorant Garamond + Inter, MG monogram. The artwork
photo is embedded (base64) so each file is portable and printable on its own.

Usage:
  python3 scripts/build-certificate.py            # blank template + all SOLD works
  python3 scripts/build-certificate.py MG-046 MG-093   # specific works
  python3 scripts/build-certificate.py --all      # every work in the inventory

Output: 05 Strategie/Verkauf/Zertifikate/
  Zertifikat_Vorlage.html                  (blank, fill by hand / print generically)
  Zertifikat_<Nr>_<Titel>.html             (filled per work)
"""

import base64
import csv
import mimetypes
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT.parent / "05 Strategie" / "Inventar" / "Mauckert_Inventar_master.csv"
BILDER = ROOT.parent / "05 Strategie" / "Inventar" / "Bilder"
LOGO = ROOT / "public" / "logo-mg.svg"
OUT = ROOT.parent / "05 Strategie" / "Verkauf" / "Zertifikate"

NAVY, CREAM, CLAY, STONE = "#121920", "#FCF9E4", "#B98272", "#C7BFA8"


def logo_svg():
    svg = LOGO.read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml.*?\?>", "", svg, flags=re.S).strip()
    return svg


def img_data_uri(nr):
    """Find the renamed work image '… - <Nr>.<ext>' (or '… - <Nr> (1).<ext>')."""
    matches = sorted(BILDER.glob(f"* - {nr}.*")) or sorted(BILDER.glob(f"* - {nr} (*).*"))
    for p in matches:
        mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f"data:{mime};base64,{b64}"
    return None


def safe_filename(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9 _-]+", "", s)
    return re.sub(r"\s+", "_", s).strip("_")


def field(label, value):
    return (f'<div class="row"><span class="lbl">{label}</span>'
            f'<span class="val">{value or "&nbsp;"}</span></div>')


def render(data, image_uri):
    """data: dict with keys Nr, Titel, Jahr, Technik, Maße. Empty value → blank line."""
    img_block = (f'<div class="art"><img src="{image_uri}" alt=""></div>'
                 if image_uri else "")
    rows = "".join([
        field("Werk-Nr.", data.get("Nr")),
        field("Titel", data.get("Titel")),
        field("Jahr", data.get("Jahr")),
        field("Technik", data.get("Technik")),
        field("Maße", (data.get("Maße") + " cm") if data.get("Maße") else ""),
    ])
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<title>Echtheitszertifikat {data.get('Nr','')} {data.get('Titel','')}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@400;500&display=swap');
  @page {{ size: A5 portrait; margin: 0; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', Helvetica, Arial, sans-serif; color: {NAVY}; }}
  .page {{
    width: 148mm; height: 210mm; padding: 16mm 15mm; margin: 0 auto;
    background: {CREAM}; position: relative;
    border: 1.5mm solid {NAVY}; outline: 0.4mm solid {CLAY}; outline-offset: -3mm;
    display: flex; flex-direction: column;
  }}
  .brand {{ display:flex; align-items:center; gap:3mm; justify-content:center; }}
  .brand svg {{ width: 14mm; height: 14mm; color: {NAVY}; }}
  .brand .name {{ font-family:'Cormorant Garamond', Georgia, serif; font-size: 15pt;
    letter-spacing: .28em; text-transform: uppercase; }}
  .title {{ text-align:center; margin: 7mm 0 1mm; }}
  .title h1 {{ font-family:'Cormorant Garamond', Georgia, serif; font-weight:600;
    font-size: 26pt; margin: 0; }}
  .title .sub {{ font-size: 8pt; letter-spacing:.32em; text-transform:uppercase;
    color: {CLAY}; }}
  .rule {{ width: 28mm; height: 0; border-top: 0.4mm solid {CLAY}; margin: 4mm auto; }}
  .intro {{ text-align:center; font-size: 9.5pt; color:#33414e; margin: 0 4mm 5mm; }}
  .art {{ text-align:center; margin: 1mm 0 4mm; }}
  .art img {{ max-height: 52mm; max-width: 80%; border: 0.6mm solid {STONE};
    box-shadow: 0 1mm 3mm rgba(0,0,0,.12); }}
  .data {{ margin: 0 2mm; }}
  .row {{ display:flex; padding: 1.7mm 0; border-bottom: 0.2mm dotted {STONE}; }}
  .row .lbl {{ flex: 0 0 30mm; font-size: 8pt; letter-spacing:.12em;
    text-transform:uppercase; color:{CLAY}; padding-top: .6mm; }}
  .row .val {{ flex:1; font-family:'Cormorant Garamond', Georgia, serif; font-size: 13pt; }}
  .statement {{ font-size: 9pt; color:#33414e; text-align:center; margin: 5mm 4mm 0;
    line-height: 1.5; }}
  .foot {{ margin-top:auto; display:flex; justify-content:space-between; gap:8mm;
    padding-top: 6mm; }}
  .sig {{ flex:1; text-align:center; }}
  .sig .line {{ border-top: 0.3mm solid {NAVY}; margin-bottom: 1mm; height: 12mm; }}
  .sig .cap {{ font-size: 7.5pt; letter-spacing:.1em; text-transform:uppercase; color:{CLAY}; }}
  .sig .nm {{ font-family:'Cormorant Garamond', Georgia, serif; font-size: 11pt; }}
  .web {{ text-align:center; font-size: 7.5pt; letter-spacing:.2em; color:{STONE};
    margin-top: 5mm; text-transform: uppercase; }}
</style></head>
<body>
  <div class="page">
    <div class="brand">{logo_svg()}<span class="name">Mauckert&nbsp;Gallery</span></div>
    <div class="title">
      <h1>Echtheitszertifikat</h1>
      <div class="sub">Certificate of Authenticity</div>
    </div>
    <div class="rule"></div>
    <p class="intro">Hiermit bestätige ich die Echtheit des nachstehenden Originalwerks
      aus meiner Hand.</p>
    {img_block}
    <div class="data">{rows}</div>
    <p class="statement">Das Werk ist ein von Hand gefertigtes Unikat, von mir
      persönlich signiert und in meinem Werkverzeichnis unter obiger Nummer geführt.</p>
    <div class="foot">
      <div class="sig"><div class="line"></div><div class="cap">Ort, Datum</div></div>
      <div class="sig"><div class="line"></div><div class="cap">Unterschrift</div>
        <div class="nm">Ute Mauckert</div></div>
    </div>
    <div class="web">www.mauckertgallery.com</div>
  </div>
</body></html>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(MASTER.open(encoding="utf-8")))
    by_nr = {r["Nr"]: r for r in rows}

    # blank template (placeholders as underscores; no image box)
    blank = {k: "" for k in ("Nr", "Titel", "Jahr", "Technik", "Maße")}
    (OUT / "Zertifikat_Vorlage.html").write_text(render(blank, None), encoding="utf-8")

    args = [a for a in sys.argv[1:]]
    if "--all" in args:
        targets = [r["Nr"] for r in rows]
    elif args:
        targets = args
    else:  # default: all sold works
        targets = [r["Nr"] for r in rows if r["Status"] == "Verkauft"]

    made = 0
    for nr in targets:
        r = by_nr.get(nr)
        if not r:
            print(f"  ! {nr} nicht im Inventar")
            continue
        data = {"Nr": r["Nr"], "Titel": r["Titel"], "Jahr": r["Jahr"],
                "Technik": r["Technik"], "Maße": r["Maße (cm)"]}
        html = render(data, img_data_uri(nr))
        fn = f"Zertifikat_{nr}_{safe_filename(r['Titel'])[:40]}.html"
        (OUT / fn).write_text(html, encoding="utf-8")
        made += 1

    print(f"Vorlage → Zertifikat_Vorlage.html")
    print(f"{made} ausgefüllte Zertifikate → {OUT.relative_to(ROOT.parent)}/")


if __name__ == "__main__":
    main()
