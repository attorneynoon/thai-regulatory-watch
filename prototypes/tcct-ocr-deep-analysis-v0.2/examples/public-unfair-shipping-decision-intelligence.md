# Illustrative Actual Use — Public Shipping-Choice Decision

**Status:** worked example for the v0.2 contract; not live Gemini output and not a final legal opinion.  
**Source boundary:** one public TCCT decision segment only.  
**Primary family:** `UNFAIR_TRADE`  
**Secondary family:** `ABUSE_OF_DOMINANCE`, `PLATFORM_HYBRID`  
**Nature tags:** `LOGISTICS_OR_ACCESS_RESTRICTION`, potentially `AFFILIATED_SERVICE_OR_SELF_PREFERENCING` only if affiliation evidence is supplied.

## 1. Thirty-second story

The complainants said a marketplace forced them to use unsuitable delivery arrangements. The Commission closed the matter because the particular facts pleaded did not hold up: one complainant later agreed to a multi-carrier arrangement and obtained another carrier change, while the other complainant’s key distance assertion was contradicted by the investigation. The decision therefore defeats these complaints on their facts; it does not create a blanket safe harbour for restrictive logistics defaults.

## 2. Holding boundary

### What the decision holds

- The first complainant’s pleaded unilateral-imposition theory was not sufficiently established after the parties agreed on a multi-carrier arrangement and a later carrier change was implemented.
- The second complainant’s distance-based burden allegation was not sufficiently established because the relevant drop-off point was approximately 600 metres away rather than 3.3 kilometres.
- Once the alleged conduct was not established, the Commission did not need to decide whether the respondent was dominant.
- The new complaint was treated as factually separate from a prior complaint rather than automatically barred as the same continuing act.

### What the decision does not decide

- whether every platform-wide logistics default is fair;
- whether ordinary sellers had a practical and timely self-service opt-out;
- whether carrier assignment systematically preferred an affiliate;
- whether independent carriers suffered foreclosure or lost route density;
- whether the platform was dominant;
- whether a different complainant with verified facts and stronger records could succeed.

## 3. Theory-of-harm matrix

| Theory | Disposition | Why |
|---|---|---|
| Claimant-specific unilateral carrier imposition | `REJECTED` at the factual threshold | the subsequent agreement and implemented carrier change undermined the pleaded unilateral-imposition account |
| Claimant-specific excessive-distance burden | `REJECTED` at the factual threshold | the investigated distance was materially different from the allegation |
| System-wide constructive coercion through difficult opt-out workflows | `NOT_REACHED` | the public reasoning does not show a cohort-wide workflow audit |
| Affiliated-carrier self-preferencing | `UNTESTED` unless affiliation/algorithm evidence is supplied | the theory requires proof of affiliation, decision criteria and discriminatory effect |
| Foreclosure or raising independent carriers’ costs | `UNTESTED` | requires market-wide volume, route-density, cost and entry/exit evidence |

## 4. Actual arguments and evidence

### Complainant side

- forced or unsuitable carrier assignment;
- delayed/non-pickup problems and reputational harm;
- an allegedly more distant drop-off arrangement.

### Respondent / investigation side

- communications and later agreement supporting a multi-carrier arrangement;
- the later request and implementation of another carrier change;
- objective location/distance checking contradicting the 3.3-kilometre premise.

### Evidentiary use

| Evidence | Legal purpose |
|---|---|
| communications and ticket history | whether the term was unilaterally imposed or negotiated/cured |
| later carrier-change request and implementation | practical availability of an alternative in the complainant’s specific case |
| GIS/distance record | accuracy of the burden allegation and causation |
| sales/revenue information | possible threshold context, not a substitute for proof of the challenged conduct |

## 5. Stronger claimant or regulator case

A stronger case would not rely only on two disputed anecdotes. It would seek:

1. native exports of all carrier-change requests, rejection reasons, response times and outcomes by seller cohort;
2. product specifications and UI event logs showing the number of steps, delay and abandonment rate for opt-out requests;
3. algorithmic rules, model features and change history governing carrier assignment;
4. objective affiliation/conflict evidence and internal communications about affiliated-carrier volume targets;
5. seller-level order, cancellation, payout, complaint and reputational-loss data tied to the challenged assignment;
6. carrier-level pricing, pickup, P50/P90 delivery, loss/damage and COD-reconciliation performance;
7. independent-carrier parcel volume, route density, unit costs, entry/exit and capacity evidence;
8. comparator evidence showing how similarly situated sellers were treated;
9. evidence that any post-complaint cure was exceptional rather than an ordinary, usable process.

No arbitrary “more than 80%” threshold should be inserted without a defined population, sampling method and economic/legal basis.

## 6. Stronger respondent defense

The respondent would defend better by preserving and producing:

- clear pre-contract notice and versioned seller consent;
- a genuinely accessible opt-out and exception process with service levels;
- objective carrier-selection rules based on price, proximity, capacity and quality;
- audit logs showing that affiliation is not an improper weighting factor;
- consumer and seller efficiency evidence, including pass-through;
- contemporaneous reason codes for each refusal or delay;
- proof that complaint-specific cures were part of a general policy rather than litigation-only exceptions;
- independent validation of GIS and logistics-performance data.

## 7. Counterarguments and replies

### Efficiency defense

**Argument:** a default carrier improves delivery reliability and consumer experience.  
**Evidence needed:** before/after service metrics, peak-capacity data, loss/damage rates and cost pass-through.  
**Reply:** even a beneficial default may be disproportionate if switching is practically unavailable or an affiliate is preferred despite inferior performance.

### Consent defense

**Argument:** sellers accepted the logistics policy when opening the shop.  
**Evidence needed:** versioned notices, informed consent and a real alternative.  
**Reply:** formal acceptance does not alone resolve surprise changes, lock-in, high switching costs or a non-functional exception path.

### Cure defense

**Argument:** the platform granted a multi-carrier option and later change.  
**Evidence needed:** ticket history and general policy.  
**Reply:** a complaint-specific cure may defeat the individual allegation but does not by itself establish that ordinary sellers have equivalent access.

## 8. Fair criticism of TCCT

### Source-grounded limitation

The published reasoning resolves the two complaints at the factual threshold and does not show a system-wide workflow or algorithm audit. That limits the decision’s value as general guidance on platform defaults.

### Fair counterview

An authority need not decide market power, foreclosure or systemic design when the particular conduct alleged is not established. Doing so could become an advisory opinion disconnected from the proven record.

### Process-design question

A future investigation could separate two tracks:

- adjudication of the complainants’ specific facts; and
- a policy or sector inquiry into default design, affiliate preference and access to alternatives.

### Loopholes and repeatability risk

- **Complaint-specific cure:** a firm may cure only the seller who complains while leaving the underlying design unchanged.
- **Evidence asymmetry:** the platform holds the workflow and algorithm records needed to prove or disprove system-wide coercion.
- **Anecdote trap:** weak individual facts can prevent examination of a potentially broader pattern.
- **Overreading dismissal:** business teams may misread a factual dismissal as approval of all similar conduct.

## 9. Academic depth requiring governed sources

| School/lens | Useful question | Status before sources are attached |
|---|---|---|
| transaction-cost economics | do platform-specific investments create hold-up or bilateral dependency? | `NEEDS_RESEARCH` |
| behavioral economics | does default design and friction make a nominal choice operationally inaccessible? | `NEEDS_RESEARCH` |
| Chicago/efficiency | does logistics integration reduce costs and improve quality with pass-through? | `NEEDS_RESEARCH` |
| post-Chicago foreclosure | can routing volume raise independent carriers’ costs or deny minimum efficient scale? | `NEEDS_RESEARCH` |
| ordoliberal/autonomy | does the rule impair commercial freedom or contestability even without quantified price harm? | `NEEDS_RESEARCH` |
| Neo-Brandeisian/platform conflict | does the platform’s dual role create structural incentive to prefer an affiliate? | `NEEDS_RESEARCH` |

## 10. Business and stakeholder translation

### Board

Treat the decision as a proof-and-process lesson, not a safe harbour. Approve a risk appetite for defaults, affiliated services and seller choice; require evidence that the design is proportionate.

### C-suite

Ask whether the business can explain, with data, why the default exists, who can exit it, how long exit takes and whether an affiliate receives preferential treatment.

### Product and operations

Build a logged, usable opt-out; use objective reason codes; preserve configuration and algorithm changes; test actual user friction rather than relying on policy text.

### Commercial and procurement

Use measurable carrier-selection criteria and document exceptions, affiliate conflicts and less restrictive alternatives.

### Finance

Quantify efficiency, pass-through, seller harm and downside scenarios. Keep transaction-level support rather than high-level estimates.

### Legal and compliance

Preserve notices, consent versions, tickets, audit logs, comparator treatment and decision rationale. Separate current-law penalty analysis from case commentary.

### SMEs and counterparties

Verify distances, dates, communications and loss before filing. Preserve native records and identify the exact policy, refusal and harm.

### Investors and lenders

Examine dependence on affiliated logistics, concentration, seller friction, unresolved regulatory theories and the cost of remedy or unbundling.

## 11. Traffic-light application

- **Green:** transparent default, real choice, objective criteria, timely exception process and complete audit trail.
- **Yellow:** justified default but manual/slow exception path, affiliate involvement or weak comparator data.
- **Red:** no usable alternative, retaliation for switching, hidden affiliate preference, inaccurate reasons or post-complaint records that cannot be reconstructed.

## 12. Evidence to preserve now

- policy and notice versions;
- consent and acknowledgement logs;
- UI and workflow telemetry;
- ticket and escalation records;
- algorithm/model/rule versions;
- carrier affiliation and selection criteria;
- SLA, cost and quality scorecards;
- GIS/source data and validation method;
- seller and consumer outcome metrics;
- financial harm and efficiency calculations;
- exception and cure records.
