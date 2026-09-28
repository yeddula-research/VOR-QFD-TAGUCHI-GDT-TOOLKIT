# Methodology

This document describes how the toolkit implements each phase of the
framework in the paper's Figure 1 — Voice of Regulation (VoR) extraction,
QFD House of Quality prioritization, Taguchi robust design, and GD&T scheme
formulation with traceability — and records every implementation choice
made where the paper does not fix a detail.

| Phase | Paper section | Module |
|---|---|---|
| 1 — VoR extraction | Phase 1, Eq. (1) | `vor_gdt.vor` |
| 2 — House of Quality | Phase 2, Eq. (2) | `vor_gdt.hoq` |
| 3 — Taguchi robust design | Phase 3, Eq. (3) | `vor_gdt.orthogonal_arrays`, `vor_gdt.taguchi`, `vor_gdt.robust_design` |
| 4 — GD&T scheme and traceability | Phase 4 | `vor_gdt.gdt`, `vor_gdt.traceability` |

## Phase 1 — Voice of Regulation extraction

**Input.** A P&ID parameter register: one row per item with `item_id`,
`pid_tag`, `parameter`, `value`, `units`, `source`, `severity` (S_i) and
`compliance_criticality` (C_i). In practice this corresponds to an export of
the equipment, line, instrument and interlock data behind a P&ID.

**Extraction rule.** An item is a VoR (critical-to-quality) parameter when its
source is one of the regulatory sources named in the paper: ASME Section VIII,
OSHA PSM requirements, or the project process datasheet
(`config.REGULATORY_SOURCES`). Items driven only by owner preference or a
general specification are not carried forward. The extracted parameters are
classified by source (`summarize_by_source`).

**Eq. (1) — regulatory criticality weight.**

    W_r = Σ_{i=1..n} (S_i · C_i) / Σ_{i=1..n} C_i

S_i is the severity rating of the i-th parameter on a 1–9 scale and C_i its
compliance criticality index; n is the number of extracted VoR parameters.

*Implementation choices.*

* The paper does not fix a numeric scale for C_i. The toolkit uses 1–5:
  5 = mandatory code or regulatory requirement, 4 = code-referenced
  requirement, 3 = project specification requirement, 2 = recommended
  practice, 1 = advisory (`config.COMPLIANCE_CRITICALITY_SCALE`).
* Eq. (1) yields one aggregate weight, whereas Eq. (2) uses a weight
  W_r,i for each VoR parameter. The toolkit uses each parameter's own term of
  the Eq. (1) sum, W_r,i = S_i · C_i / Σ C, so that Σ_i W_r,i = W_r exactly
  (`parameter_weights`).

## Phase 2 — House of Quality

Rows are the weighted VoR parameters; columns are engineering characteristics
(ECs): shell wall thickness tolerance, nozzle bore positional tolerance,
flange face flatness, surface roughness (Ra), shell out-of-roundness, and weld
joint perpendicularity. The relationship matrix holds scores
R_ij ∈ {0, 1, 3, 9} (none, weak, moderate, strong).

**Eq. (2) — absolute importance of each EC.**

    AIC_j = Σ_{i=1..m} W_r,i · R_ij

`HouseOfQuality.ranking()` reports, for each EC, the VoR parameters with a
strong (9) relationship, the unweighted relationship sum Σ_i R_ij, the
weighted AIC, its share of the total AIC, and the priority rank.

**Selection.** The `config.TOP_K_FOR_OPTIMIZATION = 3` highest-AIC ECs are
carried into Taguchi optimization, matching the paper's case study, which
optimized its three highest-priority characteristics. The remaining ECs are
still specified in the GD&T scheme, at default tolerances, but are not
optimized.

**Roof.** Technical correlations between ECs (+2 … −2) are recorded in
`config.HOQ_ROOF`; `HouseOfQuality.conflicts()` lists the negative pairs
(for example, tight positional tolerance versus surface finish) that must be
reconciled during optimization.

## Phase 3 — Taguchi robust design

**Inner array.** Each selected EC contributes one control factor — its
tolerance — at three levels. `select_inner_array` chooses L9 for up to four
three-level factors and L18 for five to seven, following the paper's
"L9 or L18 depending on the number of control factors and their levels".
With three factors, L9 columns 1–3 are used and column 4 is left for error.
All arrays in `vor_gdt.orthogonal_arrays` are checked for orthogonality in
the tests.

**Outer array (noise).** The four noise factors named in the paper — thermal
expansion variability, internal pressure fluctuation, weld distortion, and
material property scatter — are each set at two coded levels (−1, +1) in an
L8 outer array (columns 1, 2, 4 and 7). Each inner run is measured under all
eight noise conditions with three replicates (24 observations per run).

**Eq. (3) — S/N ratio, nominal-the-best.**

    η = 10 · log10( ȳ² / s² )

ȳ is the mean response of one run across its noise conditions and s² its
variance (sample variance, ddof = 1). The paper's printed Eq. (3) shows the
numerator as "y⁻²"; its Figure 1 gives ȳ² / s², the standard
nominal-the-best form, which is what `sn_nominal_the_best` implements.

The paper notes that nominal-the-best applies to the majority of GD&T
tolerance characteristics. For characteristics whose ideal value is zero
rather than a nominal target, the toolkit uses the standard
smaller-the-better form, η = −10 · log10(mean(y²)); a larger-the-better form,
η = −10 · log10(mean(1/y²)), is also provided. In the demonstration
configuration:

| Characteristic | Response | S/N form |
|---|---|---|
| Shell wall thickness tolerance | As-built shell wall thickness (mm), nominal 16.0 mm | Nominal-the-best (Eq. 3) |
| Nozzle bore positional tolerance | Radial position error of the nozzle bore axis (mm) | Smaller-the-better |
| Flange face flatness | Measured flange face flatness deviation (mm) | Smaller-the-better |

**Main effects and optimum.** For each characteristic, the mean S/N at each
level of each factor is computed (`main_effects`). The optimal level of each
control factor is the level with the highest mean S/N for that factor's own
characteristic. The S/N at the optimum is predicted with the additive model
η̂ = η̄ + Σ_f (η̄_f,opt − η̄), and a confirmation run is simulated at the
optimum with a fresh seed so that prediction and observation can be compared.
The additive prediction and the confirmation run are standard Taguchi steps
added by the toolkit; the paper does not describe them.

**ANOVA.** For each characteristic's S/N, the sum of squares of factor f is
SS_f = Σ_levels n_l (η̄_l − η̄)², with SS_error = SS_total − Σ SS_f
(unassigned L9 column plus residual). The table reports degrees of freedom,
mean squares, F, p-value, and percentage contribution SS_f / SS_total × 100.

### Demonstration simulation model

The demonstration measurements are generated by an illustrative model whose
coefficients are demonstration assumptions, not measured values
(`config.SIMULATION`). With z ~ N(0, 1) independent draws, n_k ∈ {−1, +1}
the noise-factor levels, t the tolerance at the run's level, and ℓ a coded
level index (0, 1, 2):

* **Wall thickness:** y = 16.0 + (t/3)·z + 0.01·n_thermal + 0.03·n_weld +
  0.06·n_material + 0.02·z′.
* **Nozzle bore position:** Δx = (t/3)·z₁ + 0.05·n_thermal + 0.03·n_weld +
  0.01·z₃; Δy = (t/3)·z₂ + 0.04·n_pressure·(1 + 0.25·ℓ_wall) + 0.01·z₄;
  y = √(Δx² + Δy²). The ℓ_wall coupling lets a looser wall-thickness tolerance
  amplify pressure-induced displacement.
* **Flange face flatness:** y = max(10⁻⁴, 0.5·t + (t/6)·z +
  0.015·(1 + 0.5·ℓ_flat)·(n_weld + 1)/2 + 0.004·n_thermal +
  0.004·n_material + 0.003·z′). Weld distortion shows through more when the
  flatness tolerance is looser.

The tolerance-driven process spread (t/3 or t/6) encodes the assumption that
a tighter specified tolerance is met by a more capable process. The S/N
criterion therefore favours the tightest levels; tolerance cost is not part
of the framework described in the paper and is not modelled here.

## Phase 4 — GD&T scheme and traceability

Each EC is mapped to a control per ASME Y14.5-2018 (`config.GDT_MAPPING`):

| Characteristic | Control | Datums | Tolerance |
|---|---|---|---|
| Shell wall thickness tolerance | Size (± tolerance) | — | Taguchi optimum |
| Nozzle bore positional tolerance | Position ⌖, cylindrical zone ⌀ | A \| B \| C | Taguchi optimum |
| Flange face flatness | Flatness ⏥ (form) | — | Taguchi optimum |
| Shell out-of-roundness | Circularity ○ (form) | — | Default (not optimized) |
| Weld joint perpendicularity | Perpendicularity ⟂ (orientation) | A | Default (not optimized) |
| Surface roughness (Ra) | Surface texture, symbol per ASME Y14.36 | — | Default (not optimized) |

Datums: A = shell axis, B = reference tangent line, C = 0° orientation line.
`FeatureControlFrame` enforces datum rules by category: form controls cannot
reference datums; orientation, location and runout controls require them;
profile controls may use them.

*Implementation choices.*

* A radial position allowance of ±r is converted to a cylindrical position
  zone of diameter 2r (`position_zone_diameter`).
* The paper lists true position and concentricity as examples of location
  controls. ASME Y14.5-2018 no longer includes the concentricity and symmetry
  characteristics, so the toolkit maps location requirements to position and
  rejects concentricity and symmetry callouts.
* Characteristics that are not optimized take the demonstration default
  tolerances in `config.GDT_MAPPING`.

**Traceability.** `build_traceability_matrix` links every callout to the VoR
parameters with R_ij ≥ 3 for its EC, and records each parameter's P&ID tag and
regulatory source. `coverage` checks both directions: every VoR parameter
reaches at least one callout, and every callout traces to at least one VoR
parameter; anything untraced is listed.

## What the toolkit does not compute

The paper also reports rework rates and dimensional non-conformance before and
after applying the framework (its Figure 4) and a benchmark against
conventional and QFD-based design methods (its Table 3). Those are outcomes of
the paper's case study, which cannot be derived from the method itself, so
the toolkit does not compute them. Table 3 is written to
`results/tables/table3_benchmarking_as_reported.*` from the paper for
reference.

## Published values

`vor_gdt.published` records the paper's Tables 1–3 exactly as printed, and
`scripts/07_published_values.py` writes them to `results/tables/*_as_reported.*`.
Nothing in the demonstration pipeline is fitted to these values. The script
also:

* plots the paper's Figure 2 from the S/N values in its Table 2, and its
  Figure 5 (radar chart) from the AIC values in its Table 1;
* checks that the three factor columns of Table 2 are columns 1–3 of the
  standard L9 array, and that Table 1's priority ranks follow its AIC order;
* computes the main effects of the published Table 2 S/N values, each factor
  on its own characteristic, and confirms that the best level of each factor
  is the optimum Table 2 reports (±0.5 mm wall, ±0.3 mm bore, 0.05 mm
  flatness).

The paper's Figures 3 and 4 are not included: apart from the values quoted
in the text, their data are given graphically.

## Dataset

The demonstration dataset is simulated: a fictional P&ID parameter register, House of Quality relationship matrix, and seeded Monte Carlo measurements for a fictional pressure vessel (V-101), generated by scripts/01_generate_dataset.py; it is not the case-study data reported in the paper.

The paper's case study concerns a high-pressure carbon steel pressure vessel
and related piping system under ASME Section VIII Division 1 requirements,
from which 11 VoR parameters were derived from the governing P&ID. The
demonstration register mirrors that structure (11 VoR parameters, six
engineering characteristics, three optimized with an L9 array); its values,
relationships, and measurements are the toolkit's own. The random seed is
`config.RANDOM_SEED = 42`.
