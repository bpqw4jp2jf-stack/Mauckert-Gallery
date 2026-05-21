import sharp from 'sharp';
import { readdir, stat, rename, unlink } from 'node:fs/promises';
import { join, extname } from 'node:path';

const ROOT = 'public/images';
const MAX_WIDTH = 1600;
const JPEG_QUALITY = 82;
const SKIP_SMALL_BYTES = 200 * 1024;

async function* walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(path);
    else yield path;
  }
}

function isImage(p) {
  return ['.jpg', '.jpeg', '.png'].includes(extname(p).toLowerCase());
}

async function optimize(path) {
  const stats = await stat(path);
  const meta = await sharp(path).metadata();

  if (stats.size <= SKIP_SMALL_BYTES && meta.width <= MAX_WIDTH) {
    return { before: stats.size, after: stats.size, skipped: 'already-small' };
  }

  const ext = extname(path).toLowerCase();
  const tmpPath = path + '.tmp';

  let pipeline = sharp(path).rotate();

  if (meta.width > MAX_WIDTH) {
    pipeline = pipeline.resize({ width: MAX_WIDTH, withoutEnlargement: true });
  }

  if (ext === '.png') {
    pipeline = pipeline.flatten({ background: '#ffffff' }).png({ compressionLevel: 9, palette: false });
  } else {
    pipeline = pipeline.jpeg({ quality: JPEG_QUALITY, mozjpeg: true });
  }

  await pipeline.toFile(tmpPath);
  const newStats = await stat(tmpPath);

  if (newStats.size < stats.size) {
    await rename(tmpPath, path);
    return { before: stats.size, after: newStats.size, skipped: false };
  } else {
    await unlink(tmpPath);
    return { before: stats.size, after: stats.size, skipped: 'no-improvement' };
  }
}

const fmt = (b) => (b / 1024).toFixed(0).padStart(6) + ' KB';

let totalBefore = 0, totalAfter = 0, processed = 0, skipped = 0;
for await (const path of walk(ROOT)) {
  if (!isImage(path)) continue;
  try {
    const r = await optimize(path);
    totalBefore += r.before;
    totalAfter += r.after;
    if (r.skipped) {
      skipped++;
    } else {
      processed++;
      console.log(`${fmt(r.before)} → ${fmt(r.after)}   ${path}`);
    }
  } catch (e) {
    console.error(`ERROR  ${path}: ${e.message}`);
  }
}

console.log('---');
console.log(`Processed: ${processed}, skipped: ${skipped}`);
console.log(`Total: ${fmt(totalBefore)} → ${fmt(totalAfter)}  (${((1 - totalAfter / totalBefore) * 100).toFixed(1)}% reduction)`);
