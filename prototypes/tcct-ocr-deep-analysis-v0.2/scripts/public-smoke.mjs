import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { loadGsFiles } from '../tests/load-gs.mjs';
import {
  buildBlockedReport,
  buildBranchPrompt,
  buildBranchSchema,
  buildRuntimeErrorReport,
  evaluatePublicShippingCase,
  parseInteractionJson,
  reportToMarkdown,
  selectApiKey,
} from './public-smoke-lib.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const WORK = path.join(ROOT, 'smoke-work');
const OUTPUT = path.join(ROOT, 'smoke-output');
const PDF_PATH = path.join(WORK, 'public-tcct-shipping-choice-scanned.pdf');
const META_PATH = path.join(WORK, 'fixture-metadata.json');
const API_REVISION = '2026-05-20';
const MODEL = String(process.env.GEMINI_MODEL || '').trim() || 'gemini-3.8-flash';
const SOURCE_ID = 'D1:CASE1';

let liveCallCount = 0;
let currentSourceSha256 = null;

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function sanitizeError(error, apiKey = '') {
  let message = error instanceof Error ? error.message : String(error);
  if (apiKey) message = message.split(apiKey).join('[REDACTED_API_KEY]');
  message = message.replace(/[A-Za-z0-9+/=]{200,}/g, '[REDACTED_LONG_PAYLOAD]');
  return message.slice(0, 4000);
}

function writeReport(report) {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const markdown = reportToMarkdown(report);
  fs.writeFileSync(path.join(OUTPUT, 'smoke-report.json'), `${JSON.stringify(report, null, 2)}\n`);
  fs.writeFileSync(path.join(OUTPUT, 'smoke-report.md'), `${markdown}\n`);
  if (process.env.GITHUB_STEP_SUMMARY) {
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, `${markdown}\n`);
  }
  console.log(markdown);
  console.log(`SMOKE_STATUS=${report.status}`);
}

async function callInteraction(request, label, apiKey) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 300_000);
  liveCallCount += 1;
  try {
    const response = await fetch(request.url, {
      method: 'POST',
      headers: request.headers,
      body: JSON.stringify(request.body),
      signal: controller.signal,
    });
    const responseText = await response.text();
    if (!response.ok) {
      throw new Error(`${label} returned HTTP ${response.status}: ${responseText.slice(0, 2000)}`);
    }
    let payload;
    try {
      payload = JSON.parse(responseText);
    } catch (error) {
      throw new Error(`${label} returned non-JSON HTTP content: ${error.message}`);
    }
    return {
      output: parseInteractionJson(payload),
      receipt: {
        id: payload.id || null,
        status: payload.status || null,
        model: payload.model || null,
        usage: payload.usage || payload.usage_metadata || null,
      },
    };
  } catch (error) {
    throw new Error(sanitizeError(error, apiKey));
  } finally {
    clearTimeout(timeout);
  }
}

function createGsContext() {
  return loadGsFiles([
    '25_DecisionRouter.gs',
    '35_DecisionIntelligenceContract.gs',
    '45_OutputGuard.gs',
    '55_GeminiDocumentAdapter.gs',
  ]);
}

function finalSystemInstruction() {
  return [
    'You are producing a review-only TCCT decision-intelligence record from one attached public scanned PDF.',
    'The PDF is the only case-record source. Prior branch outputs are draft analyses, not independent evidence.',
    `Use ${SOURCE_ID} for record citations.`,
    'Do not use model memory or external research for academic or comparative claims; mark those NEEDS_RESEARCH.',
    'Do not state penalties, limitation periods, director exposure, HHI, market shares, or numeric proof thresholds unless supplied by a governed source. For this smoke, penaltyStatements must be an empty array.',
    'Return JSON only and comply exactly with the supplied schema.',
  ].join('\n');
}

async function main() {
  fs.rmSync(OUTPUT, { recursive: true, force: true });
  fs.mkdirSync(OUTPUT, { recursive: true });

  if (!fs.existsSync(PDF_PATH)) throw new Error(`Public smoke PDF is missing: ${PDF_PATH}`);
  const pdf = fs.readFileSync(PDF_PATH);
  if (!pdf.subarray(0, 5).equals(Buffer.from('%PDF-'))) throw new Error('Smoke fixture is not a PDF');
  const metadata = fs.existsSync(META_PATH) ? JSON.parse(fs.readFileSync(META_PATH, 'utf8')) : {};
  const sourceSha256 = sha256(pdf);
  currentSourceSha256 = sourceSha256;
  const apiKey = selectApiKey(process.env);

  if (!apiKey) {
    writeReport({
      ...buildBlockedReport({ model: MODEL, sourceSha256 }),
      apiRevision: API_REVISION,
      sourceBytes: pdf.length,
      fixture: metadata,
    });
    return;
  }

  const ctx = createGsContext();
  const routingText = 'คำวินิจฉัยสาธารณะตามมาตรา 50 และมาตรา 57 เกี่ยวกับแพลตฟอร์มอิเล็กทรอนิกส์และทางเลือกผู้ให้บริการขนส่ง';
  const classification = ctx.tcctV02ClassifyDecision(routingText);
  if (classification.primaryFamily !== 'UNFAIR_TRADE') {
    throw new Error(`Unexpected deterministic route: ${classification.primaryFamily}`);
  }
  const analysisPlan = ctx.tcctV02GetAnalysisPlan(classification);
  const base64Data = pdf.toString('base64');
  const branches = ['litigation', 'competition', 'platform'];

  const branchResults = await Promise.all(branches.map(async (branch) => {
    const request = ctx.tcctV02BuildGeminiPdfInteraction({
      model: MODEL,
      apiKey,
      apiRevision: API_REVISION,
      base64Data,
      sensitivity: 'PUBLIC',
      prompt: buildBranchPrompt(branch, [SOURCE_ID]),
      schema: buildBranchSchema(branch),
      systemInstruction: `Source-first ${branch} analysis. The attached PDF is the only case-record source. Return structured JSON only.`,
      generationConfig: { max_output_tokens: 7000 },
    });
    const result = await callInteraction(request, branch, apiKey);
    return [branch, result];
  }));

  const branchOutputs = {};
  const branchReceipts = {};
  for (const [branch, result] of branchResults) {
    branchOutputs[branch] = result.output;
    branchReceipts[branch] = result.receipt;
  }

  const fourthLayer = ctx.tcctV02BuildFourthLayerRequest({
    classification,
    analysisPlan,
    allowedSourceIds: [SOURCE_ID],
    sourceText: `[ATTACHED_PUBLIC_PDF:${SOURCE_ID}] The PDF is the only factual source; no case facts are inserted in this prompt.`,
    branchOutputs,
  });
  const finalRequest = ctx.tcctV02BuildGeminiPdfInteraction({
    model: MODEL,
    apiKey,
    apiRevision: API_REVISION,
    base64Data,
    sensitivity: 'PUBLIC',
    prompt: fourthLayer.prompt,
    schema: fourthLayer.schema,
    systemInstruction: finalSystemInstruction(),
    generationConfig: { max_output_tokens: 18000 },
  });
  const finalResult = await callInteraction(finalRequest, 'decision_intelligence', apiKey);

  const validation = ctx.tcctV02ValidateDecisionIntelligence(finalResult.output, {
    primaryFamily: classification.primaryFamily,
    allowedSourceIds: [SOURCE_ID],
    analysisPlan,
  });
  const evaluation = evaluatePublicShippingCase(finalResult.output, validation);

  writeReport({
    status: evaluation.status,
    liveCallExecuted: liveCallCount > 0,
    liveCallCount,
    model: MODEL,
    apiRevision: API_REVISION,
    sourceSha256,
    sourceBytes: pdf.length,
    fixture: metadata,
    classification,
    analysisPlan,
    branchReceipts,
    branchOutputs,
    finalReceipt: finalResult.receipt,
    finalOutput: finalResult.output,
    validation,
    checks: evaluation.checks,
    reviewStatus: 'AI_DRAFT_REVIEW_REQUIRED',
    safety: {
      publicDocumentOnly: true,
      productionWrite: false,
      deployment: false,
      merge: false,
      thaiLegalAssistantWriteback: false,
    },
  });
}

try {
  await main();
} catch (error) {
  writeReport(buildRuntimeErrorReport({
    model: MODEL,
    apiRevision: API_REVISION,
    sourceSha256: currentSourceSha256,
    liveCallCount,
    error: sanitizeError(error, selectApiKey(process.env)),
  }));
}
