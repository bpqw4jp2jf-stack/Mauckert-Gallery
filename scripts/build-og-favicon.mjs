// Builds the social share image (og-image.jpg) and PNG favicons from the brand
// logo + colors. Run: node scripts/build-og-favicon.mjs
import sharp from "sharp";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const pub = join(root, "public");

const navy = "#121920";
const cream = "#FCF9E4";
const clay = "#B98272";
const stone = "#C7BFA8";

// Cream-on-navy logo mark, reused in the OG card.
const logoPath = `<g transform="translate(0,212) scale(0.1,-0.1)" fill="${cream}" stroke="none"><path d="M2059 1966 c-2 -3 -441 -6 -974 -7 l-970 -2 2 -926 c2 -509 5 -925 8 -923 3 1 445 2 984 2 l978 0 2 483 1 482 -202 -3 c-157 -3 -203 0 -209 10 -5 7 -9 115 -9 241 0 125 -4 227 -8 227 -4 0 -30 -23 -57 -51 -28 -28 -106 -98 -175 -156 -69 -57 -169 -147 -222 -199 -53 -52 -100 -94 -105 -94 -5 0 -58 50 -118 111 -61 61 -159 153 -220 204 -60 51 -123 107 -140 125 -16 17 -41 40 -55 50 l-25 18 0 -127 c1 -69 2 -296 3 -503 l2 -377 105 -3 105 -3 0 283 c0 155 4 282 8 282 4 0 79 -70 167 -155 88 -85 167 -154 175 -155 9 0 24 16 35 36 22 40 85 108 160 171 102 86 150 123 156 123 15 0 21 -87 13 -189 -8 -104 -7 -342 2 -371 3 -11 23 -16 81 -18 43 -2 86 -5 96 -8 16 -5 17 7 17 160 l0 166 100 0 100 0 0 -270 0 -270 -770 0 -770 0 0 703 0 703 770 3 770 3 0 -251 0 -251 105 3 104 2 7 28 c3 15 4 178 2 362 -3 314 -6 353 -29 331z"/></g>`;

const og = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="${navy}"/>
  <rect x="32" y="32" width="1136" height="566" fill="none" stroke="${clay}" stroke-width="2" opacity="0.55"/>
  <svg x="500" y="150" width="200" height="195" viewBox="0 0 218 212">${logoPath}</svg>
  <text x="600" y="430" text-anchor="middle" font-family="Cormorant Garamond, Georgia, 'Times New Roman', serif" font-size="78" fill="${cream}" letter-spacing="2">Mauckert Gallery</text>
  <text x="600" y="485" text-anchor="middle" font-family="Inter, Helvetica, Arial, sans-serif" font-size="27" fill="${stone}" letter-spacing="3">UTE MAUCKERT &#183; MALEREI &amp; ZEICHNUNG</text>
  <text x="600" y="525" text-anchor="middle" font-family="Inter, Helvetica, Arial, sans-serif" font-size="22" fill="${clay}" letter-spacing="2">Klassisch geschult, vor Ort gemalt, aus dem Rheintal</text>
</svg>`;

await sharp(Buffer.from(og)).jpeg({ quality: 88 }).toFile(join(pub, "og-image.jpg"));
console.log("wrote og-image.jpg (1200x630)");

const favSvg = await sharp(join(pub, "favicon.svg"));
await favSvg.clone().resize(180, 180).png().toFile(join(pub, "apple-touch-icon.png"));
await sharp(join(pub, "favicon.svg")).resize(32, 32).png().toFile(join(pub, "favicon-32.png"));
console.log("wrote apple-touch-icon.png (180x180) + favicon-32.png");
