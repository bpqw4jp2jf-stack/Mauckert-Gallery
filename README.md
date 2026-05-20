# Mauckert Gallery — Website

Static site for **www.mauckertgallery.com**, built with [Astro](https://astro.build/).

## Run locally

```bash
npm install         # only the first time
npm run dev         # http://localhost:4321
```

## Build

```bash
npm run build       # outputs to ./dist/
npm run preview     # serves the built site
```

## Project layout

```
data/                 JSON content (artworks, exhibitions, vita, featured, sketchbook)
public/images/        artworks, sketchbook, exhibition photos, logo
src/
  components/         Astro components (ArtworkCard, HeroMasterpieces, SketchbookSlideshow)
  layouts/            BaseLayout
  lib/                helpers
  pages/              one file per route
  styles/global.css   palette + all styles
scripts/              Python helpers (scraping, image resize, Excel export)
```

## Editing content

| What to change | Where |
|---|---|
| Home techniques copy / hero | `src/pages/index.astro` |
| Which 3 masterpieces show by default + the 3 sold | `data/featured.json` (first 3 are visible; rest unlock via "Mehr anzeigen") |
| Exhibitions list, descriptions, images | `data/exhibitions.json` + `public/images/ausstellungen/` |
| Vita timeline & "Über mich" intro | `data/vita.json` |
| Sketchbook slideshow images | re-run `python3 scripts/build-sketchbook.py` |
| Inventory Excel export | `python3 scripts/export-inventory.py` → writes `data/Mauckert_Gallery_Inventar.xlsx` |
| Brand colors | `src/styles/global.css` `:root` block |
| Inquiry email address | global search-replace `s.mauckert@web.de` |

## Deploying

See [`DEPLOY.md`](./DEPLOY.md).
