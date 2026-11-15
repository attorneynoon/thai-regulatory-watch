var TCCT_V02_CASE_FAMILIES = [
  'UNFAIR_TRADE',
  'HORIZONTAL_AGREEMENT',
  'VERTICAL_AGREEMENT',
  'ABUSE_OF_DOMINANCE',
  'MERGER_PRE_APPROVAL',
  'MERGER_POST_NOTIFICATION',
  'UNKNOWN'
];

function tcctV02NormalizeThaiDigits(value) {
  var digits = '๐๑๒๓๔๕๖๗๘๙';
  return String(value == null ? '' : value).replace(/[๐-๙]/g, function (character) {
    return String(digits.indexOf(character));
  });
}

function tcctV02AddSignal(scores, signals, family, points, signal) {
  scores[family] += points;
  signals.push({ family: family, points: points, signal: signal });
}

function tcctV02ExtractLegalBases(text) {
  var result = [];
  var seen = {};
  var expression = /มาตรา\s*\d+(?:\s*วรรค(?:หนึ่ง|สอง|สาม|สี่|\d+))?(?:\s*\([^)]+\))?/g;
  var match;
  while ((match = expression.exec(text)) !== null) {
    var value = match[0].replace(/\s+/g, ' ').trim();
    if (!seen[value]) {
      seen[value] = true;
      result.push(value);
    }
  }
  return result;
}

function tcctV02ClassifyDecision(sourceText) {
  var text = tcctV02NormalizeThaiDigits(sourceText);
  var scores = {
    UNFAIR_TRADE: 0,
    HORIZONTAL_AGREEMENT: 0,
    VERTICAL_AGREEMENT: 0,
    ABUSE_OF_DOMINANCE: 0,
    MERGER_PRE_APPROVAL: 0,
    MERGER_POST_NOTIFICATION: 0
  };
  var signals = [];

  if (/คำขออนุญาตรวมธุรกิจ/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_PRE_APPROVAL', 4, 'pre-approval heading');
  if (/มาตรา\s*51\s*วรรคสอง/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_PRE_APPROVAL', 4, 'Section 51 paragraph two');
  if (/มาตรา\s*52/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_PRE_APPROVAL', 2, 'Section 52 factors');

  if (/การแจ้งผลการรวมธุรกิจ/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_POST_NOTIFICATION', 4, 'post-notification heading');
  if (/มาตรา\s*51\s*วรรคหนึ่ง/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_POST_NOTIFICATION', 4, 'Section 51 paragraph one');
  if (/มีมติรับทราบ/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_POST_NOTIFICATION', 2, 'acknowledgement disposition');

  if (/มาตรา\s*54/.test(text)) tcctV02AddSignal(scores, signals, 'HORIZONTAL_AGREEMENT', 4, 'Section 54');
  if (/(ตกลงร่วมกันกำหนดราคา|ฮั้ว|price.?fix|แบ่งตลาด|จำกัดปริมาณ)/i.test(text)) tcctV02AddSignal(scores, signals, 'HORIZONTAL_AGREEMENT', 3, 'horizontal restraint language');
  if (/คู่แข่งขัน/.test(text)) tcctV02AddSignal(scores, signals, 'HORIZONTAL_AGREEMENT', 1, 'competitor relationship');

  if (/มาตรา\s*55/.test(text)) tcctV02AddSignal(scores, signals, 'VERTICAL_AGREEMENT', 4, 'Section 55');
  if (/(ผู้ผลิต.*ผู้จำหน่าย|ต้นน้ำ.*ปลายน้ำ|vertical restraint|ราคาขายต่อ)/i.test(text)) tcctV02AddSignal(scores, signals, 'VERTICAL_AGREEMENT', 2, 'vertical relationship language');

  if (/มาตรา\s*57/.test(text)) tcctV02AddSignal(scores, signals, 'UNFAIR_TRADE', 4, 'Section 57');
  if (/(ปฏิบัติทางการค้าที่ไม่เป็นธรรม|เงื่อนไขไม่เป็นธรรม|ผลเสียหายแก่ผู้ประกอบธุรกิจรายอื่น|บอกเลิกสัญญาอย่างไม่เป็นธรรม)/.test(text)) {
    tcctV02AddSignal(scores, signals, 'UNFAIR_TRADE', 2, 'unfair-trade language');
  }

  if (/มาตรา\s*50/.test(text)) tcctV02AddSignal(scores, signals, 'ABUSE_OF_DOMINANCE', 4, 'Section 50');
  if (/อำนาจเหนือตลาด/.test(text)) tcctV02AddSignal(scores, signals, 'ABUSE_OF_DOMINANCE', 2, 'dominance language');

  var priority = [
    'MERGER_PRE_APPROVAL',
    'MERGER_POST_NOTIFICATION',
    'HORIZONTAL_AGREEMENT',
    'VERTICAL_AGREEMENT',
    'UNFAIR_TRADE',
    'ABUSE_OF_DOMINANCE'
  ];
  var ranked = priority.map(function (family, index) {
    return { family: family, score: scores[family], priority: index };
  }).sort(function (left, right) {
    if (right.score !== left.score) return right.score - left.score;
    return left.priority - right.priority;
  });

  var primaryFamily = ranked[0].score > 0 ? ranked[0].family : 'UNKNOWN';
  var secondaryFamilies = [];
  ranked.forEach(function (entry) {
    if (entry.family !== primaryFamily && entry.score >= 4) secondaryFamilies.push(entry.family);
  });
  if (/(แพลตฟอร์ม|e-?marketplace|marketplace|multi-sided|ดิจิทัลแพลตฟอร์ม)/i.test(text)) {
    secondaryFamilies.push('PLATFORM_HYBRID');
  }

  var postureByFamily = {
    UNFAIR_TRADE: 'ADMINISTRATIVE_FACT_FINDING',
    HORIZONTAL_AGREEMENT: 'ENFORCEMENT_OR_NON_PROSECUTION',
    VERTICAL_AGREEMENT: 'ENFORCEMENT_OR_NON_PROSECUTION',
    ABUSE_OF_DOMINANCE: 'ADMINISTRATIVE_FACT_FINDING',
    MERGER_PRE_APPROVAL: 'PRE_MERGER_AUTHORIZATION',
    MERGER_POST_NOTIFICATION: 'POST_MERGER_NOTIFICATION',
    UNKNOWN: 'UNKNOWN'
  };
  var margin = ranked[0].score - (ranked[1] ? ranked[1].score : 0);
  var confidence = ranked[0].score >= 7 || margin >= 3 ? 'HIGH' : (ranked[0].score >= 4 ? 'MEDIUM' : 'LOW');

  return {
    primaryFamily: primaryFamily,
    secondaryFamilies: secondaryFamilies.filter(function (value, index, array) { return array.indexOf(value) === index; }),
    proceduralPosture: postureByFamily[primaryFamily],
    legalBases: tcctV02ExtractLegalBases(text),
    confidence: confidence,
    scores: scores,
    signals: signals
  };
}

function tcctV02GetAnalysisPlan(classification) {
  var family = classification && classification.primaryFamily ? classification.primaryFamily : 'UNKNOWN';
  var plans = {
    UNFAIR_TRADE: {
      required: [
        'relative_bargaining_and_dependency',
        'challenged_conduct_and_comparators',
        'objective_justification_and_proportionality',
        'harm_causation_and_remedy',
        'notice_cure_and_procedural_fairness'
      ],
      optional: ['market_power_if_reached', 'platform_multi_sided_economics'],
      forbidden: ['merger_hhi_delta', 'section_52_balancing'],
      doctrinalGuards: { marketDefinition: 'ONLY_IF_REACHED_OR_NECESSARY' }
    },
    HORIZONTAL_AGREEMENT: {
      required: [
        'agreement_direct_and_circumstantial_evidence',
        'object_effect_and_causal_theory',
        'implementation_monitoring_and_attribution',
        'withdrawal_settlement_and_ne_bis_in_idem',
        'procedural_and_evidentiary_defenses'
      ],
      optional: ['market_context_without_dominance_requirement'],
      forbidden: ['merger_hhi_delta', 'section_52_balancing', 'market_dominance'],
      doctrinalGuards: { enforcementMechanism: 'EVIDENCE_NOT_UNIVERSAL_ELEMENT' }
    },
    VERTICAL_AGREEMENT: {
      required: [
        'vertical_relationship_and_restraint',
        'foreclosure_or_efficiency_theory',
        'coverage_duration_and_alternatives',
        'less_restrictive_means_and_pass_through'
      ],
      optional: ['market_power_if_required'],
      forbidden: ['section_52_balancing'],
      doctrinalGuards: { perSeTreatment: 'DO_NOT_ASSUME' }
    },
    ABUSE_OF_DOMINANCE: {
      required: [
        'relevant_market',
        'market_power',
        'challenged_conduct',
        'exploitative_or_exclusionary_mechanism',
        'foreclosure_causation_efficiencies_and_remedy'
      ],
      optional: ['platform_multi_sided_economics'],
      forbidden: ['section_52_balancing'],
      doctrinalGuards: { dominance: 'SEPARATE_STATUS_FROM_ABUSE' }
    },
    MERGER_PRE_APPROVAL: {
      required: [
        'jurisdiction_control_and_thresholds',
        'overlaps_and_counterfactual',
        'merger_hhi_delta',
        'unilateral_coordinated_vertical_conglomerate_effects',
        'entry_expansion_and_buyer_power',
        'efficiencies_and_failing_firm',
        'section_52_balancing',
        'conditions_remedies_and_monitoring'
      ],
      optional: ['innovation_data_and_ecosystem_effects'],
      forbidden: ['section_57_general_fairness_substitute'],
      doctrinalGuards: { hhi: 'REPORT_LEVEL_AND_DELTA_SEPARATELY' }
    },
    MERGER_POST_NOTIFICATION: {
      required: [
        'control_threshold_and_transaction_perimeter',
        'notification_timeliness_and_completeness',
        'structural_change_summary'
      ],
      optional: ['effects_only_if_decision_reaches_them'],
      forbidden: ['section_52_balancing', 'full_remedy_design_without_source_basis'],
      doctrinalGuards: { meritsReview: 'DO_NOT_INVENT_PRE_APPROVAL_REVIEW' }
    },
    UNKNOWN: {
      required: ['identify_legal_basis_and_procedural_posture'],
      optional: [],
      forbidden: ['case_specific_conclusion_without_classification'],
      doctrinalGuards: {}
    }
  };
  var plan = plans[family] || plans.UNKNOWN;
  return {
    family: family,
    required: plan.required.slice(),
    optional: plan.optional.slice(),
    forbidden: plan.forbidden.slice(),
    doctrinalGuards: JSON.parse(JSON.stringify(plan.doctrinalGuards))
  };
}

function tcctV02SplitDecisionBundle(sourceText, documentId) {
  var text = String(sourceText == null ? '' : sourceText).replace(/\r\n?/g, '\n');
  var id = documentId || 'D1';
  var lines = text.split('\n');
  var starts = [];
  lines.forEach(function (line, index) {
    if (/^ผลคำวินิจฉัยคณะกรรมการการแข่งขันทางการค้า.*กรณี/.test(line.trim())) starts.push(index);
  });

  if (starts.length === 0) {
    return [{
      locator: id + ':CASE1',
      heading: lines[0] || '',
      text: text,
      startLine: 1,
      endLine: lines.length,
      classification: tcctV02ClassifyDecision(text),
      allowedSourceIds: [id + ':CASE1']
    }];
  }

  return starts.map(function (start, index) {
    var end = index + 1 < starts.length ? starts[index + 1] : lines.length;
    var locator = id + ':CASE' + (index + 1);
    var segmentText = lines.slice(start, end).join('\n').trim();
    return {
      locator: locator,
      heading: lines[start].trim(),
      text: segmentText,
      startLine: start + 1,
      endLine: end,
      classification: tcctV02ClassifyDecision(segmentText),
      allowedSourceIds: [locator]
    };
  });
}
