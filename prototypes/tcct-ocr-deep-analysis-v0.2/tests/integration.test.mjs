import test from 'node:test';
import assert from 'node:assert/strict';
import { loadGsFiles } from './load-gs.mjs';

const ctx = loadGsFiles([
  '25_DecisionRouter.gs',
  '35_DecisionIntelligenceContract.gs',
  '45_OutputGuard.gs',
  '95_V02Integration.gs',
]);

test('preserves the three branches and adds decision intelligence as a serial fourth layer', () => {
  const stages = ctx.tcctV02WorkflowStages();
  assert.deepEqual(Array.from(stages.parallelBranches), ['litigation', 'competition', 'platform']);
  assert.deepEqual(Array.from(stages.serialAfterBranches), ['decision_intelligence']);
});

test('plans one fourth-layer request per decision segment with isolated sources', () => {
  const bundle = `ผลคำวินิจฉัยคณะกรรมการการแข่งขันทางการค้า กรณีผลการพิจารณาคำขออนุญาตรวมธุรกิจระหว่าง ก. และ ข.
มาตรา 51 วรรคสอง มาตรา 52 HHI
ผลคำวินิจฉัยคณะกรรมการการแข่งขันทางการค้า กรณีการแจ้งผลการรวมธุรกิจระหว่าง ค. และ ง.
มาตรา 51 วรรคหนึ่ง มีมติรับทราบ`;
  const plans = ctx.tcctV02PlanFourthLayerForBundle({
    documentId: 'D1',
    text: bundle,
    branchOutputsBySegment: {
      'D1:CASE1': { litigation: {}, competition: {}, platform: {} },
      'D1:CASE2': { litigation: {}, competition: {}, platform: {} },
    },
  });
  assert.equal(plans.length, 2);
  assert.deepEqual(Array.from(plans[0].allowedSourceIds), ['D1:CASE1']);
  assert.deepEqual(Array.from(plans[1].allowedSourceIds), ['D1:CASE2']);
});

test('rejects cross-case citations and irrelevant merger modules in an unfair-trade output', () => {
  const crossCase = ctx.tcctV02ValidateSourceBoundary({ sourceRefs: ['D1:CASE2'] }, ['D1:CASE1']);
  assert.equal(crossCase.status, 'INVALID');
  assert.ok(crossCase.issues.some((issue) => issue.code === 'CROSS_CASE_CITATION'));

  const moduleResult = ctx.tcctV02ValidateAppliedModules(
    ['relative_bargaining_and_dependency', 'merger_hhi_delta'],
    { required: ['relative_bargaining_and_dependency'], optional: [], forbidden: ['merger_hhi_delta'] },
  );
  assert.equal(moduleResult.status, 'INVALID');
  assert.ok(moduleResult.issues.some((issue) => issue.code === 'FORBIDDEN_ANALYSIS_MODULE'));
});
