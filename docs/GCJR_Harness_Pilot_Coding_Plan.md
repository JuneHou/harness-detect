# Coding plan: joint and alternative harness repair families

Implement a reproducible pilot that predicts **all inclusion-minimal successful harness repair sets**, using weighted combinations of historical, experimentally measured repair-response tables. Start with one AgentDefect program and two persistent repair candidates. Build the experiment and run the stages that the available environment and configured budget support. Do not report a successful scientific pilot from synthetic unit-test tables alone.

This is an implementation specification, not a report of completed experiments. Source artifacts have been inspected, but no AgentDefect program has yet been runtime-qualified for this study. The first milestone resolves that uncertainty.

## 1. Research target and source mechanism

**Research question:** When does a harness failure require coordinated repairs to multiple components, and when do distinct repairs provide alternative routes to recovery?

**Method hypothesis:** For incidents with comparable pre-repair evidence, complete measured repair-response tables can transfer across task contexts. Synthesizing those tables may recover joint and alternative repair relationships that singleton rankings or additive effect estimates miss.

| Specific paper | Operation already demonstrated or described | Operation used in this pilot |
| --- | --- | --- |
| GCJR / Minimal Repair Family Recovery [1] | Counterfactual replay recovers all inclusion-minimal successful event-repair sets within a declared domain. Its graph restriction covers selected cross-agent, incomparable event pairs with a downstream join. | Transfer the set-valued diagnostic target and replay-based verification to persistent harness edits. Do not import its graph pruning or exactness theorem into this different intervention domain. |
| SelfHeal [2] | Produces corrected agent programs; AgentDefect supplies buggy/fixed code and tests. | Use inspectable code as a starting point. A published patch is neither a minimal-family annotation nor proof that its individual edits are independently applicable. |
| HarnessCompass [3] | Evolves components and consolidates validated edits. | The proposed output is an explicit family of minimal successful combinations for an incident, including alternative repairs. This is a narrower comparison with its described procedure, not a claim that no harness paper studies interactions. |

The donor estimator is our proposed extension. It is **synthetic-control-inspired response transfer**, not a direct reproduction of classical synthetic control and not an implementation already provided by GCJR. Execution savings are secondary to correct family recovery.

This pilot does not use EDGE and does not require exhaustive annotation of multiple errors within each trace. It requires a reliable task-outcome oracle and controlled execution of repair combinations.

## 2. Fixed scope and terminology

- Use one selected AgentDefect program for the primary experiment, one declared baseline harness revision, one task-model configuration, and two repair candidates, A and B.
- Each candidate is a persistent code/configuration change applied before execution. It must operate across inputs without using an incident ID, hidden expected answer, or benchmark label.
- Repair the agent's harness: memory handling, tool interface, control flow, output handling, or another explicit implementation mechanism. Editing a benchmark task's target code or replacing one generated message is outside this pilot.
- An incident is a task input or complete conversation plus its initial environment/session state, executed under the declared baseline harness. Repetitions of that incident are not independent incidents.
- A and B have the same semantic meaning in all donor and target incidents. Do not match arbitrary patches from unrelated programs merely because both were named A.
- Record every configuration in the domain D = {empty, A, B, AB}. Do not assume that adding a repair preserves success.
- Candidate generation is frozen before calibration and test collection. The pilot evaluates family identification among supplied candidates; it does not claim to solve unrestricted patch generation.

For incident i and configuration S, estimate p_i(S) from a fixed number R of repetitions. Set h_i(S) = 1 when the empirical success rate is at least theta. The default theta is 0.8.

For a baseline that fails this threshold, define:

    F_i = { S in {A, B, AB} : h_i(S) = 1
            and h_i(T) = 0 for every strict subset T of S }

Minimal means inclusion-minimal, not minimum execution cost or minimum number of changed lines. Include the empty configuration in every minimality check.

| Empirical threshold outcomes: empty, A, B, AB | Family | Meaning within this candidate domain |
| --- | --- | --- |
| 0, 0, 0, 1 | {{A,B}} | A and B are jointly necessary for this available recovery route. |
| 0, 1, 1, 1 | {{A},{B}} | Either repair alone is sufficient. |
| 0, 1, 1, 0 | {{A},{B}} | Alternative singleton repairs exist, but their combination is harmful. |
| 0, 1, 0, either | {{A}} | A is the only minimal successful set. |
| 0, 0, 1, either | {{B}} | B is the only minimal successful set. |
| 0, 0, 0, 0 | {} | No successful repair in this domain. |
| 1, any, any, any | baseline_adequate | The failed diagnostic observation was not a persistent baseline failure under this repetition protocol. |

Do not call a repair globally necessary: another untested patch could recover the task. No claim concerns repair sets outside D.

## 3. Milestone 1: qualify the source program and candidates

### 3.1 Acquire and audit

Use https://github.com/Laboratory-software-Innovation/SelfHeal and pin its commit and AgentDefect.zip checksum. The archive inspected during planning had SHA-256:

    9063744afae7a2912abf0465d6624d0e266b70239a3c7dd1a4b087f012891e0a

It contained 37 fixed programs and tests but 36 run_buggy.py files. Recount the downloaded archive; do not assume all 37 are executable pairs. Retain the original files unchanged and record licenses and provenance.

Audit every available pair statically. Emit case_audit.csv with case ID, available files, defect description, changed mechanisms, dependency/runtime requirements, harness relevance, test strength, proposed candidates, and rejection reason. Use semantic changes rather than raw diff hunks to define candidate repairs.

These inspected cases are audit leads, not pre-approved experimental cases:

| Case | Observed source change or concern | Required check |
| --- | --- | --- |
| 79149108 | Published fix adds assistant-message history. The token-budget loop does not recompute its token count; the fixed code also mixes tuple and dictionary message formats. | Investigate whether there are independently repairable memory and budget mechanisms. Reproduce behavior before naming them faults. Existing nonempty-response/history-length tests are insufficient to establish conversation correctness. |
| 76364591 | Published fix adds return_direct=True to a calculator tool. | A clean single-repair example, but it does not establish a joint pair. Do not split this one setting into artificial candidates. |
| 76906469 | Changes agent type, memory representation, model configuration, and parsing-error handling. | Check whether proposed partial edits create valid agents. Constructor/API incompatibility is not evidence for the intended behavioral interaction. Freeze unrelated model changes. |

The original archive contains executable code, including dynamic evaluation in some tools. Run only controlled generated inputs inside the experiment environment; do not expose an endpoint or use real user accounts.

### 3.2 Select one program using development evidence only

Runtime-screen at most two promising programs after the static audit. For each, use at most eight development incidents, four configurations, and three repeats: at most 192 configuration executions across two programs, excluding clearly documented environment troubleshooting.

A qualified program must have:

1. A reproducible baseline behavior and a task oracle that checks the intended result rather than merely nonempty output.
2. A and B that both apply independently to the same baseline, with identical candidate definitions across inputs.
3. A combined AB version whose composition is understood. Record patch order; if order changes semantics, fix one order explicitly or reject the pair. Do not hide an extra fix inside AB.
4. A runnable, inspectable harness for every configuration. Reject a pair whose apparent joint effect is only that its singleton variants cannot construct the framework object.
5. Task/state variation capable of producing different repair responses. At least two family types must occur in development before attempting a transfer claim; constant families are a trivial prediction problem.

To evaluate the full joint-versus-alternative question, development must contain both a measured joint case and a measured alternative-singleton case. If only one occurs, explicitly mark the scientific scope as partial. Do not manufacture the missing class in labels.

Natural data is preferred. If it cannot supply a suitable case, a **controlled AgentDefect-derived variant** is permitted: retain the chosen program's real harness, define reusable implementation fault mutations, and measure their consequences by executing the program. Keep this as a separate experiment with clear provenance. For the primary donor experiment, freeze one resulting baseline revision and vary task inputs/initial states. Do not mix revisions with different repair meanings into one donor pool.

Fault-injection metadata, the intended family, or the known inverse mutation must never substitute for measured outcomes. Do not construct an oracle or simulator that returns success merely when named repair flags are enabled. If no valid, nontrivial case is obtained, complete the reusable offline pipeline and return data_blocked with the audit evidence. Do not substitute a different dataset silently.

### 3.3 Freeze the experimental contract

Before calibration/test runs, write experiment_manifest.json containing the source commit, selected case, provenance mode, environment lock, baseline hash, patch hashes, task generator, split manifest, oracle version, feature schema, model/version/settings, repetition policy, theta, and resource caps. Development incidents used to choose these settings remain outside the main evaluation.

Acceptance artifact: qualification.md must show actual development traces and four-cell outcome tables, not just source inspection. Include exclusions and partial-scope findings.

## 4. Milestone 2: build a trustworthy runner

Implement one adapter with these responsibilities:

    prepare(initial_state) -> isolated session/environment
    apply_repairs(baseline, repair_set) -> runnable harness artifact
    run(task, initial_state, repair_set, repeat_id) -> RunResult
    evaluate(task, initial_state, RunResult) -> OracleResult
    reset() -> verified clean initial state

Use the same task model, prompts except declared prompt repairs, tool environment, token limits, and task state across the four configurations. Apply repairs before the first affected event and keep them active for the full episode. Reset memory, files, database state, caches with side effects, and other mutable session state between configurations.

Pin the source dependencies first. If a model or dependency is unavailable, document the compatibility adaptation and apply it identically to every configuration; re-establish baseline behavior. Never change the model only for the fixed version.

Where supported, use common random seeds across configurations. A provider seed is not a guarantee of identical sampling. When unavailable, record that fact, balance/randomize configuration order within repeat blocks, and use independent repeated calls. Do not reuse an old model response after its prompt changes.

Use full episode execution for this pilot. Checkpoint continuation is optional future work; an incorrect continuation boundary can erase a repair's effect or preserve state produced by the wrong harness.

Outcome rules:

- success: the deterministic task oracle passes every declared requirement.
- task_failure: the runnable harness produces a wrong result, violates required state conditions, or hits the declared task limit.
- invalid_configuration: patch/application/constructor incompatibility; fail qualification rather than encoding it as a useful joint-repair example.
- infrastructure_error: unavailable service, unrelated provider outage, or failed setup; store separately and do not turn it into a task failure.

Use at most two infrastructure retries per scheduled run, without changing the task or patch. Preserve all attempts and costs. Genuine harness recovery defects must be distinguished from unrelated outages by the declared task/environment contract. Never rerun task failures until one succeeds.

Rewrite imported tests so every configuration passes through the same adapter and oracle. A test that imports run_fixed directly cannot evaluate A, B, or the baseline. Keep expected answers in evaluator-only data. For arithmetic, validate the numerical answer and task semantics; for conversational memory, test the actual referenced information and state behavior rather than length alone.

Unit-test isolation using a stateful fake backend, but label all fake runs as plumbing tests. They cannot satisfy qualification or scientific acceptance.

## 5. Milestone 3: collect response tables and prevent leakage

Default full pilot: **60 independent incident groups**, split before collecting repaired outcomes into 30 donor, 15 calibration, and 15 test groups. Start with one incident per group. Paraphrases and variants derived from the same underlying task/state template stay in the same group; extra variants do not increase the independent-group count.

This is a small pilot, not a powered claim of generalization. If the selected program cannot support these distinct groups, report the actual number and narrow the claim. Do not pad the dataset with renamed copies.

For every incident, acquire a standardized diagnostic baseline trace using a separate repeat ID. This is the only execution evidence available to the primary predictor for a target. Use one scheduled diagnostic attempt; retain successful attempts as controls rather than silently discarding them. Report which incidents have observed diagnostic failures.

Then collect all four configurations with **R=20 fixed repetitions** each. This is 60 × 4 × 20 = 4,800 reference executions, plus 60 diagnostic episodes and the separately reported development runs. Each episode can contain several model calls. Produce a resource estimate from the smoke runs before the full collection and enforce configured episode/model-call/token caps. If a cap prevents completion, mark cells incomplete; never impute missing runs as failures.

Use the full fixed reference table to define empirical families. Report binomial uncertainty separately. For a probability-supported label, use fixed-N exact binomial intervals with a Bonferroni allocation across the four cells at familywise alpha=0.05. A cell is supported-success only if its lower bound is at least theta, supported-failure only if its upper bound is below theta, and otherwise unresolved. A finite-protocol family is not automatically a population-probability certificate.

No adaptive stopping on reference success rates in this first implementation. Changing R after inspecting test results would change the target and uncertainty calculation.

Split and access rules:

- Group assignment uses pre-repair provenance only, with a fixed RNG seed. Do not balance or select test groups using their repair outcomes.
- Donor outcomes are available for fitting/tuning. Tune hyperparameters with grouped cross-validation inside donors only.
- Calibration outcomes are used for uncertainty calibration, not for candidate design or feature selection.
- Test repaired outcomes live in an evaluator-only store. Prediction code accepts no path to that store.
- The predictor sees target task observables and the diagnostic baseline trace. It cannot see test repair traces, final repair outcomes, reference-family labels, or hidden fault/injection IDs.
- If repeated baseline runs later show p(empty) >= theta, mark baseline_adequate. Report those cases separately; do not secretly remove difficult targets while reporting aggregate performance.

Archive all four donor cells, including AB even when a singleton succeeds. The complete response table is needed to study interaction and harm from combinations.

## 6. Data contracts

Use JSONL/Parquet for portable records and SQLite or a manifest-backed cache for resumable execution. All paths below are project-relative.

| Record | Required fields |
| --- | --- |
| Incident | incident_id, group_id, split, source_case_id, provenance_mode, task_payload, initial_state_hash, baseline_hash, oracle_version |
| Repair | repair_id, mechanism, target_paths, patch_hash, preconditions, composition_order, semantic_description |
| Run | run_id, incident_id, configuration, repeat_id, phase, model_config_hash, seed_supported, requested_seed, code_hash, state_hash, status, success_or_null, oracle_checks, trace_path, model_calls, tokens, latency, attempt_count |
| ResponseTable | incident_id, counts and rates for empty/A/B/AB, intervals, completeness, empirical_family, probability_supported_family_or_unresolved |
| PreRepairFeatures | incident_id, feature_schema_hash, numeric_vector, missingness_flags, provenance confirming diagnostic-only extraction |
| Prediction | incident_id, method, donor_ids, weights, four predicted rates, fit_residual, effective_donors, donor_disagreement, intervals, family, family_status, fallback_reason, queried_configurations, measured_certificates |

Allowed phases: development, diagnostic, reference, online_probe, unit_test. Distinguish a replay of an already collected reference result from a genuinely new execution.

Cache keys include task hash, initial-state hash, harness/patch hashes, model/settings, oracle version, repeat ID, and run phase. Resume only identical scheduled runs. Do not reuse donor data across incompatible repair manifests.

Produce an explicit features_allowlist.json. Start with a small, interpretable vector derived from information available before repair: task length/structure, conversation depth, observed request/response counts, tool-call counts, observed parser/API errors, token/context usage, memory-history counts, and public task requirements as applicable to the selected program. Fit scaling and imputation on donors only.

Exclude repaired outputs, gold answers, expected family, mutation-selector flags, source IDs used as predictive features, and metadata describing the injected fault. Visible baseline failure evidence is allowed; hidden evaluator conclusions are not.

## 7. Milestone 4: implement donor synthesis

For a target feature vector z_i and compatible donor vectors z_j, solve:

    minimize_w  || z_i - sum_j w_j z_j ||_2^2 + lambda ||w||_2^2
    subject to  w_j >= 0 and sum_j w_j = 1

Use a constrained numerical solver; log convergence and constraint residuals. Select lambda from {0, 0.01, 0.1, 1, 10} using grouped donor-only cross-validation on four-cell prediction error. This uses historical responses for hyperparameter selection, but target weights are fitted from target pre-repair features only.

Synthesize the **whole table with the same weight vector**:

    p_pred_i(S) = sum_j w_ij * p_measured_j(S),  S in D

In particular, AB uses measured donor AB outcomes. Do not estimate it by adding singleton effects. Do not fit four unrelated donor mixtures, since that can assemble a table that no coherent comparison supports.

Eligibility requires the same selected program/baseline domain, model configuration, repair semantics, oracle, and compatible environment protocol. Begin with this strict compatibility rule; cross-program/model transfer is outside scope.

Record matching residual, nearest-donor distance, effective donor count 1/sum(w^2), maximum weight, weighted variance of each response cell, and weighted donor-family distribution. A good baseline match does not establish response transferability.

**Mandatory failure-mode test:** donors with A-only family and B-only family can average into a false joint-family prediction. For example, averaging tables (0,1,0,1) and (0,0,1,1) gives (0,0.5,0.5,1), which predicts joint necessity at theta=0.8. The true target could instead be A-only. Include this as a unit test and a reported donor-disagreement diagnostic. Do not claim that simplex weighting preserves repair-family structure.

Use donor leave-one-group-out matching residuals to define a predeclared 95th-percentile overlap threshold. Residuals exceeding it cause abstention. Also report family disagreement rather than forcing a confident answer from incompatible response patterns. Tune any additional abstention rule only inside donor development folds and freeze it before calibration.

## 8. Uncertainty and selective execution

Keep zero-probe predictions as the primary method output. Actual target executions are a separate assisted variant, so a successful exhaustive fallback cannot conceal a weak donor model.

For calibration incident k, compute a simultaneous table residual:

    r_k = max over S in D of |p_measured_k(S) - p_pred_k(S)|

For multiple incidents in a calibration group, use the maximum residual within the group. For alpha=0.10, take the ceil((n_cal_groups+1)*(1-alpha))-th ordered group residual. If that rank exceeds the available count, the bound is uninformative; return [0,1] rather than claiming coverage. Form each cell's interval by clipping p_pred +/- the residual quantile to [0,1].

These intervals target the finite-reference rates used for calibration. They are not confidence intervals for the latent success probabilities. Any exchangeability claim is conditional on the group sampling protocol; report empirical test coverage, especially under distribution shifts.

Enumerate the at most 16 success/failure assignments consistent with the four intervals and theta. Convert every assignment to a family or baseline_adequate status. If more than one result is possible, mark family ambiguity. Do not require an AB decision when certified successful singletons already make AB non-minimal.

For the assisted variant, evaluate target query budgets of 0, 1, 2, and 4 configurations. A queried configuration receives the same fixed R-repeat protocol as the reference. For each unresolved configuration, count unordered pairs of currently feasible binary assignments that have different family outputs and disagree on that configuration. Query the configuration with the highest count; break ties by declared execution cost, then the fixed order empty, A, B, AB. Treat this as a simple diagnostic heuristic, not a calibrated probability model or a new optimal active-learning algorithm. A query costs one configuration block of R executions; the original diagnostic observation is an additional, separately counted episode.

After a query, replace that cell with its measured finite-protocol outcome. Keep the original donor weights and unqueried predictions fixed in this pilot. Count every query, repetition, and model call. Do not exploit unqueried reference cells when choosing the next probe.

Maintain these statuses:

- predicted: no complete execution certificate; may include a calibrated unambiguous prediction.
- partially_verified: some required cells measured, but family completeness/minimality still depends on predictions.
- protocol_verified: every cell needed to establish the complete family under the fixed repetition protocol has been measured.
- inconclusive: insufficient donor support, missing reference cells, or unresolved ambiguity at the budget limit.

For two candidates, a joint-family certificate requires measured failure of empty, A, and B, plus measured success of AB. Alternative-singleton certification requires measured failure of empty and success of A and B; AB is irrelevant to minimality. A claim that no available repair works requires all four cells. Statistical support for latent probabilities is a separate field.

First evaluate assisted policies against a sealed offline query service backed by the fully collected reference table. Call the resulting savings **simulated online execution savings**: the offline reference was still paid for. A later live pilot is needed to demonstrate actual deployment savings.

## 9. Baselines and ablations

All predictors use the same splits, candidate set, features, target information, and outcome definitions.

| Method | Purpose |
| --- | --- |
| Exhaustive execution of all four configurations | Finite-protocol reference and full response-table cost. |
| Execution with minimality pruning | Stronger execution comparator: test empty and both singletons; test AB only if both singletons fail. It may already avoid AB. This is GCJR-inspired minimality logic without its graph restriction. |
| Singleton-only replay | Tests whether pair outcomes are necessary. Must report joint cases as unresolved/missed, not silently assume additivity. |
| Uniform donor mean | Tests whether matching matters. |
| Nearest-donor transfer | Tests whether synthesizing several donors improves on retrieving one. |
| Additive response estimate | Use the main estimator's empty/A/B predictions, but set AB = clip(p(A)+p(B)-p(empty), 0, 1). Isolates the value of measured joint responses. |
| Multi-output ridge regression | A simple supervised response-transfer comparator with donor-only tuning. Helps test whether constrained donor synthesis adds value beyond generic prediction. |
| Main donor synthesis, with and without abstention/probes | Separates prediction quality, uncertainty handling, and execution-assisted recovery. |

Apply the same calibration and probe-budget protocol to eligible predictive baselines when comparing assisted results. Report any method-specific abstention rule. No model training beyond these small estimators is required.

## 10. Evaluation and interpretation

Primary outcomes, reported for observed diagnostic failures with empirically failing baselines:

1. Family exact match: predicted set of minimal repair sets equals the reference family exactly.
2. Macro family exact match over observed types: A-only, B-only, joint, alternative, and no-repair. State absent types rather than assigning them perfect scores.
3. Missed joint-family rate and false joint-family rate.
4. False necessity: a method claims A or B is necessary although a successful reference alternative excludes it. An unresolved method output is an abstention, not a negative causal claim.
5. Four-cell MAE and interaction-contrast error, using I = p(AB)-p(A)-p(B)+p(empty). This contrast is descriptive and does not itself define the minimal family.
6. Repair-selection success: select a predicted minimal set using a fixed smallest-cardinality, then fixed A-before-B tie-break rule. Freeze every method's selected repair before testing it with 10 fresh confirmation repeats per selected target/configuration. These outcomes are unavailable to matching, calibration, family extraction, and probe selection. Deduplicate identical selected configurations across methods when collecting confirmation runs. With 15 test incidents and at most three nonempty configurations each, this adds at most 450 episodes; list this separately from the 4,860 diagnostic/reference episodes. Also report repair size and unresolved selections. If confirmation cannot be completed, report reference-based recovery only and do not present it as independent execution verification.

Separately report probability-supported versus threshold-ambiguous reference cases, transient baseline failures, successful diagnostic controls, every exclusion, and incomplete runs. For selective methods, report coverage and accuracy together; also count abstentions as incorrect in an unconditional exact-match score. Provide denominators per family and split.

Use paired differences between methods and group-level bootstrap intervals where group counts permit; call the small sample exploratory. Do not use repeated seeds or paraphrases as independent bootstrap units. Include error analyses of at least one false joint prediction, one missed alternative if observed, and unsupported donor matches.

Efficiency reporting must separate:

- donor-history construction;
- calibration collection;
- diagnostic baseline observation;
- online probes;
- offline exhaustive reference collection;
- model/token cost per episode and amortized costs under explicitly stated reuse counts.

Scientific support requires nontrivial family diversity and held-out improvement over additive and retrieval baselines, especially on joint/alternative cases, without concealing errors through low coverage. A clear negative result is valid: if pre-repair evidence cannot distinguish incidents with different response families, explain that identifiability limitation. Do not expand scope or tune on test outcomes to obtain a positive result.

## 11. Implementation layout and command contract

Use a small Python project. These are commands the coding agent must implement, not commands that already exist in the source repository.

    repair_family_pilot/
      pyproject.toml
      README.md
      configs/pilot.yaml
      src/repair_family_pilot/
        cli.py
        audit.py
        adapters/base.py
        adapters/agentdefect.py
        repairs.py
        runner.py
        oracle.py
        records.py
        splits.py
        features.py
        families.py
        donors.py
        calibration.py
        probing.py
        baselines.py
        evaluation.py
      tests/
      artifacts/audit/
      artifacts/manifests/
      artifacts/traces/
      artifacts/public_inputs/
      artifacts/donor_tables/
      artifacts/calibration/
      artifacts/reference_private/
      artifacts/predictions/
      artifacts/reports/

Default configuration fields:

    candidate_count: 2
    configurations: [empty, A, B, AB]
    success_threshold: 0.8
    reference_repeats: 20
    confirmation_repeats: 10
    development_repeats: 3
    donor_groups: 30
    calibration_groups: 15
    test_groups: 15
    split_seed: 20261020
    calibration_alpha: 0.10
    familywise_binomial_alpha: 0.05
    lambda_grid: [0, 0.01, 0.1, 1, 10]
    query_budgets: [0, 1, 2, 4]
    max_infrastructure_retries: 2
    selected_case: null
    model_config: null
    resource_caps: null

The audit fills selected_case and the environment's actual model configuration. Estimate resource use from measured smoke runs, then resolve caps using the existing project budget. Never infer unlimited API spend. If no usable runtime/model access is available, complete offline implementation and clearly identify the blocked live stage; do not replace real experimental results with mocked outcomes.

Required CLI sequence:

    python -m repair_family_pilot audit --config configs/pilot.yaml
    python -m repair_family_pilot qualify --config configs/pilot.yaml
    python -m repair_family_pilot freeze --config configs/pilot.yaml
    python -m repair_family_pilot collect --split donor --config configs/pilot.yaml
    python -m repair_family_pilot collect --split calibration --config configs/pilot.yaml
    python -m repair_family_pilot fit --config configs/pilot.yaml
    python -m repair_family_pilot calibrate --config configs/pilot.yaml
    python -m repair_family_pilot collect --split test --config configs/pilot.yaml
    python -m repair_family_pilot predict --config configs/pilot.yaml
    python -m repair_family_pilot evaluate --config configs/pilot.yaml
    python -m repair_family_pilot report --config configs/pilot.yaml

All collecting commands support --dry-run and --resume. --dry-run shows scheduled configurations, repeats, expected model calls from smoke measurements, and caps without invoking the model. Only the evaluator/query service can read reference_private. Predictions must be frozen and hashed before evaluation.

## 12. Required validation and completion criteria

Implement meaningful tests for:

- Family extraction on all 16 binary four-cell tables, including baseline success and non-monotonicity.
- No test-outcome or mutation-label access by the predictor; shuffling sealed test outcomes cannot change frozen zero-probe predictions.
- Group splits keep related variants together and all target repair outcomes outside donors/calibration.
- The same donor weights are used for every configuration; simplex constraints and solver failures are handled.
- The mixed A-only/B-only donor example can produce a false joint prediction and is not silently labeled verified.
- Invalid patch compositions, state contamination, and infrastructure failures cannot become successful evidence for a joint mechanism.
- Repair-family certificate rules distinguish partial verification from complete finite-protocol verification.
- Resume/cache keys cannot mix harness revisions, seeds, states, or phases.

Deliver these artifacts:

1. Runnable project and dependency lock, with exact reproduction commands.
2. case_audit.csv and qualification.md, including the selected case or the concrete reason none qualified.
3. Frozen manifest, repair definitions/diffs, split manifest, oracle and feature specification.
4. Raw real-run traces and complete measured response tables, when live collection is possible.
5. Frozen predictions and a comparison table with exact-match, joint/alternative errors, coverage, uncertainty and costs.
6. A short final report stating: what was actually run; what is natural versus derived; whether family diversity exists; whether donors transfer; and what remains untested.

Completion statuses must distinguish implementation_complete, data_blocked, partial_scientific_scope, pilot_complete_negative, and pilot_complete_supported. Passing software tests alone establishes implementation_complete, not pilot_complete_supported.

The first useful scientific deliverable is the qualification table with a real four-configuration response pattern. If that fails, report it early while finishing reusable infrastructure. Do not spend the full collection budget on a program that cannot test the question.

## Sources and provenance

[1] Li et al. Localizing Emergent Failures in Agentic AI: Recovering Minimal Repair Families via Counterfactual Replay, v2. https://arxiv.org/html/2608.29228v2 — source for the minimal-family target, bounded replay and original graph-domain restrictions.

[2] Islam et al. SelfHeal: Empirical Fix Pattern Analysis and Bug Repair in LLM Agents. https://arxiv.org/html/2604.17699v1 — source for AgentDefect and SelfHeal. Released code: https://github.com/Laboratory-software-Innovation/SelfHeal — source for the inspected case observations.

[3] HarnessCompass: Guiding Automatic Harness Evolution toward Generalizable and Effective Agent Harnesses. https://arxiv.org/html/2608.01918v1 — comparator for component-wise evolution and consolidation.

All estimator choices, defaults, qualification gates, data splits, uncertainty rules and experiment sizes in this specification are proposed pilot decisions. They are not results or guarantees reported by those papers.
