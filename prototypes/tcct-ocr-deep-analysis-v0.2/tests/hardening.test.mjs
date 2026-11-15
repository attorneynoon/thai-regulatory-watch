import test from 'node:test';
import assert from 'node:assert/strict';
import { loadGsFiles } from './load-gs.mjs';

const ctx = loadGsFiles([
  '25_DecisionRouter.gs',
  '35_DecisionIntelligenceContract.gs',
  '45_OutputGuard.gs',
  '55_GeminiDocumentAdapter.gs',
]);

function minimalOutput() {
  return {
    schemaVersion: '2.0',
    caseProfile: {
      primaryFamily: 'UNFAIR_TRADE',
      proceduralPosture: 'ADMINISTRATIVE_FACT_FINDING',
      legalBases: ['มาตรา 57'],
      modulesApplied: [],
    },
    holdingBoundary: {
      whatDecisionHolds: [{ text: 'The allegation was not established.', provenanceType: 'TCCT_HOLDING', sourceRefs: ['D1:CASE1'] }],
      whatDecisionDoesNotDecide: [{ text: 'No blanket approval follows.', provenanceType: 'ANALYST_INFERENCE', sourceRefs: ['D1:CASE1'] }],
    },
    adjudicativeMap: [],
    theoriesOfHarm: [],
    litigationWarRoom: {
      actualArgumentsAndEvidence: [], strongerClaimantOrRegulatorCase: [], strongerRespondentDefense: [],
      missingRecord: [], proceduralChallenges: [], remedyOptions: [],
    },
    tcctCritique: [{
      target: 'published reasoning', type: 'SOURCE_GROUNDED_OMISSION',
      criticism: 'The public text does not describe a system-wide audit.',
      supportingRefs: ['D1:CASE1'], limits: 'The non-public file may contain more.', fairCounterview: 'The pleaded facts failed first.',
    }],
    academicLenses: [{
      school: 'Transaction cost economics', proposition: 'Specific investments can create dependency.', assumptions: [],
      fitToRecord: 'Potentially relevant.', tension: 'Efficiencies may justify a default.',
      sourceStatus: 'SUPPLIED_SOURCE', externalSourceRefs: ['ACADEMIC:TCE:1'],
    }],
    businessTranslation: {
      thirtySecondStory: 'A dispute about choice versus coercion.', fightInPlainLanguage: 'Whether an operating default was genuinely optional.',
      whyOutcome: 'The pleaded facts were not established.', whatItDoesNotMean: ['Not a blanket safe harbour.'],
      roleTakeaways: {
        board: ['Set risk appetite.'], executive: ['Demand evidence.'], productOperations: ['Log opt-outs.'],
        commercialProcurement: ['Use objective criteria.'], finance: ['Quantify exposure.'], legalCompliance: ['Preserve records.'],
        smeCounterparty: ['Keep requests and loss evidence.'], investorLender: ['Test concentration exposure.'],
      },
      trafficLights: { green: [], yellow: [], red: [] }, evidenceToPreserve: [], nextMondayDecisions: [], penaltyStatements: [],
    },
    quality: { confidence: 'MEDIUM', researchNeeds: [], unsupportedClaims: [] },
  };
}

const context = {
  primaryFamily: 'UNFAIR_TRADE',
  allowedSourceIds: ['D1:CASE1'],
  analysisPlan: { required: [], optional: [], forbidden: [] },
};

test('schema pins the detailed theory-of-harm and business audience contract', () => {
  const schema = ctx.tcctV02GetDecisionIntelligenceSchema();
  const theory = schema.properties.theoriesOfHarm.items;
  assert.ok(theory.required.includes('actualEvidence'));
  assert.ok(theory.required.includes('idealEvidence'));
  assert.ok(theory.required.includes('counterArguments'));
  const roles = schema.properties.businessTranslation.properties.roleTakeaways;
  assert.ok(roles.required.includes('board'));
  assert.ok(roles.required.includes('productOperations'));
  assert.ok(roles.required.includes('investorLender'));
});

test('keeps governed academic sources outside the case-record boundary', () => {
  const output = minimalOutput();
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, context);
  assert.equal(result.status, 'VALID', JSON.stringify(result.issues));
});

test('rejects cross-case references in TCCT critique supporting evidence', () => {
  const output = minimalOutput();
  output.tcctCritique[0].supportingRefs = ['D1:CASE2'];
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, context);
  assert.ok(result.issues.some((issue) => issue.code === 'CROSS_CASE_CITATION'));
});

test('requires provenance on material holding statements', () => {
  const output = minimalOutput();
  delete output.holdingBoundary.whatDecisionHolds[0].provenanceType;
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, context);
  assert.ok(result.issues.some((issue) => issue.code === 'MATERIAL_PROVENANCE_MISSING'));
});

test('requires non-empty role-specific business takeaways', () => {
  const output = minimalOutput();
  output.businessTranslation.roleTakeaways.finance = [];
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, context);
  assert.ok(result.issues.some((issue) => issue.code === 'BUSINESS_ROLE_EMPTY'));
});

test('blocks confidential native-PDF request construction until every approval is recorded', () => {
  assert.throws(() => ctx.tcctV02BuildGeminiPdfInteraction({
    model: 'approved-test-model', apiKey: 'test-key', base64Data: 'JVBERi0=', prompt: 'Analyze', schema: { type: 'object' },
    sensitivity: 'CONFIDENTIAL',
    approvals: { provider: true, retention: false, region: true, access: true },
  }), /approval/i);

  const request = ctx.tcctV02BuildGeminiPdfInteraction({
    model: 'approved-test-model', apiKey: 'test-key', base64Data: 'JVBERi0=', prompt: 'Analyze', schema: { type: 'object' },
    sensitivity: 'CONFIDENTIAL',
    approvals: { provider: true, retention: true, region: true, access: true },
  });
  assert.equal(request.body.store, false);
});

test('does not allow a zero-error OCR claim when the measured error rate is non-zero', () => {
  const result = ctx.tcctV02ValidateOcrAssessment({
    status: 'BASELINE_COMPARED', comparisonMethod: 'manual baseline', sampledPages: 5,
    characterErrorRate: 0.01, zeroErrors: true,
  });
  assert.equal(result.status, 'INVALID');
  assert.ok(result.issues.some((issue) => issue.code === 'OCR_ZERO_ERROR_CONTRADICTION'));
});
