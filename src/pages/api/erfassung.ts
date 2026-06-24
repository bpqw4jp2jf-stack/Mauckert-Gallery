// Lokale API für das Werk-Erfassen-Tool. NUR im Dev-Modus aktiv (localhost) –
// in Produktion (Cloudflare) gibt es kein Dateisystem, daher 403.
//
// GET  -> aktueller Erfassungsstand (data/erfassung.json) über den Seed gelegt.
// POST -> { records } nach data/erfassung.json schreiben, neue Nummerierung zurück.

import type { APIRoute } from "astro";
import {
  seedRecords,
  mergeSaved,
  computeOrder,
  type ErfassungRecord,
} from "../../lib/erfassung";

export const prerender = false;

const FORBIDDEN = () =>
  new Response(
    JSON.stringify({ error: "Werk-Erfassen ist nur lokal (npm run dev) verfügbar." }),
    { status: 403, headers: { "Content-Type": "application/json" } },
  );

async function dataFile(): Promise<{ fs: typeof import("node:fs"); file: string }> {
  const fs = await import("node:fs");
  const path = await import("node:path");
  return { fs, file: path.join(process.cwd(), "data", "erfassung.json") };
}

async function readSaved(): Promise<ErfassungRecord[] | null> {
  const { fs, file } = await dataFile();
  if (!fs.existsSync(file)) return null;
  try {
    return JSON.parse(fs.readFileSync(file, "utf-8")) as ErfassungRecord[];
  } catch {
    return null;
  }
}

function payload(records: ErfassungRecord[]) {
  const order = computeOrder(records);
  return {
    records,
    order,
    vollstaendig: order.filter((o) => o.vollstaendig).length,
    gesamt: order.length,
  };
}

export const GET: APIRoute = async () => {
  if (!import.meta.env.DEV) return FORBIDDEN();
  const records = mergeSaved(seedRecords(), await readSaved());
  return new Response(JSON.stringify(payload(records)), {
    headers: { "Content-Type": "application/json" },
  });
};

export const POST: APIRoute = async ({ request }) => {
  if (!import.meta.env.DEV) return FORBIDDEN();
  let body: { records?: ErfassungRecord[] };
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "Ungültiges JSON" }), { status: 400 });
  }
  if (!Array.isArray(body.records)) {
    return new Response(JSON.stringify({ error: "records fehlt" }), { status: 400 });
  }
  // Sicheren, vollständigen Stand über den Seed legen und speichern.
  const records = mergeSaved(seedRecords(), body.records);
  const { fs, file } = await dataFile();
  fs.mkdirSync(file.replace(/[/\\][^/\\]+$/, ""), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(records, null, 2), "utf-8");
  return new Response(JSON.stringify(payload(records)), {
    headers: { "Content-Type": "application/json" },
  });
};
