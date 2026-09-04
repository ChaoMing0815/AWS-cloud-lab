import { cp, mkdir, readFile, rm, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
const assets = ["index.html", "src", "public", "capture-manifest.json"];

await rm(dist, { force: true, recursive: true });
await mkdir(dist, { recursive: true });
for (const asset of assets) await cp(path.join(root, asset), path.join(dist, asset), { recursive: true });

const html = await readFile(path.join(dist, "index.html"), "utf8");
if (/\b(?:src|href)="https?:\/\//i.test(html)) throw new Error("Build contains a runtime network asset");
for (const asset of assets) await stat(path.join(dist, asset));
console.log("build=passed assets=4 runtime_network_assets=0");
