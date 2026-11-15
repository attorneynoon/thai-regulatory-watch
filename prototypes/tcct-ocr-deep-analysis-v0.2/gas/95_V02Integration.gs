function tcctV02WorkflowStages() {
  return {
    sourcePreparation: ['source_prepare', 'decision_segment', 'case_route'],
    parallelBranches: ['litigation', 'competition', 'platform'],
    serialAfterBranches: ['decision_intelligence'],
    finalization: ['evidence_qa', 'render_candidate']
  };
}

function tcctV02PlanFourthLayerForBundle(input) {
  var value = input || {};
  if (!value.text) throw new Error('Source text is required');
  var documentId = value.documentId || 'D1';
  var segments = tcctV02SplitDecisionBundle(value.text, documentId);
  var outputs = value.branchOutputsBySegment || {};

  return segments.map(function (segment) {
    var plan = tcctV02GetAnalysisPlan(segment.classification);
    var context = {
      classification: segment.classification,
      analysisPlan: plan,
      allowedSourceIds: segment.allowedSourceIds,
      sourceText: segment.text,
      branchOutputs: outputs[segment.locator] || { litigation: {}, competition: {}, platform: {} }
    };
    return {
      segmentLocator: segment.locator,
      heading: segment.heading,
      classification: segment.classification,
      analysisPlan: plan,
      allowedSourceIds: segment.allowedSourceIds.slice(),
      request: tcctV02BuildFourthLayerRequest(context),
      reviewStatus: 'AI_DRAFT_REVIEW_REQUIRED'
    };
  });
}
