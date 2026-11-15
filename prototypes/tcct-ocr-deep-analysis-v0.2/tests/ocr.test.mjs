import test from 'node:test';
import assert from 'node:assert/strict';
import { loadGsFiles } from './load-gs.mjs';

const ctx = loadGsFiles(['45_OutputGuard.gs', '55_GeminiDocumentAdapter.gs']);

test('builds a stateless v1beta Interactions API request for a Gemini file URI', () => {
  const request = ctx.tcctV02BuildGeminiPdfInteraction({
    model: 'approved-test-model',
    apiKey: 'test-key',
    fileUri: 'https://generativelanguage.googleapis.com/v1beta/files/public-test',
    prompt: 'Analyze the public ruling',
    schema: { type: 'object', properties: {} },
  });
  assert.equal(request.url, 'https://generativelanguage.googleapis.com/v1beta/interactions');
  assert.equal(request.body.store, false);
  assert.equal(request.body.input[0].type, 'document');
  assert.equal(request.body.input[0].uri, 'https://generativelanguage.googleapis.com/v1beta/files/public-test');
  assert.equal(request.body.response_format.mime_type, 'application/json');
  assert.equal(request.headers['x-goog-api-key'], 'test-key');
  assert.equal(request.headers['Api-Revision'], '2026-05-20');
});

test('supports inline PDF data without changing the evidence contract', () => {
  const request = ctx.tcctV02BuildGeminiPdfInteraction({
    model: 'approved-test-model', apiKey: 'test-key', base64Data: 'JVBERi0=', prompt: 'Extract', schema: { type: 'object' },
  });
  assert.equal(request.body.input[0].data, 'JVBERi0=');
  assert.equal(request.body.input[0].mime_type, 'application/pdf');
});

test('blocks confidential or privileged native-PDF processing without provider approval', () => {
  assert.equal(ctx.tcctV02ChoosePdfProcessingPath({ sensitivity: 'CONFIDENTIAL', providerApproved: false }).path, 'BLOCKED_PENDING_PROVIDER_APPROVAL');
  assert.equal(ctx.tcctV02ChoosePdfProcessingPath({ sensitivity: 'PRIVILEGED', providerApproved: false }).path, 'BLOCKED_PENDING_PROVIDER_APPROVAL');
});

test('does not permit CLEAN_TEXT or zero-error claims without baseline comparison', () => {
  const invalid = ctx.tcctV02ValidateOcrAssessment({ status: 'CLEAN_TEXT', zeroErrors: true });
  assert.equal(invalid.status, 'INVALID');
  assert.ok(invalid.issues.some((issue) => issue.code === 'OCR_STATUS_UNSUPPORTED'));

  const valid = ctx.tcctV02ValidateOcrAssessment({
    status: 'BASELINE_COMPARED',
    comparisonMethod: 'native text and manual page sample',
    sampledPages: 10,
    characterErrorRate: 0.004,
  });
  assert.equal(valid.status, 'VALID', JSON.stringify(valid.issues));
});

test('removes private-use rendering artifacts', () => {
  assert.equal(ctx.tcctV02SanitizeMarkdown('A\uE803B\uE802C'), 'ABC');
});
