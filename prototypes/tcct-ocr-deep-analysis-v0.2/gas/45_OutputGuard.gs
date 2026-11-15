function tcctV02Issue(code, path, message) {
  return { code: code, path: path || '', message: message || code };
}

function tcctV02Walk(value, path, visitor) {
  visitor(value, path);
  if (Array.isArray(value)) {
    value.forEach(function (item, index) { tcctV02Walk(item, path + '[' + index + ']', visitor); });
  } else if (value && typeof value === 'object') {
    Object.keys(value).forEach(function (key) {
      tcctV02Walk(value[key], path ? path + '.' + key : key, visitor);
    });
  }
}

function tcctV02ValidateSourceBoundary(output, allowedSourceIds) {
  var issues = [];
  var allowed = allowedSourceIds || [];
  tcctV02Walk(output, '', function (value, path) {
    if (!/sourceRefs$/.test(path) || !Array.isArray(value)) return;
    value.forEach(function (reference) {
      var valid = allowed.some(function (prefix) {
        return reference === prefix || String(reference).indexOf(prefix + ':') === 0;
      });
      if (!valid) issues.push(tcctV02Issue('CROSS_CASE_CITATION', path, 'Source reference is outside the decision segment: ' + reference));
    });
  });
  return { status: issues.length ? 'INVALID' : 'VALID', issues: issues };
}

function tcctV02ValidateAppliedModules(appliedModules, analysisPlan) {
  var applied = appliedModules || [];
  var plan = analysisPlan || { required: [], optional: [], forbidden: [] };
  var issues = [];
  (plan.required || []).forEach(function (moduleName) {
    if (applied.indexOf(moduleName) === -1) issues.push(tcctV02Issue('REQUIRED_ANALYSIS_MODULE_MISSING', 'caseProfile.modulesApplied', moduleName));
  });
  (plan.forbidden || []).forEach(function (moduleName) {
    if (applied.indexOf(moduleName) !== -1) issues.push(tcctV02Issue('FORBIDDEN_ANALYSIS_MODULE', 'caseProfile.modulesApplied', moduleName));
  });
  return { status: issues.length ? 'INVALID' : 'VALID', issues: issues };
}

function tcctV02ValidateOcrAssessment(assessment) {
  var value = assessment || {};
  var issues = [];
  var allowed = ['UNCHECKED', 'TEXT_EXTRACTED', 'MANUAL_SAMPLE_REVIEWED', 'BASELINE_COMPARED', 'FAILED'];
  if (allowed.indexOf(value.status) === -1) issues.push(tcctV02Issue('OCR_STATUS_UNSUPPORTED', 'status', 'Unsupported OCR status: ' + value.status));
  if (value.zeroErrors === true && value.status !== 'BASELINE_COMPARED') {
    issues.push(tcctV02Issue('OCR_ABSOLUTE_CLAIM_UNPROVEN', 'zeroErrors', 'A zero-error claim requires a defined baseline comparison'));
  }
  if (value.status === 'BASELINE_COMPARED') {
    if (!value.comparisonMethod) issues.push(tcctV02Issue('OCR_COMPARISON_METHOD_MISSING', 'comparisonMethod'));
    if (!(Number(value.sampledPages) > 0)) issues.push(tcctV02Issue('OCR_SAMPLE_SIZE_MISSING', 'sampledPages'));
    if (typeof value.characterErrorRate !== 'number') issues.push(tcctV02Issue('OCR_ERROR_RATE_MISSING', 'characterErrorRate'));
  }
  return { status: issues.length ? 'INVALID' : 'VALID', issues: issues };
}

function tcctV02SanitizeMarkdown(value) {
  return String(value == null ? '' : value).replace(/[\uE000-\uF8FF]/g, '');
}

function tcctV02ContainsInferredDissent(value) {
  var found = false;
  var expression = /(majority vote indicates|at least one dissenting commissioner|เสียงข้างมาก.{0,60}(แสดง|หมายความ|ชี้))/i;
  tcctV02Walk(value, '', function (item) {
    if (typeof item === 'string' && expression.test(item)) found = true;
  });
  return found;
}

function tcctV02ValidateDecisionIntelligence(output, context) {
  var issues = [];
  var value = output || {};
  var requiredTop = [
    'schemaVersion', 'caseProfile', 'holdingBoundary', 'adjudicativeMap', 'theoriesOfHarm',
    'litigationWarRoom', 'tcctCritique', 'academicLenses', 'businessTranslation', 'quality'
  ];
  requiredTop.forEach(function (key) {
    if (value[key] == null) issues.push(tcctV02Issue('TOP_LEVEL_SECTION_MISSING', key, key));
  });

  if (value.schemaVersion && value.schemaVersion !== '2.0') issues.push(tcctV02Issue('SCHEMA_VERSION_MISMATCH', 'schemaVersion'));
  if (value.caseProfile && context && context.primaryFamily && value.caseProfile.primaryFamily !== context.primaryFamily) {
    issues.push(tcctV02Issue('CASE_FAMILY_MISMATCH', 'caseProfile.primaryFamily'));
  }

  var moduleResult = tcctV02ValidateAppliedModules(
    value.caseProfile ? value.caseProfile.modulesApplied : [],
    context ? context.analysisPlan : null
  );
  issues = issues.concat(moduleResult.issues);

  (value.theoriesOfHarm || []).forEach(function (theory, theoryIndex) {
    if (!theory.id || !theory.theory || !theory.disposition) {
      issues.push(tcctV02Issue('THEORY_OF_HARM_INCOMPLETE', 'theoriesOfHarm[' + theoryIndex + ']'));
    }
    (theory.idealEvidence || []).forEach(function (evidence, evidenceIndex) {
      var path = 'theoriesOfHarm[' + theoryIndex + '].idealEvidence[' + evidenceIndex + ']';
      var required = ['element', 'item', 'whyItMatters', 'custodian', 'authentication', 'expectedRebuttal', 'provenanceType', 'sourceRefs'];
      var missing = required.filter(function (key) { return evidence[key] == null || evidence[key] === ''; });
      if (missing.length) issues.push(tcctV02Issue('IDEAL_EVIDENCE_INCOMPLETE', path, missing.join(', ')));
      var numericText = [evidence.item, evidence.whyItMatters].join(' ');
      if (/\b\d+(?:\.\d+)?\s*%/.test(numericText) && !(evidence.numericBasisRefs && evidence.numericBasisRefs.length)) {
        issues.push(tcctV02Issue('UNSUPPORTED_NUMERIC_TARGET', path, numericText));
      }
    });
  });

  (value.academicLenses || []).forEach(function (lens, index) {
    var path = 'academicLenses[' + index + ']';
    if (['SUPPLIED_SOURCE', 'NEEDS_RESEARCH'].indexOf(lens.sourceStatus) === -1) {
      issues.push(tcctV02Issue('ACADEMIC_SOURCE_STATUS_INVALID', path + '.sourceStatus'));
    }
    if (lens.sourceStatus === 'SUPPLIED_SOURCE' && !(lens.externalSourceRefs && lens.externalSourceRefs.length)) {
      issues.push(tcctV02Issue('ACADEMIC_SOURCE_MISSING', path + '.externalSourceRefs'));
    }
  });

  var roleTakeaways = value.businessTranslation && value.businessTranslation.roleTakeaways;
  var roles = ['board', 'executive', 'productOperations', 'commercialProcurement', 'finance', 'legalCompliance', 'smeCounterparty', 'investorLender'];
  roles.forEach(function (role) {
    if (!roleTakeaways || !Array.isArray(roleTakeaways[role])) issues.push(tcctV02Issue('BUSINESS_ROLE_MISSING', 'businessTranslation.roleTakeaways.' + role));
  });

  var penaltyStatements = value.businessTranslation && value.businessTranslation.penaltyStatements || [];
  penaltyStatements.forEach(function (statement, index) {
    if (!(statement.statuteRefs && statement.statuteRefs.length) || !statement.lawAsOf) {
      issues.push(tcctV02Issue('PENALTY_SOURCE_MISSING', 'businessTranslation.penaltyStatements[' + index + ']'));
    }
  });

  if (tcctV02ContainsInferredDissent(value)) issues.push(tcctV02Issue('INFERRED_DISSENT_RATIONALE', 'tcctCritique'));

  var boundaryResult = tcctV02ValidateSourceBoundary(value, context ? context.allowedSourceIds : []);
  issues = issues.concat(boundaryResult.issues);

  return { status: issues.length ? 'INVALID' : 'VALID', issues: issues };
}
