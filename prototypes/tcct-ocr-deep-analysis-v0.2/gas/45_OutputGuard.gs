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

function tcctV02LastPathField(path) {
  var parts = String(path || '').split('.');
  return parts[parts.length - 1].replace(/\[\d+\]$/, '');
}

function tcctV02ValidateSourceBoundary(output, allowedSourceIds) {
  var issues = [];
  var allowed = allowedSourceIds || [];
  tcctV02Walk(output, '', function (value, path) {
    var field = tcctV02LastPathField(path);
    if ((field !== 'sourceRefs' && field !== 'supportingRefs') || !Array.isArray(value)) return;
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
    if (value.zeroErrors === true && Number(value.characterErrorRate) !== 0) {
      issues.push(tcctV02Issue('OCR_ZERO_ERROR_CONTRADICTION', 'zeroErrors', 'Measured character error rate is non-zero'));
    }
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

function tcctV02ValidateMaterialStatement(statement, path, issues) {
  if (!statement || typeof statement !== 'object') {
    issues.push(tcctV02Issue('MATERIAL_STATEMENT_INVALID', path));
    return;
  }
  if (!statement.text) issues.push(tcctV02Issue('MATERIAL_TEXT_MISSING', path + '.text'));
  if (!statement.provenanceType || TCCT_V02_PROVENANCE_TYPES.indexOf(statement.provenanceType) === -1) {
    issues.push(tcctV02Issue('MATERIAL_PROVENANCE_MISSING', path + '.provenanceType'));
  }
  if (!Array.isArray(statement.sourceRefs)) {
    issues.push(tcctV02Issue('MATERIAL_SOURCE_REFS_MISSING', path + '.sourceRefs'));
    return;
  }
  var grounded = ['SOURCE_FACT', 'PARTY_ARGUMENT', 'TCCT_FINDING', 'TCCT_HOLDING', 'ANALYST_INFERENCE'];
  if (grounded.indexOf(statement.provenanceType) !== -1 && statement.sourceRefs.length === 0) {
    issues.push(tcctV02Issue('MATERIAL_SOURCE_REFS_EMPTY', path + '.sourceRefs'));
  }
}

function tcctV02ValidateHoldingBoundary(boundary, issues) {
  var value = boundary || {};
  ['whatDecisionHolds', 'whatDecisionDoesNotDecide'].forEach(function (field) {
    if (!Array.isArray(value[field])) return;
    value[field].forEach(function (statement, index) {
      tcctV02ValidateMaterialStatement(statement, 'holdingBoundary.' + field + '[' + index + ']', issues);
    });
  });
}

function tcctV02ValidateActualEvidence(theories, issues) {
  (theories || []).forEach(function (theory, theoryIndex) {
    (theory.actualEvidence || []).forEach(function (evidence, evidenceIndex) {
      var path = 'theoriesOfHarm[' + theoryIndex + '].actualEvidence[' + evidenceIndex + ']';
      tcctV02ValidateMaterialStatement(evidence, path, issues);
      if (!evidence.legalPurpose) issues.push(tcctV02Issue('EVIDENCE_LEGAL_PURPOSE_MISSING', path + '.legalPurpose'));
    });
  });
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

  tcctV02ValidateHoldingBoundary(value.holdingBoundary, issues);
  tcctV02ValidateActualEvidence(value.theoriesOfHarm, issues);

  (value.theoriesOfHarm || []).forEach(function (theory, theoryIndex) {
    if (!theory.id || !theory.theory || !theory.disposition) {
      issues.push(tcctV02Issue('THEORY_OF_HARM_INCOMPLETE', 'theoriesOfHarm[' + theoryIndex + ']'));
    }
    (theory.idealEvidence || []).forEach(function (evidence, evidenceIndex) {
      var path = 'theoriesOfHarm[' + theoryIndex + '].idealEvidence[' + evidenceIndex + ']';
      var required = [
        'element', 'item', 'whyItMatters', 'custodian', 'authentication',
        'expectedRebuttal', 'provenanceType', 'sourceRefs', 'numericBasisRefs'
      ];
      var missing = required.filter(function (key) {
        return evidence[key] == null || evidence[key] === '' || ((key === 'sourceRefs' || key === 'numericBasisRefs') && !Array.isArray(evidence[key]));
      });
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
    if (!roleTakeaways || !Array.isArray(roleTakeaways[role])) {
      issues.push(tcctV02Issue('BUSINESS_ROLE_MISSING', 'businessTranslation.roleTakeaways.' + role));
    } else if (roleTakeaways[role].length === 0) {
      issues.push(tcctV02Issue('BUSINESS_ROLE_EMPTY', 'businessTranslation.roleTakeaways.' + role));
    }
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
