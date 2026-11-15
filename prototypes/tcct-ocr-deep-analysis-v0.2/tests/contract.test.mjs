import test from 'node:test';
import assert from 'node:assert/strict';
import { loadGsFiles } from './load-gs.mjs';

const ctx = loadGsFiles([
  '25_DecisionRouter.gs',
  '35_DecisionIntelligenceContract.gs',
  '45_OutputGuard.gs',
]);

function statement(text, provenanceType = 'ANALYST_INFERENCE', sourceRefs = ['D1:CASE1']) {
  return { text, provenanceType, sourceRefs };
}

function evidence(text, legalPurpose = 'proof') {
  return { text, legalPurpose, provenanceType: 'SOURCE_FACT', sourceRefs: ['D1:CASE1'] };
}

function idealEvidence(item = 'Complete opt-out request and rejection logs') {
  return {
    element: 'coercion',
    item,
    whyItMatters: 'Shows whether the choice was practically available',
    custodian: 'platform CRM owner',
    authentication: 'native export, audit log and responsible-witness declaration',
    expectedRebuttal: 'Requests were exceptional or incomplete',
    provenanceType: 'MISSING_EVIDENCE',
    sourceRefs: [],
    numericBasisRefs: [],
  };
}

function strongerCase(proposition) {
  return {
    proposition: statement(proposition),
    evidenceNeeded: [idealEvidence()],
    expectedCounter: statement('The observed requests were exceptional', 'HYPOTHESIS', []),
    replyEvidence: [idealEvidence('Cohort-level requests, rejection reasons and response times')],
  };
}

function validOutput() {
  return {
    schemaVersion: '2.0',
    caseProfile: {
      primaryFamily: 'UNFAIR_TRADE',
      proceduralPosture: 'ADMINISTRATIVE_FACT_FINDING',
      legalBases: ['มาตรา 57'],
      modulesApplied: ['relative_bargaining_and_dependency'],
    },
    holdingBoundary: {
      whatDecisionHolds: [statement('The record was insufficient on the alleged unilateral term.', 'TCCT_HOLDING')],
      whatDecisionDoesNotDecide: [statement('It does not approve all carrier defaults.')],
    },
    adjudicativeMap: [{
      issue: 'Whether the term was imposed unilaterally',
      claimantPosition: 'It was forced',
      respondentPosition: 'A negotiated alternative existed',
      tcctReasoning: 'The parties agreed to a multi-carrier option',
      outcome: 'Not established',
      decisiveEvidence: [{ text: 'Negotiation record', provenanceType: 'TCCT_FINDING', sourceRefs: ['D1:CASE1'] }],
      notReached: [],
    }],
    theoriesOfHarm: [{
      id: 'TOH-1',
      theory: 'Constructive coercion through a restrictive default',
      disposition: 'UNTESTED',
      causalChain: [],
      actualEvidence: [evidence('A seller requested a carrier change', 'conduct')],
      idealEvidence: [idealEvidence()],
      counterArguments: [{ argument: 'The default improves delivery performance', supportingEvidence: [], reply: 'Compare outcomes and less restrictive alternatives', missingEvidence: ['SLA scorecards'] }],
      outcomeChangingCounterfactual: 'Repeated rejected opt-outs across comparable sellers',
    }],
    litigationWarRoom: {
      actualArgumentsAndEvidence: [{
        side: 'claimant',
        argument: statement('The carrier default was practically unavoidable', 'PARTY_ARGUMENT'),
        evidence: [evidence('Seller support ticket and carrier-change record', 'conduct and practical choice')],
      }],
      strongerClaimantOrRegulatorCase: [strongerCase('Prove system-wide opt-out friction and discriminatory treatment')],
      strongerRespondentDefense: [strongerCase('Prove an accessible and objective exception process')],
      missingRecord: [idealEvidence('Complete cohort-level opt-out logs')],
      proceduralChallenges: [],
      remedyOptions: [],
    },
    tcctCritique: [{
      target: 'Scope of fact finding',
      type: 'SOURCE_GROUNDED_OMISSION',
      criticism: 'The published record does not show a market-wide workflow audit.',
      supportingRefs: ['D1:CASE1'],
      limits: 'The unpublished file may contain more material.',
      fairCounterview: 'The individual allegations failed at the factual threshold.',
    }],
    academicLenses: [{
      school: 'Transaction cost economics',
      proposition: 'Specific investments can create bilateral dependency.',
      assumptions: ['platform-specific investment'],
      fitToRecord: 'Potentially relevant but not measured in the published record.',
      tension: 'Efficiency benefits may justify a default.',
      sourceStatus: 'NEEDS_RESEARCH',
      externalSourceRefs: [],
    }],
    businessTranslation: {
      thirtySecondStory: 'The dispute concerns whether a logistics default was a useful operating rule or an unavoidable tie.',
      fightInPlainLanguage: 'The regulator had to distinguish curation from coercion.',
      whyOutcome: 'The specific factual allegations were not established.',
      whatItDoesNotMean: ['It is not a blanket approval of forced logistics.'],
      roleTakeaways: {
        board: ['Set a risk appetite for affiliated-service defaults.'],
        executive: ['Require evidence of consumer and seller benefits.'],
        productOperations: ['Build a logged, usable opt-out.'],
        commercialProcurement: ['Use objective carrier-selection criteria.'],
        finance: ['Quantify cost and harm scenarios.'],
        legalCompliance: ['Preserve consent, notice and exception records.'],
        smeCounterparty: ['Verify facts and preserve requests and losses.'],
        investorLender: ['Test concentration and related-party exposure.'],
      },
      trafficLights: { green: [], yellow: [], red: [] },
      evidenceToPreserve: [],
      nextMondayDecisions: [],
      penaltyStatements: [],
    },
    quality: { confidence: 'MEDIUM', researchNeeds: [], unsupportedClaims: [] },
  };
}

test('fourth-layer schema and prompt require the requested litigation, academic and business depth', () => {
  const schema = ctx.tcctV02GetDecisionIntelligenceSchema();
  assert.ok(schema.required.includes('theoriesOfHarm'));
  assert.ok(schema.required.includes('litigationWarRoom'));
  assert.ok(schema.required.includes('academicLenses'));
  assert.ok(schema.required.includes('businessTranslation'));

  const classification = ctx.tcctV02ClassifyDecision('มาตรา 57 แพลตฟอร์มกำหนดเงื่อนไข');
  const prompt = ctx.tcctV02BuildDecisionIntelligencePrompt({
    classification,
    analysisPlan: ctx.tcctV02GetAnalysisPlan(classification),
    allowedSourceIds: ['D1:CASE1'],
    sourceText: 'SOURCE D1:CASE1',
    branchOutputs: { litigation: {}, competition: {}, platform: {} },
  });
  assert.match(prompt, /actual arguments and evidence/i);
  assert.match(prompt, /ideal evidence/i);
  assert.match(prompt, /counterarguments/i);
  assert.match(prompt, /schools of thought/i);
  assert.match(prompt, /business owners, executives/i);
  assert.match(prompt, /what the decision does not decide/i);
});

test('litigation war-room schema requires auditable argument and stronger-case records', () => {
  const schema = ctx.tcctV02GetDecisionIntelligenceSchema();
  const warRoom = schema.properties.litigationWarRoom;
  const actual = warRoom.properties.actualArgumentsAndEvidence.items;
  assert.ok(actual.required.includes('side'));
  assert.ok(actual.required.includes('argument'));
  assert.ok(actual.required.includes('evidence'));

  const stronger = warRoom.properties.strongerClaimantOrRegulatorCase.items;
  assert.ok(stronger.required.includes('proposition'));
  assert.ok(stronger.required.includes('evidenceNeeded'));
  assert.ok(stronger.required.includes('expectedCounter'));
  assert.ok(stronger.required.includes('replyEvidence'));
});

test('accepts a complete source-bounded output', () => {
  const result = ctx.tcctV02ValidateDecisionIntelligence(validOutput(), {
    primaryFamily: 'UNFAIR_TRADE',
    allowedSourceIds: ['D1:CASE1'],
    analysisPlan: { required: ['relative_bargaining_and_dependency'], optional: [], forbidden: ['merger_hhi_delta'] },
  });
  assert.equal(result.status, 'VALID', JSON.stringify(result.issues));
});

test('rejects empty war-room argument and stronger-case objects', () => {
  const actual = validOutput();
  actual.litigationWarRoom.actualArgumentsAndEvidence = [{}];
  let result = ctx.tcctV02ValidateDecisionIntelligence(actual, {
    primaryFamily: 'UNFAIR_TRADE', allowedSourceIds: ['D1:CASE1'], analysisPlan: { required: [], optional: [], forbidden: [] },
  });
  assert.ok(result.issues.some((issue) => issue.code === 'WAR_ROOM_ARGUMENT_INCOMPLETE'));

  const stronger = validOutput();
  stronger.litigationWarRoom.strongerClaimantOrRegulatorCase = [{}];
  result = ctx.tcctV02ValidateDecisionIntelligence(stronger, {
    primaryFamily: 'UNFAIR_TRADE', allowedSourceIds: ['D1:CASE1'], analysisPlan: { required: [], optional: [], forbidden: [] },
  });
  assert.ok(result.issues.some((issue) => issue.code === 'WAR_ROOM_STRONGER_CASE_INCOMPLETE'));
});

test('rejects ideal evidence that omits custodian or authentication', () => {
  const output = validOutput();
  delete output.theoriesOfHarm[0].idealEvidence[0].custodian;
  delete output.theoriesOfHarm[0].idealEvidence[0].authentication;
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, {
    primaryFamily: 'UNFAIR_TRADE', allowedSourceIds: ['D1:CASE1'], analysisPlan: { required: [], optional: [], forbidden: [] },
  });
  assert.ok(result.issues.some((issue) => issue.code === 'IDEAL_EVIDENCE_INCOMPLETE'));
});

test('rejects inferred dissenting reasons and invented numeric targets', () => {
  const output = validOutput();
  output.tcctCritique[0].criticism = 'A majority vote indicates at least one dissenting commissioner accepted the claimant theory.';
  output.theoriesOfHarm[0].idealEvidence[0].item = 'A survey proving more than 80% of merchants were blocked';
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, {
    primaryFamily: 'UNFAIR_TRADE', allowedSourceIds: ['D1:CASE1'], analysisPlan: { required: [], optional: [], forbidden: [] },
  });
  assert.ok(result.issues.some((issue) => issue.code === 'INFERRED_DISSENT_RATIONALE'));
  assert.ok(result.issues.some((issue) => issue.code === 'UNSUPPORTED_NUMERIC_TARGET'));
});

test('requires governed sources for academic claims and statutory support for penalties', () => {
  const output = validOutput();
  output.academicLenses[0].sourceStatus = 'SUPPLIED_SOURCE';
  output.businessTranslation.penaltyStatements.push({ text: 'A ten-percent fine applies.', statuteRefs: [], lawAsOf: '' });
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, {
    primaryFamily: 'UNFAIR_TRADE', allowedSourceIds: ['D1:CASE1'], analysisPlan: { required: [], optional: [], forbidden: [] },
  });
  assert.ok(result.issues.some((issue) => issue.code === 'ACADEMIC_SOURCE_MISSING'));
  assert.ok(result.issues.some((issue) => issue.code === 'PENALTY_SOURCE_MISSING'));
});

test('requires every audience role in the business translation', () => {
  const output = validOutput();
  delete output.businessTranslation.roleTakeaways.finance;
  const result = ctx.tcctV02ValidateDecisionIntelligence(output, {
    primaryFamily: 'UNFAIR_TRADE', allowedSourceIds: ['D1:CASE1'], analysisPlan: { required: [], optional: [], forbidden: [] },
  });
  assert.ok(result.issues.some((issue) => issue.code === 'BUSINESS_ROLE_MISSING'));
});
