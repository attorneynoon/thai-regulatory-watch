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
  var expression = /มาตรา\s*\d+(?:\s*วรรค\s*(?:หนึ่ง|สอง|สาม|สี่|\d+))?(?:\s*\([^)]+\))?/g;
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

function tcctV02AddNatureTag(tags, tag) {
  if (tags.indexOf(tag) === -1) tags.push(tag);
}

function tcctV02DetectNatureTags(text) {
  var tags = [];

  if (/(บังคับ.{0,40}(เข้าร่วม|ใช้|ซื้อ|รับ)|ผูก.{0,40}(สินค้า|บริการ)|forced participation|tying)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'FORCED_PARTICIPATION_OR_TYING');
  }
  if (/(เลือกปฏิบัติ|discriminat|ปฏิบัติแตกต่าง.{0,40}(ไม่มีเหตุ|ไร้เหตุ))/i.test(text)) {
    tcctV02AddNatureTag(tags, 'DISCRIMINATORY_TREATMENT');
  }
  if (/(ในเครือ|บริษัทในเครือ|บริการของตน|self-preferen|affiliated service)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'AFFILIATED_SERVICE_OR_SELF_PREFERENCING');
  }
  if (/(บอกเลิก|ยกเลิกสัญญา|ระงับบัญชี|ปฏิเสธการค้า|termination|refusal to deal)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'TERMINATION_SUSPENSION_OR_REFUSAL');
  }
  if (/(เครดิตเทอม|ระยะเวลาชำระ|ค้างชำระ|payment term|credit term)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'PAYMENT_OR_CREDIT_TERMS');
  }
  if (/(ขนส่ง|โลจิสติก|delivery|logistic)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'LOGISTICS_OR_ACCESS_RESTRICTION');
  }

  if (/(กำหนดราคา|price.?fix)/i.test(text)) tcctV02AddNatureTag(tags, 'PRICE_FIXING');
  if (/(แบ่งตลาด|แบ่งลูกค้า|market allocation)/i.test(text)) tcctV02AddNatureTag(tags, 'MARKET_OR_CUSTOMER_ALLOCATION');
  if (/(จำกัดปริมาณ|output restriction)/i.test(text)) tcctV02AddNatureTag(tags, 'OUTPUT_RESTRICTION');
  if (/(ฮั้วประมูล|bid.?rig)/i.test(text)) tcctV02AddNatureTag(tags, 'BID_RIGGING');

  if (/(ราคาขายต่อ|resale price|RPM)/i.test(text)) tcctV02AddNatureTag(tags, 'RESALE_PRICE_MAINTENANCE');
  if (/(ซื้อขายแต่เพียงผู้เดียว|exclusive dealing|ห้ามซื้อจาก)/i.test(text)) tcctV02AddNatureTag(tags, 'EXCLUSIVE_DEALING');
  if (/(MFN|most favou?red nation|price parity|เงื่อนไขเสมอภาคด้านราคา)/i.test(text)) tcctV02AddNatureTag(tags, 'MFN_OR_PARITY_CLAUSE');

  if (/(แข่งขันกัน|คู่แข่งขัน|ตลาดเดียวกัน|horizontal|ทับซ้อน)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'HORIZONTAL_OVERLAP');
  }
  if (/(ต้นน้ำ.{0,50}ปลายน้ำ|ปลายน้ำ.{0,50}ต้นน้ำ|ห่วงโซ่อุปทาน|vertical|ผู้ผลิต.{0,50}ผู้จำหน่าย)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'VERTICAL_FORECLOSURE');
  }
  if (/(ระบบนิเวศ|ecosystem|conglomerate|บริการเสริม|ผลิตภัณฑ์เกี่ยวเนื่อง)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'CONGLOMERATE_OR_ECOSYSTEM_EFFECTS');
  }
  if (/(network effect|ผลกระทบเครือข่าย|data advantage|ความได้เปรียบด้านข้อมูล)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'DATA_OR_NETWORK_EFFECTS');
  }
  if (/(failing firm|กิจการล้มเหลว|ไม่สามารถดำรงกิจการ)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'FAILING_FIRM_OR_DISTRESS');
  }
  if (/(มาตรการเยียวยา|remed|เงื่อนไขอนุญาต|monitoring trustee)/i.test(text)) {
    tcctV02AddNatureTag(tags, 'REMEDY_OR_CONDITION_DESIGN');
  }

  return tags;
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
  if (/มาตรา\s*51\s*วรรค\s*(?:สอง|2)/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_PRE_APPROVAL', 4, 'Section 51 paragraph two');
  if (/มาตรา\s*52/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_PRE_APPROVAL', 2, 'Section 52 factors');

  if (/การแจ้งผลการรวมธุรกิจ/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_POST_NOTIFICATION', 4, 'post-notification heading');
  if (/มาตรา\s*51\s*วรรค\s*(?:หนึ่ง|1)/.test(text)) tcctV02AddSignal(scores, signals, 'MERGER_POST_NOTIFICATION', 4, 'Section 51 paragraph one');
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
    natureTags: tcctV02DetectNatureTags(text),
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
        'statutory_unfairness_and_case_specific_benchmark',
        'challenged_conduct_and_comparators',
        'objective_justification_and_proportionality',
        'harm_causation_and_remedy',
        'notice_cure_and_procedural_fairness'
      ],
      optional: [
        'bargaining_context_and_dependency_if_relevant',
        'market_power_if_reached',
        'platform_multi_sided_economics'
      ],
      forbidden: ['merger_hhi_delta_if_supported', 'section_52_balancing'],
      doctrinalGuards: {
        dependency: 'CONTEXT_NOT_UNIVERSAL_ELEMENT',
        marketDefinition: 'ONLY_IF_REACHED_OR_NECESSARY'
      }
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
      forbidden: ['merger_hhi_delta_if_supported', 'section_52_balancing', 'market_dominance'],
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
        'market_structure_and_concentration_evidence',
        'unilateral_coordinated_vertical_conglomerate_effects',
        'entry_expansion_and_buyer_power',
        'efficiencies_and_failing_firm',
        'section_52_balancing',
        'conditions_remedies_and_monitoring'
      ],
      optional: ['merger_hhi_delta_if_supported', 'innovation_data_and_ecosystem_effects'],
      forbidden: ['section_57_general_fairness_substitute'],
      doctrinalGuards: { hhi: 'CONDITIONAL_METRIC_REPORT_LEVEL_AND_DELTA_IF_SUPPORTED' }
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
    doctrinalGuards: JSON.parse(JSON.stringify(plan.doctrinalGuards)),
    natureTags: classification && classification.natureTags ? classification.natureTags.slice() : []
  };
}

function tcctV02StripHeadingPrefix(value) {
  return String(value || '').replace(/^\s*(?:#{1,6}\s*|[-*]\s*)/, '').trim();
}

function tcctV02SplitDecisionBundle(sourceText, documentId) {
  var text = String(sourceText == null ? '' : sourceText).replace(/\r\n?/g, '\n');
  var id = documentId || 'D1';
  var lines = text.split('\n');
  var starts = [];
  lines.forEach(function (line, index) {
    var normalized = tcctV02StripHeadingPrefix(line);
    if (/^ผลคำวินิจฉัยคณะกรรมการการแข่งขันทางการค้า.*กรณี/.test(normalized)) starts.push(index);
  });

  if (starts.length === 0) {
    return [{
      locator: id + ':CASE1',
      heading: tcctV02StripHeadingPrefix(lines[0] || ''),
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
    var segmentLines = lines.slice(start, end);
    segmentLines[0] = tcctV02StripHeadingPrefix(segmentLines[0]);
    var segmentText = segmentLines.join('\n').trim();
    return {
      locator: locator,
      heading: tcctV02StripHeadingPrefix(lines[start]),
      text: segmentText,
      startLine: start + 1,
      endLine: end,
      classification: tcctV02ClassifyDecision(segmentText),
      allowedSourceIds: [locator]
    };
  });
}
