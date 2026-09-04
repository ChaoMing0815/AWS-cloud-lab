import { open, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.resolve(root, "..", "captures");
const manifest = JSON.parse(await readFile(path.join(root, "capture-manifest.json"), "utf8"));

for (const section of manifest.sections) {
  const handle = await open(path.join(output, section.file), "r");
  const header = Buffer.alloc(24);
  await handle.read(header, 0, 24, 0);
  await handle.close();
  const signature = header.subarray(0, 8).toString("hex");
  const width = header.readUInt32BE(16);
  const height = header.readUInt32BE(20);
  if (signature !== "89504e470d0a1a0a" || width !== manifest.viewport.width || height !== manifest.viewport.height) {
    throw new Error(`${section.file}: expected ${manifest.viewport.width}x${manifest.viewport.height} PNG`);
  }
}
console.log(`captures=passed count=${manifest.sections.length} viewport=1920x1080`);
