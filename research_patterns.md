# Research-specific slide patterns

Use these as structures, not templates for inventing data. Bracketed fields are placeholders that must be replaced from verified sources or explicitly marked unavailable. A claim can be a question when findings do not yet exist.

## Biomedical experiment

**Title:** A factual finding within the tested model, not an unsupported clinical claim.

**Exhibit:** Design schematic (groups, dose, time points, assay) OR one primary result with individual biological observations when available. Distinguish biological replicates from technical replicates; identify experimental unit, n per group, units, controls and exclusions. Define error bars (SD, SEM, CI), test and multiple-testing correction when applicable. Do not manufacture error bars or turn technical replicates into independent biological samples. Avoid mechanistic/causal language from correlation alone.

**Interpretation:** Effect size and uncertainty; one limitation about model, assay or generalizability. Keep preclinical evidence distinct from clinical efficacy.

## ML or AI benchmark

**Title:** State the metric and held-out evaluation scope, e.g. “Model A improves [metric] on [external test set]”. Do not write “state of the art” without a fair, supported comparison.

**Exhibit:** One comparable metric with uncertainty across stated independent runs/folds, or one paired comparison. Include dataset/source/version, train/validation/test split, split unit (patient, scaffold, time, species), test size, leakage controls and baseline. Indicate higher/lower is better. For imbalanced classification, report prevalence and appropriate metrics; do not present accuracy alone as proof. Separate model selection from final test evaluation. Distinguish random-split and out-of-distribution performance.

**Interpretation:** Improvement magnitude, limitations and compute/cost if relevant. Put full hyperparameters and per-task scores in backup slides.

## Systems biology and simulation

**Title:** Identify the result as predicted or simulated unless experimentally validated.

**Exhibit:** Model inputs → constraints/assumptions → prediction → validation evidence. For GEM analyses include organism/model version, medium, objective, key bounds and method where they affect interpretation. Show units and flux conventions. Distinguish feasible flux, optimized flux and measured flux. Do not equate feasibility with biological truth; show sensitivity to assumptions or alternative optima where material.

## Structure, docking and molecule design

Label predictions separately from experimental structures or affinity measurements. Include method/version, receptor/ligand provenance and score units/conventions. Docking scores do not establish potency, selectivity or safety. Explain the validation step and uncertainty; do not label untested candidates as confirmed hits.

## Grant aims and milestones

One aim per slide: gap → hypothesis → approach → measurable deliverable → decision criterion → risk/alternative. Separate preliminary results from planned work. Tie timeline and resources to verifiable deliverables. Do not invent performance targets, cost quotes or partner commitments; user-provided aspirational targets remain labeled targets.

## Evidence ledger (planning artifact)

For each central claim, record: slide, exact source/page/figure, evidence type, population/model, key number+unit, uncertainty, caveat, and whether reconstruction is permitted. Verify citations and URLs; do not reuse the fictional examples in slide_patterns.md as actual research evidence. Keep private/unpublished data within the user's authorized audience.
