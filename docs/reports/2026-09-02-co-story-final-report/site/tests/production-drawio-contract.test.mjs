import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const diagramPath = path.join(root, "public", "diagrams", "production-architecture.drawio");
const previewPath = path.join(root, "public", "diagrams", "production-architecture.svg");

test("P6 Draw.io 原稿保留可逐色檢查的圖層", async () => {
  const xml = await readFile(diagramPath, "utf8");

  assert.match(xml, /^<mxfile\b/);
  for (const layer of [
    "Base · zones and services",
    "Ingress · HTTPS 443",
    "Work · SQS and DLQ",
    "Data · TLS 5432",
    "Inference · NAT to Bedrock",
    "Delivery · approval and SSM",
    "Observability · CloudWatch",
  ]) {
    assert.match(xml, new RegExp(`value="${layer.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"`), layer);
  }

  assert.match(xml, /value="Ingress · HTTPS 443"[^>]*visible="1"/);
  assert.match(xml, /value="Work · SQS and DLQ"[^>]*visible="1"/);
  assert.match(xml, /value="Data · TLS 5432"[^>]*visible="1"/);
  assert.match(xml, /value="Inference · NAT to Bedrock"[^>]*visible="1"/);
  for (const visibleLayer of [
    "Delivery · approval and SSM",
    "Observability · CloudWatch",
  ]) {
    assert.match(xml, new RegExp(`value="${visibleLayer.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"[^>]*visible="1"`));
  }
});

test("P6 圖稿只呈現有證據的正式環境元件", async () => {
  const xml = await readFile(diagramPath, "utf8");

  for (const required of [
    "玩家瀏覽器",
    "Internet Gateway",
    "NAT Gateway",
    "Nginx · Web · API",
    "Publisher",
    "Story Worker A",
    "Story Worker B",
    "RDS for PostgreSQL",
    "Amazon SQS",
    "DLQ",
    "Amazon Bedrock",
    "Amazon ECR",
    "GitHub Actions OIDC",
    "人工核准",
    "Systems Manager",
    "CloudWatch",
    "public app subnet",
    "private compute subnet · same AZ",
    "private data subnets · DB subnet group",
  ]) {
    assert.match(xml, new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), required);
  }

  for (const forbidden of ["DynamoDB", "ALB", "ECS", "EKS", "CloudFront", "Route 53", "Lambda"]) {
    assert.doesNotMatch(xml, new RegExp(forbidden, "i"), forbidden);
  }
  assert.doesNotMatch(xml, /stateful virtual firewall/i);
});

test("P6 入站、工作、資料與推論路徑分層且箭頭結構有效", async () => {
  const xml = await readFile(diagramPath, "utf8");
  const edges = [...xml.matchAll(/<mxCell\b[^>]*\bedge="1"[^>]*>[\s\S]*?<\/mxCell>/g)].map(
    (match) => match[0],
  );
  const cellIds = [...xml.matchAll(/<mxCell\b[^>]*\bid="([^"]+)"/g)].map((match) => match[1]);

  assert.equal(new Set(cellIds).size, cellIds.length, "每個 Draw.io cell id 必須唯一");
  assert.equal(edges.length, 24);
  for (const edge of edges) {
    assert.match(edge, /strokeColor=#(?:69B9F2|D47ADE|47C9B8|F2BD57|FF7B72|AEB8B4)/);
    assert.match(edge, /<mxGeometry\b[^>]*relative="1"[^>]*as="geometry"/);
  }
  assert.equal(edges.filter((edge) => edge.includes("strokeColor=#69B9F2")).length, 2);
  assert.equal(edges.filter((edge) => edge.includes("strokeColor=#D47ADE")).length, 5);
  assert.equal(edges.filter((edge) => edge.includes("strokeColor=#47C9B8")).length, 4);
  assert.equal(edges.filter((edge) => edge.includes("strokeColor=#F2BD57")).length, 4);
  assert.equal(edges.filter((edge) => edge.includes("strokeColor=#FF7B72")).length, 5);
  assert.equal(edges.filter((edge) => edge.includes("strokeColor=#AEB8B4")).length, 4);
  for (const edge of edges.filter(
    (edge) =>
      !edge.includes('id="work-sqs-worker-trunk"') &&
      !edge.includes('id="inference-worker-a-merge"') &&
      !edge.includes('id="inference-worker-b-merge"') &&
      !edge.includes('id="data-web-merge"') &&
      !edge.includes('id="data-worker-a-merge"') &&
      !edge.includes('id="data-worker-b-merge"') &&
      !edge.includes('id="delivery-ssm-junction"') &&
      !edge.includes('id="observability-web-merge"') &&
      !edge.includes('id="observability-workers-merge"') &&
      !edge.includes('id="observability-data-merge"'),
  )) {
    assert.match(edge, /endArrow=blockThin/);
    assert.match(edge, /endFill=1/);
    assert.match(edge, /endSize=10/);
  }
  assert.match(xml, /id="work-sqs-worker-trunk"[^>]*endArrow=none/);
  assert.match(xml, /id="inference-worker-a-merge"[^>]*endArrow=none/);
  assert.match(xml, /id="inference-worker-b-merge"[^>]*endArrow=none/);
  for (const [id, source, target] of [
    ["work-publisher-sqs", "web-service-group", "sqs-service-group"],
    ["work-sqs-worker-trunk", "sqs-service-group", "worker-branch-junction"],
    ["work-sqs-worker-a", "worker-branch-junction", "worker-a-icon"],
    ["work-sqs-worker-b", "worker-branch-junction", "worker-b-icon"],
    ["work-sqs-dlq", "sqs-service-group", "dlq-icon"],
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*source="${source}"[^>]*target="${target}"`));
  }
  for (const [id, source, target] of [
    ["data-web-merge", "web-ec2-label", "data-rds-junction"],
    ["data-worker-a-merge", "worker-a-label", "data-rds-junction"],
    ["data-worker-b-merge", "worker-b-label", "data-rds-junction"],
    ["data-rds-trunk", "data-rds-junction", "rds-icon"],
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*source="${source}"[^>]*target="${target}"`));
  }
  assert.match(xml, /id="data-rds-junction"[\s\S]*?<mxGeometry x="1103" y="385" width="4" height="4"/);
  assert.match(xml, /id="data-web-merge"[^>]*endArrow=none[^>]*exitX=0.5;exitY=1/);
  assert.match(xml, /id="data-web-merge"[\s\S]*?<mxPoint x="441" y="480"\/>[\s\S]*?<mxPoint x="1105" y="480"\/>/);
  assert.match(xml, /id="data-worker-a-merge"[\s\S]*?<mxPoint x="1105" y="338"\/>/);
  assert.match(xml, /id="data-worker-b-merge"[\s\S]*?<mxPoint x="1105" y="402"\/>/);
  assert.match(xml, /id="worker-a-label"[\s\S]*?<mxGeometry x="88" y="45" width="270"/);
  assert.match(xml, /id="nat-label"[\s\S]*?<mxGeometry x="88" y="51" width="205"/);
  assert.match(xml, /id="work-sqs-dlq"[^>]*dashed=1;dashPattern=4 3/);
  for (const [id, source, target] of [
    ["inference-worker-a-merge", "worker-a-icon", "inference-worker-junction"],
    ["inference-worker-b-merge", "worker-b-icon", "inference-worker-junction"],
    ["inference-workers-nat", "inference-worker-junction", "nat-label"],
    ["inference-nat-bedrock", "nat-label", "bedrock-icon"],
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*source="${source}"[^>]*target="${target}"`));
  }
  assert.match(xml, /id="inference-worker-junction"[\s\S]*?<mxGeometry x="613" y="283" width="4" height="4"/);
  assert.match(xml, /id="inference-worker-a-merge"[\s\S]*?<mxPoint x="615" y="325"/);
  assert.match(xml, /id="inference-workers-nat"[^>]*jumpStyle=gap;jumpSize=8[^>]*entryX=1;entryY=0.5/);
  assert.match(xml, /id="inference-nat-bedrock"[^>]*jumpStyle=gap;jumpSize=8[^>]*exitX=0.57;exitY=0[^>]*entryX=0.5;entryY=1/);
  assert.match(xml, /id="inference-nat-bedrock"[\s\S]*?<mxPoint x="445" y="175"\/>[\s\S]*?<mxPoint x="1274" y="175"\/>/);
  assert.match(xml, /id="worker-b-icon"[\s\S]*?<mxGeometry x="24" y="112" width="54" height="54"/);
  assert.match(xml, /id="worker-b-label"[\s\S]*?<mxGeometry x="88" y="109" width="270" height="60"/);
  assert.match(xml, /id="rds-icon"[\s\S]*?<mxGeometry x="18" y="66" width="50" height="50"/);
  assert.match(xml, /id="rds-label"[\s\S]*?<mxGeometry x="75" y="62" width="264" height="58"/);
  assert.match(xml, /id="work-sqs-worker-b"[\s\S]*?<mxPoint x="590" y="402"\/>/);
  assert.match(xml, /id="inference-worker-b-merge"[\s\S]*?<mxPoint x="615" y="389"\/>/);
  assert.match(xml, /id="workers-service-group"[\s\S]*?<mxGeometry x="24" y="45" width="334" height="128"/);

  for (const [id, source, target] of [
    ["delivery-ecr-approval", "delivery-source-group", "approval-service-group"],
    ["delivery-approval-ssm", "approval-service-group", "ssm-service-group"],
    ["delivery-ssm-junction", "ssm-service-group", "delivery-compute-junction"],
    ["delivery-junction-web", "delivery-compute-junction", "web-service-group"],
    ["delivery-junction-workers", "delivery-compute-junction", "workers-service-group"],
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*source="${source}"[^>]*target="${target}"`));
  }
  assert.match(xml, /id="delivery-source-group"[\s\S]*?<mxGeometry x="220" y="637" width="330" height="76"/);
  assert.match(xml, /id="approval-service-group"[\s\S]*?<mxGeometry x="655" y="646" width="200" height="58"/);
  assert.match(xml, /id="ssm-icon"[\s\S]*?<mxGeometry x="960" y="648" width="52" height="52"/);
  assert.match(xml, /id="ssm-label"[\s\S]*?<mxGeometry x="1019" y="646" width="201" height="58"/);
  assert.match(xml, /id="ssm-service-group"[\s\S]*?<mxGeometry x="960" y="646" width="260" height="58"/);
  assert.match(xml, /id="delivery-compute-junction"[\s\S]*?<mxGeometry x="1015" y="583" width="4" height="4"/);
  assert.match(xml, /id="delivery-ecr-approval"[^>]*exitX=1;exitY=0.5[^>]*entryX=0;entryY=0.5[\s\S]*?<mxGeometry relative="1" as="geometry"\/>/);
  assert.match(xml, /id="delivery-approval-ssm"[^>]*exitX=1;exitY=0.5[^>]*entryX=0;entryY=0.5[\s\S]*?<mxGeometry relative="1" as="geometry"\/>/);
  assert.match(xml, /id="delivery-ssm-junction"[^>]*exitX=0.22;exitY=0/);
  assert.match(xml, /id="delivery-junction-web"[\s\S]*?<mxPoint x="346" y="585"\/>/);
  assert.match(xml, /id="delivery-junction-workers"[^>]*jumpStyle=gap;jumpSize=8[\s\S]*?<mxPoint x="734" y="585"\/>/);

  for (const [id, source, target] of [
    ["observability-web-merge", "web-service-group", "observability-junction"],
    ["observability-workers-merge", "workers-service-group", "observability-junction"],
    ["observability-data-merge", "data-subnets", "observability-junction"],
    ["observability-cloudwatch-trunk", "observability-junction", "cloudwatch-service-group"],
  ]) {
    assert.match(xml, new RegExp(`id="${id}"[^>]*source="${source}"[^>]*target="${target}"`));
  }
  assert.match(xml, /id="observability-junction"[\s\S]*?<mxGeometry x="1284" y="558" width="4" height="4"/);
  assert.match(xml, /id="observability-web-merge"[^>]*dashed=1;dashPattern=4 3[^>]*jumpStyle=gap;jumpSize=8[\s\S]*?<mxPoint x="473" y="560"\/>/);
  assert.match(xml, /id="observability-workers-merge"[^>]*dashed=1;dashPattern=4 3[^>]*jumpStyle=gap;jumpSize=8[\s\S]*?<mxPoint x="901" y="560"\/>/);
  assert.match(xml, /id="observability-data-merge"[\s\S]*?<mxPoint x="1320" y="560"\/>/);
  assert.match(xml, /id="cloudwatch-service-group"[\s\S]*?<mxGeometry x="1260" y="646" width="284" height="58"/);
  assert.match(xml, /id="observability-cloudwatch-trunk"[^>]*entryX=0.2;entryY=0/);
  assert.match(xml, /HTTPS 443/);
  assert.match(xml, /id="browser-icon"[\s\S]*?<mxGeometry x="38" y="372" width="64" height="64"/);
  assert.match(xml, /id="browser-label"[\s\S]*?<mxGeometry x="0" y="445" width="140" height="58"/);
  assert.match(xml, /id="igw-icon"[\s\S]*?<mxGeometry x="153" y="372"/);
  assert.match(xml, /id="sqs-service-group"[\s\S]*?<mxGeometry x="555" y="54" width="213" height="58"/);
  assert.match(xml, /id="sqs-label"[\s\S]*?<mxGeometry x="63" y="1" width="150"/);
  assert.match(xml, /id="dlq-icon"[\s\S]*?<mxGeometry x="850" y="54"/);
  assert.match(xml, /id="web-service-group"[\s\S]*?<mxGeometry x="22" y="46" width="254" height="66"/);
  assert.match(xml, /id="work-publisher-sqs"[\s\S]*?<mxPoint x="580" y="404"/);
  assert.match(xml, /id="worker-branch-junction"[\s\S]*?<mxGeometry x="588" y="336" width="4" height="4"/);
  assert.match(xml, /id="rds-label"[^>]*fillColor=none/);
  assert.match(xml, /id="delivery-label" value="GitHub Actions OIDC&lt;br&gt;→ Amazon ECR&lt;br&gt;/);
  assert.match(xml, /id="delivery-label"[\s\S]*?<mxGeometry x="340" y="637" width="210" height="76"/);
  assert.match(xml, /id="approval-label"[\s\S]*?<mxGeometry x="714" y="646" width="141" height="58"/);
  assert.match(xml, /pageHeight="760"/);
  assert.doesNotMatch(xml, /Public EC2 · Publisher|Amazon&lt;br[^>]*&gt;ECR/);
  assert.doesNotMatch(xml, /<!--/);
  assert.doesNotMatch(xml, /fontSize=(?:[1-9]|1[0-7])(?:;|&quot;)/);
});

test("P6 SVG 預覽固定尺寸且不依賴執行時網路", async () => {
  const svg = await readFile(previewPath, "utf8");

  assert.match(svg, /^<svg\b/);
  assert.match(svg, /viewBox="0 0 1600 760"/);
  assert.match(svg, /<title[^>]*>P6 正式環境當前架構<\/title>/);
  assert.doesNotMatch(svg, /(?:href|src)="https?:\/\//i);
  assert.doesNotMatch(svg, /<script\b/i);
});
