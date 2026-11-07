# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
#   language_info:
#     name: python
# ---

# %% [markdown]
# # What does loan narrative text add?
#
# **Post-competition research extension.** This maintained notebook reads a
# reviewed, full-data matched benchmark produced by the shared `src/` runner.
# It separates description, prediction and intervention. The primary August
# results and October explanatory sensitivity retain their own evidence status.
#
# The central question is whether narrative information improves forecasts on
# later **observed completed loans**, beyond structured loan context. This is
# not a funding-success model for all listings, a causal estimate of rewriting,
# or a fresh untouched test. Previous versions are preserved in Git history.

# %%
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython import get_ipython
from IPython.display import Markdown, display

if get_ipython() is not None:
    get_ipython().run_line_magic("matplotlib", "inline")

PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent
if not (PROJECT_ROOT / "src").is_dir():
    raise RuntimeError("Open this notebook from the repository root or notebooks directory")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark_data import feature_registry
from src.benchmark_models import default_config
from src.benchmark_reporting import load_bundle
from src.run_text_benchmark import run_benchmark

# Configuration: reviewed reports are the default; training is explicit.
RUN_MODE = "reviewed_report"
BUNDLE_DIR = Path(os.environ.get("KIVA_BENCHMARK_DIR", str(PROJECT_ROOT / "reports/text_benchmark_reviewed")))
DATA_PATH = PROJECT_ROOT / "data/Kiva_Loans.pkl"
FEATURE_CACHE = PROJECT_ROOT / "reports/text_benchmark_private/features.pkl"
SEED = 42
FIGURE_DIR = PROJECT_ROOT / "reports/text_benchmark_private/notebook_figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
np.random.seed(SEED)
pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", None)
plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
COLORS = plt.cm.viridis(np.linspace(.1,.85,5))

if RUN_MODE == "run":
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    BUNDLE_DIR = PROJECT_ROOT / "reports" / f"text_benchmark_{run_id}"
    run_benchmark(DATA_PATH, BUNDLE_DIR, default_config(), FEATURE_CACHE)
    bundle = load_bundle(BUNDLE_DIR, require_review=False)
    display(Markdown("**New execution is pending independent review. Do not publish these findings as accepted.**"))
elif RUN_MODE == "reviewed_report":
    bundle = load_bundle(BUNDLE_DIR)
else:
    raise ValueError("RUN_MODE must be reviewed_report or run")

benchmark, audit = bundle["benchmark"], bundle["audit"]
provenance = bundle["provenance"]
metrics = pd.DataFrame([dict(year=m["year"], family=m["family"], arm=m["arm"], **m["metrics"])
                        for m in benchmark["models"]])
paired = pd.DataFrame(benchmark["paired_comparisons"])
windows = pd.DataFrame(benchmark["windows"])

# %% [markdown]
# ## 0. Decision and evidence status
#
# **Observe:** The report loader verifies hashes, every configured window/arm,
# matching row identities and completed execution. In reviewed-report mode it
# also requires a bound review record; explicit run mode remains pending review.
# **Implication:** Results are traceable to one configuration and dataset.
# **Boundary:** Accepted retrospective evidence does not establish a writing
# intervention's benefit or restore a previously examined period as untouched.

# %%
display(pd.DataFrame({"item":["Input records","Eligible completed durations","Review status",
                                  "Model/arm windows","Report identity"],
                      "value":[audit["input_rows"],audit["eligible_rows"],
                               bundle["review"].get("status","pending"),len(metrics),
                               provenance["benchmark_sha256"][:16]]}))

# %% [markdown]
# ## 1. Outcome and availability audit
#
# A loan posted before a cutoff cannot enter training unless its completion was
# also observed before that cutoff. This applies to both targets because the
# cohort itself is selected on completed funding. A negative 24-hour label can
# mature while the loan's eventual inclusion remains unknown.

# %%
availability = pd.DataFrame(audit["windows"])
display(availability[["year","posting_only_train_rows","unavailable_completed_membership_rows",
                      "asof_train_rows","evaluation_rows","evaluation_posting_max"]])
display(pd.DataFrame({"diagnostic":["Invalid durations/dates","Duplicate ID rows",
                                      "Repeated nonblank descriptions","Missing descriptions"],
                      "rows":[audit["excluded_rows"],audit["duplicate_id_rows"],
                              audit["duplicate_description_rows"],audit["missing_description_rows"]]}))
excluded = availability.set_index("year")["unavailable_completed_membership_rows"]
ax = excluded.plot.bar(color=COLORS[2],figsize=(8,3.5))
ax.set(title="Completions unavailable at each training cutoff",ylabel="Excluded training records",xlabel="Evaluation year")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "availability.png")
plt.show()
display(Markdown(f"**Observe:** Between {int(excluded.min()):,} and {int(excluded.max()):,} pre-cutoff postings per window had not completed by training time. "
                 "**Implication:** Posting-date separation alone overstates the historically available training cohort. "
                 "**Boundary:** This audit does not isolate the resulting change in the old model's performance."))

# %% [markdown]
# ## 2. Validation contract
#
# Expanding training histories feed separate 2021–2025 posting-year evaluations.
# The data remain a completed-only snapshot: missing all-listing histories,
# extraction timing and historical text versions limit deployment claims.
# Windows show actual observed coverage, not an assumed complete calendar year.
# All transforms fit training rows only. Fixed budgets and disabled random
# early stopping avoid selecting candidates on the evaluated years.

# %%
display(windows[["year","train_rows","test_rows","training_max_completion","posting_min","posting_max"]])
display(pd.DataFrame({"setting":list(benchmark["configuration"]),
                      "value":[str(v) for v in benchmark["configuration"].values()]}))

# %% [markdown]
# ## 3. Baselines: what can simple context predict?
#
# B0 uses training median duration and training prevalence. B1 pools past
# country × sector × posting-month observations and shrinks them toward B0
# with 50 observations. It does not use current or future outcomes.

# %%
baseline = metrics[metrics.family.eq("baseline")]
display(baseline[["year","arm","rows","mae_days","brier","prevalence"]].round(5))
ax = baseline.pivot(index="year",columns="arm",values="mae_days").plot(marker="o",color=COLORS[:2],figsize=(8,3.5))
ax.set(title="Available baseline error across time",ylabel="MAE (days)",xlabel="Posting year",
       xticks=benchmark["configuration"]["years"])
plt.tight_layout()
plt.savefig(FIGURE_DIR / "baselines.png")
plt.show()

# %% [markdown]
# **Observe:** The table compares two forecasts using only available training
# information. **Implication:** A complex model must add useful information
# beyond these benchmarks. **Boundary:** Better prediction does not identify
# which intervention would help a loan fund faster.

# %% [markdown]
# ## 4. Feature registry and measurement
#
# S is structured listing context; M is description form/presence; L is
# transparent lexicon, specificity and sentiment measurement; R is a
# training-fitted TF-IDF representation; P is programme text as an unvalidated
# context proxy. T uses M+L+R without S. Neither country PPP nor cumulative
# country lending enters the new benchmark because its historical availability
# was not established. Text itself may have been edited after listing.

# %%
recorded_registry = provenance["feature_registry"]
display(pd.DataFrame([{"block":block,"features":", ".join(columns)}
                      for block,columns in recorded_registry.items()]))
if recorded_registry != feature_registry():
    display(Markdown("**Source definitions have changed since this run. The table above uses the run's recorded registry.**"))

# %% [markdown]
# ## 5. Matched model comparisons
#
# Compare arms within each model family and window. Sparse linear models can
# consume TF-IDF directly; the compact tree study includes structured and
# lexical blocks only. It does not establish the value of richer text for trees.
# Ridge and boosting predict log duration; exponentiating does not generally
# estimate mean days. MAE and R² measure different aspects, and R² can be negative.

# %%
display(metrics[["year","family","arm","rows","mae_days","median_ae_days",
                 "rmse_days","r2_days","roc_auc","average_precision","brier","log_loss"]].round(5))
fit_diagnostics = pd.DataFrame([{"year":m["year"],"family":m["family"],"arm":m["arm"],
                                 "fit_seconds":m["fit"].get("fit_seconds"),
                                 "classifier_iterations":m["fit"].get("classifier_iterations"),
                                 "warnings":"; ".join(m["fit"].get("warnings",[]))}
                                for m in benchmark["models"]])
display(fit_diagnostics)

# %% [markdown]
# ## 6. Incremental text value and uncertainty
#
# Positive gain means lower error after adding text. Each contrast uses the same
# evaluation records. Month and country resampling are separate sensitivities.
# They condition on the fitted models and omit retraining uncertainty; an annual
# window has few month blocks. Intervals are pointwise, without multiplicity
# adjustment. Compare practical size and stability, not only
# whether an interval crosses zero. No stakeholder minimum benefit is assumed.

# %%
main = paired[(paired.baseline.eq("S")) &
              ((paired.family.eq("linear") & paired.candidate.eq("S+M+L+R")) |
               (paired.family.eq("histogram_boosting") & paired.candidate.eq("S+M+L")))]
display(main[["year","family","metric","resampling_unit","gain","interval_95","clusters"]])
fig,axes=plt.subplots(1,2,figsize=(11,4))
for ax,metric,label in zip(axes,["mae_days","brier"],["MAE reduction (days)","Brier reduction"]):
    for i,family in enumerate(["linear","histogram_boosting"]):
        rows=main[(main.family.eq(family)) & main.metric.eq(metric) & main.resampling_unit.eq("calendar_month")].sort_values("year")
        x=rows.year.to_numpy()+(-.07 if i==0 else .07)
        ax.plot(x,rows.gain,"o-",label=family,color=COLORS[i+1])
        for xx,interval in zip(x,rows.interval_95):
            if interval is not None: ax.vlines(xx,interval[0],interval[1],color=COLORS[i+1])
    ax.axhline(0,color="grey",linewidth=1)
    ax.set(xlabel="Posting year",ylabel=label,xticks=benchmark["configuration"]["years"])
axes[0].legend(fontsize=8)
fig.suptitle("Added text: matched gains with month-block sensitivity intervals")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "incremental_text.png")
plt.show()

# %% [markdown]
# Programme-adjusted comparisons ask whether text adds information beyond S+P.
# They do not prove that partner effects or confounding have been removed.

# %%
display(paired[paired.baseline.eq("S+P") & paired.resampling_unit.eq("calendar_month")]
        [["year","family","metric","gain","interval_95"]])

# %% [markdown]
# ## 7. Probability quality and duration tails
#
# AUC measures ranking; Brier combines more than calibration. Reliability bins
# show predicted versus observed completion within 24 hours, along with counts.
# These probabilities apply only to this completed-record population. Duration
# slices below are evaluation diagnostics, never predictor inputs.

# %%
latest=max(benchmark["configuration"]["years"])
selected=[m for m in benchmark["models"] if m["year"]==latest and
          ((m["family"]=="linear" and m["arm"] in ["S","S+M+L+R"]) or
           (m["family"]=="histogram_boosting" and m["arm"] in ["S","S+M+L"]))]
fig,ax=plt.subplots(figsize=(6.5,4.5))
for i,m in enumerate(selected):
    bins=pd.DataFrame(m["calibration"])
    observed=bins[bins["count"]>0]
    ax.plot(observed.mean_probability,observed.observed_rate,"o-",color=COLORS[i],label=f'{m["family"]} {m["arm"]}')
ax.plot([0,1],[0,1],"--",color="grey",linewidth=1)
ax.set(xlabel="Mean predicted probability",ylabel="Observed 24-hour completion rate",title=f"Reliability in the {latest} observed cohort")
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(FIGURE_DIR / "calibration.png")
plt.show()
display(pd.DataFrame([dict(family=m["family"],arm=m["arm"],**b) for m in selected for b in m["calibration"]]))
display(pd.DataFrame([dict(family=m["family"],arm=m["arm"],**s) for m in selected for s in m["slices"] if s["dimension"]=="duration_band"]))

# %% [markdown]
# **Observe:** The reliability plot and tail table expose errors hidden by an
# aggregate score. **Implication:** Ranking quality alone does not justify an
# operational queue. **Boundary:** We did not fit or claim a separate calibrated
# deployment model; any calibration needs its own earlier temporal data.

# %% [markdown]
# ## 8. Stability, missing text and new contexts
#
# Group diagnostics include row counts and suppress small slices. Exact and
# digit-normalised description signatures provide limited novelty checks;
# semantic similarity and verified partner transfer require further work.
# A subgroup error difference is not permission to deprioritise its borrowers.

# %%
slices=pd.DataFrame([dict(year=m["year"],family=m["family"],arm=m["arm"],**s)
                     for m in benchmark["models"] for s in m["slices"]])
display(slices[(slices.year.eq(latest)) & (slices.family.eq("linear")) &
               slices.arm.isin(["S","S+M+L+R"]) &
               slices.dimension.isin(["description_missing","template_signature_novelty","country_iso_novelty","status"])])
country=slices[(slices.year.eq(latest)) & slices.family.eq("linear") &
               slices.arm.isin(["S","S+M+L+R"]) & slices.dimension.eq("country") & ~slices.suppressed]
if not country.empty:
    largest=country[country.arm.eq("S")].nlargest(10,"rows")["group"]
    chart=country[country.group.isin(largest)].pivot(index="group",columns="arm",values="mae_days")
    ax=chart.plot.barh(color=COLORS[1:3],figsize=(8,4.5))
    ax.set(xlabel="MAE (days)",ylabel="Country",title=f"Error in ten largest observed country groups ({latest})")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "country_errors.png")
    plt.show()

# %% [markdown]
# ## 9. Text construct validity: an open requirement
#
# Lexicon counts, VADER and TF-IDF are measurements, not validated psychological
# constructs. The next measurement study needs a codebook, independent dual
# coding, disagreement analysis and uncertainty by construct/context. Develop
# measures on development-period texts; freeze them before later-period audits.
# No human annotation agreement or causal mechanism is claimed by this notebook.

# %% [markdown]
# ## 10. Explanatory evidence remains separate
#
# The primary `reports/generated_full_dataset/` snapshot and reviewed October
# `reports/expanded_feature_sensitivity_reviewed/` extension estimate different
# explanatory specifications. The new predictive contrasts do not validate their
# coefficients, replace country-clustered inference, or prove a universal null.
# See `docs/2_evidence_and_corrections.md` for effect units and sparse-cluster
# limitations. SHAP, if added later, would describe model use rather than the
# effect of rewriting a narrative.

# %% [markdown]
# ## 11. Decision and next test

# %%
for family in ["linear","histogram_boosting"]:
    rows=main[main.family.eq(family) & main.metric.eq("mae_days") & main.resampling_unit.eq("calendar_month")]
    if len(rows):
        display(Markdown(f"**{family}:** adding the tested text block reduced MAE in {int((rows.gain>0).sum())} of {len(rows)} windows; "
                         f"the median window gain was {rows.gain.median():.3f} days (range {rows.gain.min():.3f} to {rows.gain.max():.3f}). "
                         "This measures additional predictive information, not time saved by editing."))
latest_linear=metrics[metrics.year.eq(latest) & metrics.family.eq("linear")].set_index("arm")
if {"S","S+M+L+R"}.issubset(latest_linear.index):
    base,added=latest_linear.loc["S"],latest_linear.loc["S+M+L+R"]
    display(Markdown(f"**Metric trade-off ({latest}, sparse linear):** MAE {base.mae_days:.3f} → {added.mae_days:.3f} days; "
                     f"AUC {base.roc_auc:.4f} → {added.roc_auc:.4f}; Brier {base.brier:.4f} → {added.brier:.4f}. "
                     f"The text-added day-space R² is {added.r2_days:.3f}. "
                     "An improvement in one loss does not establish improvement in ranking or tail error."))
display(Markdown("**Next decision:** review the size and temporal stability of the matched gains, text validity and data availability. "
                 "A factual clarity pilot would require an agreed intervention, all eligible listings, an observation horizon, power and guardrails. "
                 "An all-listing model needs unsuccessful/censored histories before survival analysis or live prioritisation."))

# %% [markdown]
# ## 12. Reproduction and limitations
#
# The report stores data/source/resource hashes, exact configuration, row
# identity hashes, timing, environment, warnings and a source archive. Private
# prediction files permit recomputation without publishing borrower records.
# This notebook executes its report/plot workflow; it does not silently retrain
# the models in default mode. Its committed source pair remains output-free.

# %%
display(pd.DataFrame(list(provenance["versions"].items()),columns=["dependency","version"]))
display(pd.DataFrame({"item":["Dataset","Data SHA-256","Source revision","Dirty tree at run",
                                  "Runtime seconds","Peak process memory MiB","Recorded model warnings"],
                      "value":[provenance["data_and_feature_identity"]["data_filename"],
                               provenance["data_and_feature_identity"]["data_sha256"],
                               provenance["git_revision"],provenance["git_tree_dirty"],
                               benchmark["runtime_seconds"],benchmark["peak_process_memory_mib"],
                               benchmark["model_warning_count"]]}))
display(Markdown("Completed-record selection, snapshot text availability, repeated holdout examination, correlated contexts, "
                 "unvalidated constructs and unmeasured intervention effects remain limitations after these comparisons."))
