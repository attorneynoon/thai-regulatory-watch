import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildBlockedReport,
  buildBranchPrompt,
  evaluatePublicShippingCase,
  extractInteractionText,
  parseInteractionJson,
  selectApiKey,
} from '../scripts/public-smoke-lib.mjs';

function groundedOutput() {
  return {
    schemaVersion: '2.0',
    caseProfile: { primaryFamily: 'UNFAIR_TRADE' },
    holdingBoundary: {
      whatDecisionHolds: [
        { text: 'ผู้ร้องที่ 1 ตกลงใช้รูปแบบผู้ขนส่งหลายราย และวันที่ 20 มิถุนายน 2567 ขอเปลี่ยนผู้ให้บริการอีกครั้ง' },
        { text: 'จุด Drop off ที่ใกล้ที่สุดอยู่ประมาณ 600 เมตร ไม่ใช่ 3.3 กิโลเมตร' },
      ],
      whatDecisionDoesNotDecide: [
        { text: 'คณะกรรมการไม่ได้วินิจฉัยอำนาจเหนือตลาด เพราะไม่จำเป็นต้องพิจารณาเมื่อข้อเท็จจริงตามคำร้องไม่ปรากฏ' },
      ],
    },
    theoriesOfHarm: [
      { theory: 'constructive coercion', disposition: 'NOT_REACHED', actualEvidence: [], idealEvidence: [], counterArguments: [] },
    ],
    academicLenses: [
      { school: 'transaction cost economics', sourceStatus: 'NEEDS_RESEARCH', externalSourceRefs: [] },
    ],
    litigationWarRoom: {},
    tcctCritique: [],
    businessTranslation: {
      whatItDoesNotMean: ['ไม่ใช่การรับรองนโยบายขนส่งทุกแบบ'],
      roleTakeaways: {
        board: ['Treat the result as fact-specific.'],
        executive: ['Require evidence for default design.'],
        productOperations: ['Preserve opt-out logs.'],
        commercialProcurement: ['Use objective carrier criteria.'],
        finance: ['Quantify harm and efficiencies.'],
        legalCompliance: ['Preserve notice and consent records.'],
        smeCounterparty: ['Verify facts before filing.'],
        investorLender: ['Assess affiliate and remedy exposure.'],
      },
      penaltyStatements: [],
    },
  };
}

test('extracts structured text from the current steps/model_output response schema', () => {
  const payload = {
    id: 'int_public_test',
    status: 'completed',
    steps: [
      { type: 'thought', summary: [{ type: 'text', text: 'private summary not output' }] },
      { type: 'model_output', content: [{ type: 'text', text: '{"schemaVersion":"2.0"}' }] },
    ],
  };
  assert.equal(extractInteractionText(payload), '{"schemaVersion":"2.0"}');
  assert.deepEqual(parseInteractionJson(payload), { schemaVersion: '2.0' });
});

test('rejects a response without a text model_output step', () => {
  assert.throws(() => extractInteractionText({ steps: [{ type: 'thought' }] }), /model_output/i);
});

test('selects the first non-empty supported API key without exposing it', () => {
  assert.equal(selectApiKey({ GEMINI_API_KEY: '', GOOGLE_API_KEY: 'google-key', GOOGLE_GENAI_API_KEY: 'third-key' }), 'google-key');
  assert.equal(selectApiKey({}), '');
});

test('builds branch prompts that require actual evidence and keep the PDF as the only factual source', () => {
  const prompt = buildBranchPrompt('litigation', ['D1:CASE1']);
  assert.match(prompt, /actual arguments and evidence/i);
  assert.match(prompt, /counterarguments/i);
  assert.match(prompt, /PDF is the only case-record source/i);
  assert.doesNotMatch(prompt, /600\s*metres/i);
});

test('passes a grounded public shipping-choice result and records every smoke check', () => {
  const evaluation = evaluatePublicShippingCase(groundedOutput(), { status: 'VALID', issues: [] });
  assert.equal(evaluation.status, 'PASS', JSON.stringify(evaluation.checks));
  assert.ok(evaluation.checks.length >= 10);
  assert.ok(evaluation.checks.every((check) => check.pass));
});

test('fails unsupported OCR certainty, invented thresholds and unsourced penalty claims', () => {
  const output = groundedOutput();
  output.quality = { note: 'OCR Quality Status: CLEAN_TEXT with zero corruption' };
  output.theoriesOfHarm[0].idealEvidence.push({ item: 'Prove that >80% of merchants were blocked.' });
  output.businessTranslation.penaltyStatements.push({ text: 'Directors face criminal exposure and a 10% fine.' });
  const evaluation = evaluatePublicShippingCase(output, { status: 'VALID', issues: [] });
  assert.equal(evaluation.status, 'FAIL');
  assert.ok(evaluation.checks.some((check) => check.id === 'no_absolute_ocr_claim' && !check.pass));
  assert.ok(evaluation.checks.some((check) => check.id === 'no_unsupported_80_percent' && !check.pass));
  assert.ok(evaluation.checks.some((check) => check.id === 'no_unsourced_penalty_claim' && !check.pass));
});

test('builds an explicit non-live report when no API key is configured', () => {
  const report = buildBlockedReport({ model: 'gemini-3.8-flash', sourceSha256: 'abc123' });
  assert.equal(report.status, 'BLOCKED_NO_API_KEY');
  assert.equal(report.liveCallExecuted, false);
  assert.equal(report.model, 'gemini-3.8-flash');
  assert.equal(report.sourceSha256, 'abc123');
});
