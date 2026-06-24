# Domain-Umzug: mauckertgallery.com von Wix weg → Cloudflare

**Warum:** Wix erlaubt keinen Nameserver-Wechsel. Damit die neue Cloudflare-Seite
unter `mauckertgallery.com` laufen kann, muss die Domain zu einem Registrar
umziehen, bei dem wir die Nameserver frei setzen können. Danach zeigen wir die
Nameserver auf Cloudflare → die schon vorbereitete Zone wird aktiv.

Cloudflare-Nameserver (stehen schon bereit): `brad.ns.cloudflare.com` ·
`emma.ns.cloudflare.com`

Status der neuen Seite: live & geprüft auf
`https://mauckertgallery.z2ryc6cm6c.workers.dev` (Wix-Seite weiterhin unberührt).

---

## Phase 1 — Bei Wix transferbereit machen  *(du, jetzt, ~10 Min)*

Im Wix-Konto → **Domains** → `mauckertgallery.com`:

1. **Domain-Sperre / Transfer Lock AUS** schalten (oft „Advanced" → „Transfer your
   domain away from Wix" / „Domain entsperren").
2. **WHOIS-/Datenschutz-Schutz AUS**, falls aktiv (manche Registrare brauchen das
   für den Transfer).
3. **Transfer-Authorization-Code (EPP-/Auth-Code) anfordern.** Wix zeigt ihn an
   oder schickt ihn per E-Mail.
4. Prüfen, dass die **E-Mail-Adresse der Domain aktuell** ist — die
   Bestätigungs-Mails laufen dorthin.

> Mögliche Hürde: Transfer geht nur, wenn die Domain **älter als 60 Tage** ist und
> in den letzten 60 Tagen kein Transfer/Inhaberwechsel war. (Bei uns vermutlich ok
> — registriert lange vor 2026.) Falls Wix blockt: Datum/Grund notieren.

---

## Phase 2 — Neuer Registrar & Transfer starten  *(du, ~15 Min + Wartezeit)*

Ziel-Registrar (einer reicht; muss freie Nameserver erlauben):
- **IONOS** — deutsch, deutscher Support (bequem, ~15 €/Jahr)
- **Porkbun** — günstig (~11 $/Jahr), einfach, englisch
- *(Cloudflare Registrar = am günstigsten, geht aber erst **später**: setzt voraus,
  dass die Domain schon auf Cloudflare-Nameservern läuft. Optionaler 2. Umzug in
  60+ Tagen.)*

Schritte:
1. Konto beim Ziel-Registrar anlegen.
2. **„Domain transfer / Domain umziehen"** → `mauckertgallery.com` eingeben.
3. **Auth-Code** aus Phase 1 eingeben, ~1 Jahr Verlängerung bezahlen (Pflicht beim
   Transfer, ~10–15 €).
4. Bestätigungs-Mails anklicken (kommen an die Domain-E-Mail + ggf. Wix-Freigabe).
5. **Warten: ~5–7 Tage** (ICANN-Vorgabe). Wix kann den Transfer auch vorzeitig
   freigeben.

---

## Phase 3 — Auf Cloudflare zeigen & Domain anhängen  *(zusammen, ~15 Min)*

Sobald die Domain beim neuen Registrar ist:
1. Beim neuen Registrar **Nameserver** setzen:
   `brad.ns.cloudflare.com` + `emma.ns.cloudflare.com`.
2. Cloudflare erkennt das → Zone wird **Active** (Minuten bis Stunden).
3. **Custom Domain an den Worker hängen:** `mauckertgallery.com` + `www` →
   macht Simon/Claude (Dashboard oder `wrangler`). SSL wird automatisch ausgestellt.
4. Testen (Browser privat + Handy). Fertig — die neue Seite ist unter der echten
   Domain live.

---

## Danach
- Wix: nur noch das **Hosting/Premium kündigen**. Die Domain ist dann eh weg.
- Optional später: Domain zu **Cloudflare Registrar** holen (günstigste
  Verlängerung) — geht, sobald sie auf Cloudflare-NS läuft.
- Optional: kostenloses **Cloudflare Email Routing** für `info@mauckertgallery.com`.

---

## Aktueller Stand (abhaken)
- [x] Phase 1: Auth-Code von Wix geholt, Domain entsperrt
- [x] Phase 2: Transfer bei **IONOS** gestartet (läuft seit 2026-06-11)
- [x] Phase 2: Wix-Transfer-Benachrichtigung erhalten (2026-06-12). **Nicht stoppen!**
      Wix-Auto-Freigabe-Frist: **2026-06-16 18:29 UTC (~20:29 Uhr MESZ)**. Danach
      läuft der Transfer automatisch durch. Optional in Wix vorzeitig freigeben.
- [x] Phase 2: Transfer abgeschlossen — Domain liegt bei **IONOS** (NS = `ui-dns.*`,
      Root zeigt auf IONOS-Parkseite `217.160.0.210`). Bestätigt am 2026-06-18.
- [ ] Phase 3: Nameserver bei IONOS auf Cloudflare gesetzt
      (`brad.ns.cloudflare.com` + `emma.ns.cloudflare.com`) → Zone Active  ← **DU, JETZT**
- [ ] Phase 3: Custom Domain am Worker, SSL aktiv, getestet
      (Config in `wrangler.jsonc` vorbereitet → danach `wrangler deploy`)  ← Claude
