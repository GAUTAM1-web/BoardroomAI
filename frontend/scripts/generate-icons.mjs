import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const root = process.cwd();
const source = path.join(root, "public", "boardroom-mark.svg");
const outputDir = path.join(root, "electron", "build");
const sizes = [16, 24, 32, 48, 64, 128, 256];

await mkdir(outputDir, { recursive: true });

const svg = await readFile(source);
const pngImages = await Promise.all(
  sizes.map((size) =>
    sharp(svg)
      .resize(size, size)
      .png()
      .toBuffer()
      .then((buffer) => ({ size, buffer }))
  )
);

await writeFile(path.join(outputDir, "icon.png"), pngImages.at(-1).buffer);
await writeFile(path.join(outputDir, "icon.ico"), createIco(pngImages));

function createIco(images) {
  const headerSize = 6;
  const directorySize = images.length * 16;
  let imageOffset = headerSize + directorySize;

  const header = Buffer.alloc(headerSize);
  header.writeUInt16LE(0, 0);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(images.length, 4);

  const entries = images.map(({ size, buffer }) => {
    const entry = Buffer.alloc(16);
    entry.writeUInt8(size >= 256 ? 0 : size, 0);
    entry.writeUInt8(size >= 256 ? 0 : size, 1);
    entry.writeUInt8(0, 2);
    entry.writeUInt8(0, 3);
    entry.writeUInt16LE(1, 4);
    entry.writeUInt16LE(32, 6);
    entry.writeUInt32LE(buffer.length, 8);
    entry.writeUInt32LE(imageOffset, 12);
    imageOffset += buffer.length;
    return entry;
  });

  return Buffer.concat([header, ...entries, ...images.map(({ buffer }) => buffer)]);
}
