// Central place for the inquiry email address and the prefilled mailto templates,
// so the wording stays consistent across the homepage, the contact page and
// anywhere else we link an inquiry. Edit the plain strings here — they get
// URL-encoded automatically.

export const INQUIRY_EMAIL = "s.mauckert@web.de";

function mailto(subject: string, body: string): string {
  return `mailto:${INQUIRY_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

/** "Für Unternehmen anfragen" — business / hospitality (B2B) inquiry. */
export const businessInquiryMailto = mailto(
  "Anfrage: Kunst für unsere Räume",
  `Guten Tag Frau Mauckert,

wir interessieren uns für Originale von Ihnen für unsere Räume.

Damit Sie uns gut beraten können, ein paar Eckdaten (gern ergänzen oder weglassen):

· Unternehmen / Haus:
· Art der Räume (z. B. Büro, Empfang, Hotel, Restaurant, Weingut):
· Etwa wie viele Werke / welche Wandflächen:
· Stil oder Motive, die zu uns passen:
· Zeitlicher Rahmen:

Über ein persönliches Gespräch freuen wir uns.

Mit freundlichen Grüßen
`,
);

/** "Werk anfragen" — general inquiry about an artwork (not a specific one). */
export const workInquiryMailto = mailto(
  "Anfrage zu einem Werk",
  `Guten Tag Frau Mauckert,

ich interessiere mich für ein Werk aus Ihrer Galerie und habe folgende Frage:


Mit freundlichen Grüßen
`,
);

/** "Anfragen" on a specific, available artwork detail page. */
export function artworkInquiryMailto(opts: { name: string; price: string; url: string }): string {
  return mailto(
    `Anfrage: ${opts.name}`,
    `Guten Tag Frau Mauckert,

ich interessiere mich für das Werk „${opts.name}" (${opts.price}) und würde es gern erwerben oder reservieren.

Könnten Sie mir die nächsten Schritte nennen (Reservierung, Besichtigung, Versand oder Abholung)?

Werk: ${opts.url}

Mit freundlichen Grüßen
`,
  );
}

/** "Ähnliches Werk anfragen" on a sold artwork detail page. */
export function similarWorkMailto(opts: { name: string; url: string }): string {
  return mailto(
    `Ähnliches Werk gesucht: ${opts.name}`,
    `Guten Tag Frau Mauckert,

das Werk „${opts.name}" ist bereits verkauft. Gibt es ein ähnliches verfügbares Werk – oder die Möglichkeit einer Arbeit auf Anfrage?

Werk: ${opts.url}

Mit freundlichen Grüßen
`,
  );
}
