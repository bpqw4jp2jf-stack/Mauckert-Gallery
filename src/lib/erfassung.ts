// Werk-Erfassung: führt alle vorhandenen Werk-Infos aus den bestehenden Datenquellen
// zusammen ("detect all infos"), bestimmt Vollständigkeit und vergibt Werk-Nummern
// (vollständige Werke zuerst: 001, 002, …, danach die unvollständigen).
//
// Reine Logik – kein Dateizugriff. Wird von der Seite und der API-Route geteilt.

import artworksData from "../../data/artworks.json";
import enrichedData from "../../data/artworks_enriched.json";
import sketchbookData from "../../data/sketchbook.json";
import werkverzeichnisData from "../../data/werkverzeichnis.json";

export interface ErfassungRecord {
  id: string;                       // stabile ID (artwork-slug oder sketchbook-<n>)
  quelle: "artwork" | "sketchbook";
  bild: string;                     // lokaler Bildpfad (/images/...)
  titel: string;
  jahr: string;
  technik: string;
  masse: string;                    // "Breite x Höhe"
  preis: string;
  status: string;                   // z.B. "verfügbar" / "verkauft"
  notiz: string;
}

export type ErfassungFeld = keyof Omit<ErfassungRecord, "id" | "quelle" | "bild">;

// Felder, die für ein "vollständiges" Werk vorhanden sein müssen.
export const PFLICHTFELDER: ErfassungFeld[] = [
  "titel",
  "jahr",
  "technik",
  "masse",
  "preis",
  "status",
];

export const FELD_LABEL: Record<ErfassungFeld, string> = {
  titel: "Titel",
  jahr: "Jahr",
  technik: "Technik / Medium",
  masse: "Maße (B × H cm)",
  preis: "Preis €",
  status: "Status",
  notiz: "Notiz",
};

// ---------------------------------------------------------------------------
// Fuzzy-Helfer (Dice-Koeffizient über Bigramme) für Dedupe & Cross-Reference
// ---------------------------------------------------------------------------

function normalize(s: string): string {
  return String(s ?? "")
    .toLowerCase()
    .replace(/\bhommage an\b|\bhomage an\b|\bnach\b/g, " ")
    .replace(/[^a-zäöüß0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function bigrams(s: string): Map<string, number> {
  const m = new Map<string, number>();
  for (let i = 0; i < s.length - 1; i++) {
    const bg = s.slice(i, i + 2);
    m.set(bg, (m.get(bg) ?? 0) + 1);
  }
  return m;
}

function dice(a: string, b: string): number {
  if (!a || !b) return 0;
  if (a === b) return 1;
  const ba = bigrams(a);
  const bb = bigrams(b);
  let overlap = 0;
  let sizeA = 0;
  for (const v of ba.values()) sizeA += v;
  let sizeB = 0;
  for (const v of bb.values()) sizeB += v;
  for (const [bg, count] of ba) {
    const other = bb.get(bg);
    if (other) overlap += Math.min(count, other);
  }
  return sizeA + sizeB === 0 ? 0 : (2 * overlap) / (sizeA + sizeB);
}

function bestMatch<T>(
  target: string,
  candidates: T[],
  keyOf: (c: T) => string,
  cutoff: number,
): T | null {
  const nt = normalize(target);
  let best: T | null = null;
  let bestScore = cutoff;
  for (const c of candidates) {
    const score = dice(nt, normalize(keyOf(c)));
    if (score >= bestScore) {
      bestScore = score;
      best = c;
    }
  }
  return best;
}

const MASS_RE = /(\d+[.,]?\d*)\s*[xX]\s*(\d+[.,]?\d*)/;

function massAusText(text: string | undefined | null): string {
  if (!text) return "";
  const m = MASS_RE.exec(text);
  return m ? `${m[1]} x ${m[2]}` : "";
}

// ---------------------------------------------------------------------------
// Seed: alle Werke aus den bestehenden Quellen zusammenführen
// ---------------------------------------------------------------------------

interface ArtworkLike {
  slug: string;
  name: string;
  price: number | null;
  formatted_price: string | null;
  categories: string[];
  in_stock: boolean;
  description?: string;
  media: { local_path?: string; display_url?: string }[];
}

interface EnrichedLike {
  slug: string;
  enrichment?: {
    description_text?: string;
    size_guess?: string;
    year_guess?: number | null;
    sold_hint?: boolean;
  };
}

interface WvLike {
  nr: string;
  titel: string;
  jahr: number | string;
  technik: string;
  masse: string;
  preis: number | string;
  status?: string;
}

interface SketchLike {
  title: string;
  src: string;
  thumb?: string;
}

const artworks = artworksData as unknown as ArtworkLike[];
const enriched = enrichedData as unknown as EnrichedLike[];
const sketchbook = sketchbookData as unknown as SketchLike[];
const werkverzeichnis = werkverzeichnisData as unknown as WvLike[];

const enrichedBySlug = new Map(enriched.map((e) => [e.slug, e]));

function preisString(a: ArtworkLike): string {
  if (a.formatted_price) return a.formatted_price.replace(/\s?€$/, "").trim();
  if (a.price != null) return String(a.price);
  return "";
}

export function seedRecords(): ErfassungRecord[] {
  const records: ErfassungRecord[] = [];
  const artworkTitles = artworks.map((a) => a.name);

  // 1) Kunstwerke
  for (const a of artworks) {
    const e = enrichedBySlug.get(a.slug);
    const wv = bestMatch<WvLike>(a.name, werkverzeichnis, (w) => w.titel, 0.78);

    const masse =
      (wv?.masse ? String(wv.masse).trim() : "") ||
      (e?.enrichment?.size_guess ?? "") ||
      massAusText(e?.enrichment?.description_text) ||
      massAusText(a.description);

    const jahr = wv?.jahr
      ? String(wv.jahr).trim()
      : e?.enrichment?.year_guess
        ? String(e.enrichment.year_guess)
        : "";

    let status = wv?.status ? String(wv.status).trim() : "";
    if (!status) {
      if (e?.enrichment?.sold_hint || a.in_stock === false) status = "verkauft";
      else status = "verfügbar";
    }

    records.push({
      id: a.slug,
      quelle: "artwork",
      bild: a.media?.[0]?.local_path || a.media?.[0]?.display_url || "",
      titel: a.name,
      jahr,
      technik: (a.categories ?? []).join(", "),
      masse,
      preis: preisString(a),
      status,
      notiz: e?.enrichment?.description_text?.replace(/\s+/g, " ").trim() ?? "",
    });
  }

  // 2) Sketchbook-Werke, die nicht schon als Kunstwerk vorhanden sind
  sketchbook.forEach((s, i) => {
    const dup = bestMatch(s.title, artworkTitles.map((t) => ({ t })), (c) => c.t, 0.72);
    if (dup) return;
    const wv = bestMatch<WvLike>(s.title, werkverzeichnis, (w) => w.titel, 0.78);
    records.push({
      id: `sketchbook-${i}`,
      quelle: "sketchbook",
      bild: s.src,
      titel: s.title,
      jahr: wv?.jahr ? String(wv.jahr).trim() : "",
      technik: wv?.technik ? String(wv.technik).trim() : "",
      masse: wv?.masse ? String(wv.masse).trim() : "",
      preis: wv?.preis ? String(wv.preis).trim() : "",
      status: wv?.status ? String(wv.status).trim() : "",
      notiz: "",
    });
  });

  return records;
}

// ---------------------------------------------------------------------------
// Vollständigkeit & Nummerierung
// ---------------------------------------------------------------------------

export function fehlendeFelder(r: ErfassungRecord): ErfassungFeld[] {
  return PFLICHTFELDER.filter((f) => !String(r[f] ?? "").trim());
}

export function istVollstaendig(r: ErfassungRecord): boolean {
  return fehlendeFelder(r).length === 0;
}

export interface NummeriertesWerk {
  record: ErfassungRecord;
  nummer: string | null; // "001" … für vollständige, null für unvollständige
  position: number; // laufende Position über alle (1-basiert)
  vollstaendig: boolean;
  fehlt: ErfassungFeld[];
}

// Vollständige Werke zuerst (stabil nach Technik, dann Titel), durchnummeriert 001…;
// danach die unvollständigen (ohne Nummer), ebenfalls stabil sortiert.
export function computeOrder(records: ErfassungRecord[]): NummeriertesWerk[] {
  const sortKey = (r: ErfassungRecord) =>
    `${(r.technik || "zzz").toLowerCase()}|${r.titel.toLowerCase()}`;

  const enriched = records.map((record) => ({
    record,
    vollstaendig: istVollstaendig(record),
    fehlt: fehlendeFelder(record),
  }));

  const voll = enriched
    .filter((x) => x.vollstaendig)
    .sort((a, b) => sortKey(a.record).localeCompare(sortKey(b.record), "de"));
  const unvoll = enriched
    .filter((x) => !x.vollstaendig)
    .sort((a, b) => sortKey(a.record).localeCompare(sortKey(b.record), "de"));

  const result: NummeriertesWerk[] = [];
  let pos = 0;
  voll.forEach((x, i) => {
    result.push({
      ...x,
      nummer: String(i + 1).padStart(3, "0"),
      position: ++pos,
    });
  });
  unvoll.forEach((x) => {
    result.push({ ...x, nummer: null, position: ++pos });
  });
  return result;
}

// Gespeicherte Records über den Seed legen (per id); neue Seed-Werke bleiben erhalten.
export function mergeSaved(
  seed: ErfassungRecord[],
  saved: ErfassungRecord[] | null | undefined,
): ErfassungRecord[] {
  if (!saved || saved.length === 0) return seed;
  const savedById = new Map(saved.map((r) => [r.id, r]));
  const merged = seed.map((s) => {
    const ov = savedById.get(s.id);
    return ov ? { ...s, ...ov, id: s.id, quelle: s.quelle, bild: s.bild } : s;
  });
  // Records, die nur im gespeicherten Stand existieren (z.B. später manuell ergänzt)
  for (const r of saved) {
    if (!merged.some((m) => m.id === r.id)) merged.push(r);
  }
  return merged;
}
