import test from 'node:test';
import assert from 'node:assert/strict';
import { loadGsFiles } from './load-gs.mjs';

const ctx = loadGsFiles(['25_DecisionRouter.gs']);

test('routes a Section 57 platform dispute to unfair trade with secondary theories', () => {
  const result = ctx.tcctV02ClassifyDecision(`
    ผู้ร้องกล่าวว่าผู้ประกอบธุรกิจแพลตฟอร์มกำหนดเงื่อนไขไม่เป็นธรรม
    อาจเป็นความผิดตามมาตรา 57 และมีการกล่าวถึงมาตรา 50 และอำนาจเหนือตลาด
  `);
  assert.equal(result.primaryFamily, 'UNFAIR_TRADE');
  assert.ok(result.secondaryFamilies.includes('ABUSE_OF_DOMINANCE'));
  assert.ok(result.secondaryFamilies.includes('PLATFORM_HYBRID'));
  const plan = ctx.tcctV02GetAnalysisPlan(result);
  assert.ok(plan.required.includes('relative_bargaining_and_dependency'));
  assert.ok(plan.forbidden.includes('merger_hhi_delta'));
});

test('routes a Section 54 price discussion to horizontal agreement without inventing an enforcement element', () => {
  const result = ctx.tcctV02ClassifyDecision('คู่แข่งขันประชุมตกลงร่วมกันกำหนดราคา อาจเป็นความผิดตามมาตรา 54 (1)');
  assert.equal(result.primaryFamily, 'HORIZONTAL_AGREEMENT');
  const plan = ctx.tcctV02GetAnalysisPlan(result);
  assert.ok(plan.required.includes('agreement_direct_and_circumstantial_evidence'));
  assert.equal(plan.doctrinalGuards.enforcementMechanism, 'EVIDENCE_NOT_UNIVERSAL_ELEMENT');
  assert.ok(!plan.required.includes('market_dominance'));
});

test('distinguishes merger pre-approval from post-notification', () => {
  const pre = ctx.tcctV02ClassifyDecision('คำขออนุญาตรวมธุรกิจ ตามมาตรา 51 วรรคสอง พิจารณาปัจจัยตามมาตรา 52 และค่า HHI');
  assert.equal(pre.primaryFamily, 'MERGER_PRE_APPROVAL');
  const prePlan = ctx.tcctV02GetAnalysisPlan(pre);
  assert.ok(prePlan.required.includes('merger_hhi_delta'));
  assert.ok(prePlan.required.includes('section_52_balancing'));

  const post = ctx.tcctV02ClassifyDecision('การแจ้งผลการรวมธุรกิจ ตามมาตรา 51 วรรคหนึ่ง คณะกรรมการมีมติรับทราบ');
  assert.equal(post.primaryFamily, 'MERGER_POST_NOTIFICATION');
  const postPlan = ctx.tcctV02GetAnalysisPlan(post);
  assert.ok(postPlan.required.includes('notification_timeliness_and_completeness'));
  assert.ok(!postPlan.required.includes('section_52_balancing'));
});

test('segments a merger compilation before classification', () => {
  const bundle = `ผลคำวินิจฉัยเรื่องการรวมธุรกิจ พ.ศ. 2568
ผลคำวินิจฉัยคณะกรรมการการแข่งขันทางการค้า กรณีผลการพิจารณาคำขออนุญาตรวมธุรกิจระหว่างบริษัท ก. และบริษัท ข.
คำขออนุญาตรวมธุรกิจตามมาตรา 51 วรรคสอง และมาตรา 52
ผลคำวินิจฉัยคณะกรรมการการแข่งขันทางการค้า กรณีการแจ้งผลการรวมธุรกิจระหว่างบริษัท ค. และบริษัท ง.
การแจ้งผลการรวมธุรกิจตามมาตรา 51 วรรคหนึ่ง มีมติรับทราบ`;
  const segments = ctx.tcctV02SplitDecisionBundle(bundle, 'D1');
  assert.equal(segments.length, 2);
  assert.equal(segments[0].locator, 'D1:CASE1');
  assert.equal(segments[0].classification.primaryFamily, 'MERGER_PRE_APPROVAL');
  assert.equal(segments[1].locator, 'D1:CASE2');
  assert.equal(segments[1].classification.primaryFamily, 'MERGER_POST_NOTIFICATION');
  assert.deepEqual(Array.from(segments[0].allowedSourceIds), ['D1:CASE1']);
});
