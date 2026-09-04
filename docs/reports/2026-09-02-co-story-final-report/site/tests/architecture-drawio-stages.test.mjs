import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const diagrams = path.join(root, "public", "diagrams");

async function readDiagram(name) {
  return readFile(path.join(diagrams, name), "utf8");
}

function edges(xml) {
  return [...xml.matchAll(/<mxCell\b[^>]*\bedge="1"[^>]*>[\s\S]*?<\/mxCell>/g)].map(
    (match) => match[0],
  );
}

test("P6 人工核准置中且左右發布路徑等長", async () => {
  const xml = await readDiagram("production-architecture.drawio");

  assert.match(xml, /id="approval-icon"[\s\S]*?<mxGeometry x="655" y="648" width="52" height="52"/);
  assert.match(xml, /id="approval-label"[\s\S]*?<mxGeometry x="714" y="646" width="141" height="58"/);
  assert.match(xml, /id="approval-service-group"[\s\S]*?<mxGeometry x="655" y="646" width="200" height="58"/);
  assert.match(xml, /id="delivery-source-group"[\s\S]*?<mxGeometry x="220" y="637" width="330"/);
  assert.match(xml, /id="ssm-service-group"[\s\S]*?<mxGeometry x="960" y="646" width="260"/);
});

test("P4 起始架構使用 P6 邊界與正交路徑規則", async () => {
  const xml = await readDiagram("classic-architecture.drawio");
  const svg = await readDiagram("classic-architecture.svg");
  const routes = edges(xml);

  assert.equal(routes.length, 4);
  for (const layer of ["Base · classic services", "Ingress · HTTPS 443", "Data · RDS", "Inference · Bedrock"]) {
    assert.match(xml, new RegExp(`value="${layer.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"[^>]*visible="1"`));
  }
  for (const required of [
    "玩家瀏覽器",
    "Internet Gateway",
    "Amazon VPC",
    "public app subnet",
    "private data subnets",
    "Web Security Group",
    "DB Security Group",
    "Nginx · Web · API",
    "RDS for PostgreSQL",
    "Amazon Bedrock",
  ]) {
    assert.match(xml, new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  for (const forbidden of ["Amazon SQS", "Story Worker", "CloudWatch", "Systems Manager", "DynamoDB", "ALB", "ECS", "EKS"]) {
    assert.doesNotMatch(xml, new RegExp(forbidden, "i"));
  }
  for (const [id, source, target] of [
    ["classic-browser-igw", "classic-browser-icon", "classic-igw-icon"],
    ["classic-igw-web", "classic-igw-icon", "classic-web-group"],
    ["classic-web-rds", "classic-web-group", "classic-rds-group"],
    ["classic-web-bedrock", "classic-web-group", "classic-bedrock-group"],
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*source="${source}"[^>]*target="${target}"`));
  }
  assert.match(xml, /id="classic-browser-igw"[^>]*exitX=1;exitY=0.5[^>]*entryX=0;entryY=0.5/);
  assert.match(xml, /id="classic-browser-icon"[\s\S]*?<mxGeometry x="38" y="316" width="64" height="64"/);
  assert.match(xml, /id="classic-browser-label"[\s\S]*?<mxGeometry x="0" y="390" width="140" height="58"/);
  assert.match(xml, /id="classic-igw-label"[\s\S]*?<mxGeometry x="155" y="390" width="150" height="58"/);
  assert.match(xml, /id="classic-managed-title" value="AWS MANAGED&lt;br&gt;SERVICE · VPC 外"/);
  assert.match(xml, /id="classic-managed-title"[\s\S]*?<mxGeometry x="1305" y="108" width="275" height="58"/);
  assert.match(xml, /id="classic-igw-web"[^>]*exitX=1;exitY=0.5[^>]*entryX=0;entryY=0.5/);
  assert.match(xml, /id="classic-web-rds"[^>]*strokeColor=#47C9B8[^>]*exitX=1;exitY=0.5[^>]*entryX=0;entryY=0.5/);
  assert.match(xml, /id="classic-web-bedrock"[\s\S]*?<mxPoint x="510" y="560"\/>[\s\S]*?<mxPoint x="1430" y="560"\/>/);
  assert.match(svg, /viewBox="0 0 1600 760"/);
  assert.doesNotMatch(svg, /(?:href|src)="https?:\/\//i);
});

test("P5 同步與非同步圖面採分層的水平服務鏈", async () => {
  const xml = await readDiagram("architecture-evolution.drawio");
  const svg = await readDiagram("architecture-evolution.svg");
  const routes = edges(xml);

  assert.equal(routes.length, 9);
  for (const layer of [
    "Base · comparison",
    "Before · ingress",
    "Before · data",
    "Before · inference",
    "After · ingress",
    "After · work",
    "After · data",
    "After · inference",
  ]) {
    assert.match(xml, new RegExp(`value="${layer.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"[^>]*visible="1"`));
  }
  for (const required of [
    "改造前",
    "同步處理",
    "等待故事完成後回應",
    "改造後",
    "非同步處理",
    "202 先回應 · 背景完成",
    "Amazon SQS",
    "Story Worker",
    "Private RDS",
    "Amazon Bedrock",
  ]) {
    assert.match(xml, new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  for (const [id, color] of [
    ["before-browser-web", "#69B9F2"],
    ["before-web-sync", "#69B9F2"],
    ["before-sync-rds", "#47C9B8"],
    ["before-sync-bedrock", "#F2BD57"],
    ["after-browser-web", "#69B9F2"],
    ["after-web-sqs", "#D47ADE"],
    ["after-sqs-worker", "#D47ADE"],
    ["after-worker-rds", "#47C9B8"],
    ["after-worker-bedrock", "#F2BD57"],
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*strokeColor=${color}`));
  }
  for (const id of [
    "before-browser-web",
    "before-web-sync",
    "before-sync-rds",
    "after-browser-web",
    "after-web-sqs",
    "after-sqs-worker",
    "after-worker-rds",
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*exitX=1;exitY=0.5[^>]*entryX=0;entryY=0.5`));
  }
  assert.match(xml, /id="before-sync-bedrock"[\s\S]*?<mxPoint x="760" y="330"\/>[\s\S]*?<mxPoint x="1340" y="330"\/>/);
  assert.match(xml, /id="after-worker-bedrock"[\s\S]*?<mxPoint x="870" y="710"\/>[\s\S]*?<mxPoint x="1350" y="710"\/>/);
  assert.match(svg, /viewBox="0 0 1600 760"/);
  assert.doesNotMatch(svg, /(?:href|src)="https?:\/\//i);
});
