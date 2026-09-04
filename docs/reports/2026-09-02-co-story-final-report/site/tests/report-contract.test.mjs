import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => readFile(path.join(root, relativePath), "utf8");

const sectionIds = [
  "opening",
  "product",
  "scenarios",
  "classic",
  "evolution",
  "production",
  "async",
  "components",
  "delivery",
  "security",
  "operations",
  "stewardship",
  "ai",
  "demo",
];

const awsIcons = [
  "amazon-ec2.svg",
  "amazon-rds.svg",
  "amazon-sqs.svg",
  "amazon-bedrock.svg",
  "amazon-cloudwatch.svg",
  "aws-systems-manager.svg",
  "amazon-ecr.svg",
  "aws-iam.svg",
  "amazon-vpc.svg",
  "nat-gateway.svg",
  "internet-gateway.svg",
];

test("報告固定十四個可深連結的 16:9 簡報頁", async () => {
  const [html, css, script] = await Promise.all([read("index.html"), read("src/main.css"), read("src/app.js")]);
  const actual = [...html.matchAll(/<section\b[^>]*\bid="([^"]+)"[^>]*\bdata-capture\b/g)].map(
    (match) => match[1],
  );
  assert.deepEqual(actual, sectionIds);
  assert.match(html, /aria-label="章節導覽"/);
  assert.doesNotMatch(html, /class="topbar"|chapter-readout|chapter-number|chapter-name/);
  assert.doesNotMatch(css, /\.topbar|\.brand(?:\W)|\.chapter-readout|#chapter-number|\.chapter-rule/);
  assert.doesNotMatch(script, /chapterNumber|chapterName/);
});

test("十四章採用已確認的觀眾版文案", async () => {
  const html = await read("index.html");
  for (const accepted of [
    "共演計劃",
    "在雲端一起創作",
    "各自天馬行空",
    "AI 續寫故事",
    "一起迎向結局",
    "同一套協作核心",
    "延伸不同應用場景",
    "目前完成作品為多人文字 RPG，其餘為潛在應用構想。",
    "同步轉非同步",
    "快速接收行動",
    "背景完成故事",
    "即使重新提交需求，系統也只保留一次有效結果。",
    "組件化上雲",
    "增加架構彈性",
    "故障隔離",
    "可驗證、可回復",
    "核准後自動上線",
    "8 個發布環節",
    "1 次人工核准",
    "失敗自動回復",
    "看見訊號",
    "執行受控處置",
    "留下紀錄",
    "成本透明",
    "建立費用邊界",
    "持續運作",
    "規則先定",
    "責任可控",
    "故事主持人依規則續寫；規則助理回答玩法。",
    "共演計劃已完成 AWS 正式環境部署。",
    "成品展示",
    "現在，進入共演計劃。",
  ]) {
    assert.match(html, new RegExp(accepted.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), accepted);
  }

  for (const rejected of [
    "4 位玩家",
    "4 回合",
    "產品縮影",
    "快速接受",
    "可靠完成每次敘事",
    "一次提交",
    "ENGINEERING OUTCOME",
    "AWS PRODUCTION PROJECT",
  ]) {
    assert.doesNotMatch(html, new RegExp(rejected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), rejected);
  }
});

test("全站與指定頁面採用本輪投影排版規則", async () => {
  const [html, css] = await Promise.all([read("index.html"), read("src/main.css")]);
  const opening = html.match(/<section id="opening"[\s\S]*?<\/section>/)?.[0] ?? "";
  const product = html.match(/<section id="product"[\s\S]*?<\/section>/)?.[0] ?? "";
  const scenarios = html.match(/<section id="scenarios"[\s\S]*?<\/section>/)?.[0] ?? "";
  const evolution = html.match(/<section id="evolution"[\s\S]*?<\/section>/)?.[0] ?? "";
  const production = html.match(/<section id="production"[\s\S]*?<\/section>/)?.[0] ?? "";
  const asyncSection = html.match(/<section id="async"[\s\S]*?<\/section>/)?.[0] ?? "";
  const delivery = html.match(/<section id="delivery"[\s\S]*?<\/section>/)?.[0] ?? "";
  const ai = html.match(/<section id="ai"[\s\S]*?<\/section>/)?.[0] ?? "";

  assert.match(css, /--eyebrow-size:\s*15px/);
  assert.match(css, /\.chapter:not\(\.chapter-opening\)::before/);
  assert.match(css, /\.rail a\s*\{[^}]*width:\s*32px;[^}]*height:\s*32px;/s);

  assert.match(opening, /class="opening-concept reveal"/);
  assert.doesNotMatch(opening, /class="opening-stage"|class="hero-service"|aws-icons/);
  assert.match(product, /採取的行動。<br \/>系統依規則擲骰/);
  assert.match(scenarios, /設計，<br \/>也能延伸/);
  assert.equal((scenarios.match(/class="scenario-lines"/g) ?? []).length, 3);
  assert.match(evolution, /<h2 class="single-title">同步轉非同步<\/h2>/);
  assert.doesNotMatch(evolution, /<h2[^>]*>[\s\S]*分散伺服器壓力/);
  assert.match(production, /<span>依職責劃分網段<\/span><span>入口公開、運算資料私有<\/span>/);
  assert.match(production, /私有網段，<br \/>再透過指定路徑/);
  assert.match(asyncSection, /class="async-decoration"/);
  assert.match(delivery, /工程師逐項處理/);
  assert.match(delivery, /核准正式環境後，系統自動取得短期權限/);
  assert.equal((ai.match(/class="ai-role (?:story-host|rules-assistant)"/g) ?? []).length, 2);
  assert.match(ai, /故事主持人依規則續寫；規則助理回答玩法。/);
  assert.match(css, /\.chapter-delivery \.delivery-compare\s*\{[^}]*margin-top:\s*94px;/s);
  assert.match(css, /\.chapter-demo \.demo-flow\s*\{[^}]*margin-top:\s*104px;/s);
});

test("眉標採標題相對定位且重點頁面使用本機插圖與垂直置中節奏", async () => {
  const [html, css] = await Promise.all([read("index.html"), read("src/main.css")]);
  const opening = html.match(/<section id="opening"[\s\S]*?<\/section>/)?.[0] ?? "";
  const ai = html.match(/<section id="ai"[\s\S]*?<\/section>/)?.[0] ?? "";

  assert.match(css, /\.eyebrow\s*\{[^}]*position:\s*static;[^}]*color:\s*var\(--gold\);[^}]*font:\s*700 var\(--eyebrow-size\)/s);
  assert.match(css, /\.chapter \.eyebrow\s*\{[^}]*color:\s*var\(--gold\);[^}]*font:\s*700 var\(--eyebrow-size\)/s);
  assert.doesNotMatch(css, /--eyebrow-top:/);
  assert.match(css, /\.js-enhanced \.reveal:has\(> \.eyebrow\)/);
  assert.match(css, /\.wide-heading\s*\{[^}]*row-gap:\s*18px;/s);
  assert.match(css, /\.section-intro\s*\{[^}]*row-gap:\s*18px;/s);
  assert.match(css, /\.split-heading\s*\{[^}]*row-gap:\s*18px;/s);

  assert.match(opening, /<img[^>]+opening-hero-art[^>]+cloud-collaboration-hero\.png/);
  assert.match(css, /\.opening-hero-art\s*\{[^}]*mask-image:\s*radial-gradient/s);
  assert.match(ai, /<img[^>]+assistant-avatar[^>]+rules-assistant-slime\.png/);
  await access(path.join(root, "public", "visuals", "cloud-collaboration-hero.png"));
  await access(path.join(root, "public", "visuals", "rules-assistant-slime.png"));

  assert.match(css, /\.chapter-async\s*\{[^}]*padding-top:\s*150px;/s);
  assert.match(css, /\.chapter-delivery \.delivery-compare\s*\{[^}]*margin-top:\s*94px;/s);
  assert.match(css, /\.chapter-demo \.demo-flow\s*\{[^}]*margin-top:\s*104px;/s);
  assert.match(css, /\.chapter-demo \.demo-flow[^}]*min-height:\s*310px;/s);
});

test("P2 至 P14 共用左上往右下的柔和聚光燈背景", async () => {
  const css = await read("src/main.css");

  assert.match(css, /\.chapter:not\(\.chapter-opening\)::before\s*\{[^}]*opacity:\s*\.64;[^}]*linear-gradient\(132deg,[^}]*clip-path:\s*polygon\(0 0, 24% 0, 92% 100%, 56% 100%\);/s);
  assert.doesNotMatch(css, /\.chapter-opening:not/);
});

test("產品只占前段情境並直接使用本機證據截圖", async () => {
  const html = await read("index.html");
  assert.match(html, /id="product"[\s\S]*?<img[^>]+gameplay-evidence\.png/);
  assert.match(html, /潛在應用場景/);
  assert.match(html, /多人文字 RPG/);
  assert.match(html, /AI 輔助會議/);
  assert.match(html, /培訓工作坊/);
  assert.doesNotMatch(html, /story-console|遊戲玩法流程示意/);
  await access(path.join(root, "public", "evidence", "gameplay-evidence.png"));
});

test("AWS 工程主線涵蓋服務選型、組件化、部署、安全、成本與 AI 邊界", async () => {
  const [html, classic, production] = await Promise.all([
    read("index.html"),
    read("public/diagrams/classic-architecture.drawio"),
    read("public/diagrams/production-architecture.drawio"),
  ]);
  const report = `${html}\n${classic}\n${production}`;
  for (const required of [
    "Internet Gateway",
    "public app subnet",
    "private compute subnet",
    "private data subnets",
    "Security Group",
    "Publisher",
    "SQS",
    "DLQ",
    "Worker A",
    "Worker B",
    "GitHub Actions OIDC",
    "ECR 保存",
    "digest 掃描",
    "Systems Manager",
    "CloudWatch",
    "人工核准",
    "Budget",
    "Nova Lite",
    "deterministic cited lookup",
  ]) {
    assert.match(report, new RegExp(required, "i"), required);
  }
});

test("投影標題具有受控斷行且不產生單字或孤立標點行", async () => {
  const [html, css] = await Promise.all([read("index.html"), read("src/main.css")]);
  const titles = [...html.matchAll(/<h[12][^>]*class="[^"]*rhythm-title[^"]*"[^>]*>([\s\S]*?)<\/h[12]>/g)];
  assert.ok(titles.length >= 8, "至少八個大型標題採受控斷行");
  for (const [, title] of titles) {
    const lines = [...title.matchAll(/<span[^>]*>([\s\S]*?)<\/span>/g)].map((match) =>
      match[1].replace(/<[^>]+>/g, "").replace(/\s/g, ""),
    );
    assert.ok(lines.length >= 2 && lines.length <= 3, title);
    for (const line of lines) {
      assert.ok([...line].length >= 2, `不可單字成行：${line}`);
      assert.doesNotMatch(line, /^[，。；：！？、（）「」『』]$/u);
    }
  }
  assert.match(css, /--font-note:\s*clamp\(20px,/);
  assert.match(css, /--font-title:\s*clamp\(60px,/);
});

test("網站只引用 repo-local 樣式、程式與官方 AWS 圖示", async () => {
  const html = await read("index.html");
  assert.doesNotMatch(html, /(?:src|href)="https?:\/\//i);
  assert.match(html, /href="\.\/src\/main\.css"/);
  assert.match(html, /src="\.\/src\/app\.js"/);
  await Promise.all(
    awsIcons.map((file) => access(path.join(root, "public", "aws-icons", file))),
  );
  assert.match(html, /單一 NAT Gateway/);
});

test("頁面不含越界服務、課程分級與交付自我提示", async () => {
  const html = await read("index.html");
  for (const forbidden of [
    "DynamoDB",
    "ALB",
    "ECS",
    "EKS",
    "CloudFront",
    "Route 53",
    "Lambda",
    "Tier 0",
    "Tier 1",
    "Tier 2",
    "Tier 3",
    "Tier 4",
    "Tier 5",
    "交付檢查",
    "請確認",
    "SG 無狀態",
  ]) {
    assert.doesNotMatch(html, new RegExp(forbidden, "i"), forbidden);
  }
});

test("鍵盤、scroll snap、reduced motion 與靜態比較契約完整", async () => {
  const [script, css, html] = await Promise.all([
    read("src/app.js"),
    read("src/main.css"),
    read("index.html"),
  ]);
  for (const key of ["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End"]) {
    assert.match(script, new RegExp(key));
  }
  assert.match(script, /if \(location\.hash \|\| captureMode\) requestAnimationFrame/);
  assert.match(css, /scroll-snap-type:\s*y mandatory/);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  assert.match(html, /src="\.\/public\/diagrams\/architecture-evolution\.svg"/);
  assert.doesNotMatch(html, /data-state-target|data-architecture-state/);
  assert.doesNotMatch(script, /architectureCopy|requestedArchitecture|data-state-target/);
});

test("P4、P5、P6 使用 repo-local Draw.io SVG，並保留可讀替代文字", async () => {
  const [html, css, script] = await Promise.all([
    read("index.html"),
    read("src/main.css"),
    read("src/app.js"),
  ]);
  const classic = html.match(/<section id="classic"[\s\S]*?<\/section>/)?.[0] ?? "";
  const evolution = html.match(/<section id="evolution"[\s\S]*?<\/section>/)?.[0] ?? "";
  const production = html.match(/<section id="production"[\s\S]*?<\/section>/)?.[0] ?? "";

  assert.match(classic, /class="drawio-architecture classic-board reveal"/);
  assert.match(classic, /src="\.\/public\/diagrams\/classic-architecture\.svg"/);
  assert.match(classic, /alt="[^"]*Internet Gateway[^"]*private RDS[^"]*Amazon Bedrock[^"]*"/);
  assert.match(evolution, /class="drawio-architecture evolution-stage reveal"/);
  assert.match(evolution, /src="\.\/public\/diagrams\/architecture-evolution\.svg"/);
  assert.match(evolution, /alt="[^"]*同步[^"]*非同步[^"]*SQS[^"]*Story Worker[^"]*"/);
  assert.match(production, /class="drawio-architecture topology-board reveal"/);
  assert.match(production, /src="\.\/public\/diagrams\/production-architecture\.svg"/);
  assert.match(production, /alt="[^"]*正式環境[^"]*SQS[^"]*RDS[^"]*CloudWatch[^"]*"/);
  assert.doesNotMatch(html, /class="architecture-lines"|class="comparison-lines|class="topology-lines/);
  assert.doesNotMatch(script, /topologyPaths|setAttribute\("d"/);
  assert.match(css, /\.drawio-architecture\s*\{[^}]*overflow:\s*hidden/s);
  assert.match(css, /\.drawio-architecture\s*>\s*img\s*\{[^}]*object-fit:\s*contain/s);
});

test("index.html 可由 Chrome 直接以 file URL 開啟", async () => {
  const [html, css, script] = await Promise.all([
    read("index.html"),
    read("src/main.css"),
    read("src/app.js"),
  ]);
  assert.match(html, /<script\s+defer\s+src="\.\/src\/app\.js"><\/script>/);
  assert.doesNotMatch(html, /<script[^>]+type="module"/);
  assert.match(css, /\.reveal\s*\{\s*opacity:\s*1;/);
  assert.match(css, /\.js-enhanced \.reveal/);
  assert.match(script, /documentElement\.classList\.add\("js-enhanced"\)/);
});

test("captures manifest 與章節順序一致且禁止 hosting 設定", async () => {
  const manifest = JSON.parse(await read("capture-manifest.json"));
  assert.deepEqual(
    manifest.sections.map((section) => section.id),
    sectionIds,
  );
  assert.equal(manifest.viewport.width, 1920);
  assert.equal(manifest.viewport.height, 1080);
  assert.ok(manifest.sections.every((section) => !("query" in section)));
  await assert.rejects(access(path.join(root, ".openai", "hosting.json")));
});
