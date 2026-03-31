"""
Confidence-Interval Visualizations for Population-Weighted Averages

Produces
--------
  figures/ci_all_groups/
      all_groups_obes_vs_le_ci_<YEAR>.png   (×4, one per GDP-grouping year)

  figures/median_all_groups/
      all_groups_obes_vs_le_median_<YEAR>.png  (×4, medians only, no error bars)

  figures/ci_country_scatter/
      Israel.png, Argentina.png

  figures/ci_tables/
      ci_table_<YEAR>.csv                   (×4, includes Q1/median/Q3 columns)

CI methodology (analytic / reliability weights)
-----------------------------------------------
  V1     = Σ wᵢ
  V2     = Σ wᵢ²
  x̄_w   = Σ(wᵢ·xᵢ) / V1
  s²     = V1 / (V1² − V2) · Σ wᵢ(xᵢ − x̄_w)²     (Bessel-corrected)
  Var(x̄) = s² · V2 / V1²
  SE     = √Var(x̄)
  CI     = x̄_w ± t(n−1, 0.975) · SE
"""

import os
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from visualize_all_countries import (
    download_data,
    load_gdp,
    load_life_exp,
    load_population,
    load_obesity,
    align_datasets,
    YEARS,
    GROUP_NAMES,
    safe_filename,
    OUTPUT_DIR,
)

warnings.filterwarnings("ignore")

GROUPING_YEARS = ["1990", "1997", "2005", "2013"]
INDIVIDUAL_COUNTRIES = ["Israel", "Argentina"]


# ---------------------------------------------------------------------------
# GDP quintile labeling for an arbitrary year
# ---------------------------------------------------------------------------
def assign_gdp_labels_for_year(gdp: pd.DataFrame, year: str):
    """Return (labels_array, quantile_boundaries) based on *year*."""
    quantiles = gdp[year].quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]).tolist()
    bins = list(quantiles)
    bins[-1] += 1
    labels = pd.cut(
        gdp[year], bins=bins, labels=[0, 1, 2, 3, 4], include_lowest=True,
    )
    return labels.astype(int).values, quantiles


# ---------------------------------------------------------------------------
# Weighted mean + 95 % confidence interval
# ---------------------------------------------------------------------------
def weighted_mean_ci(values, weights, confidence=0.95):
    """
    Population-weighted mean and its CI (analytic-weights formulation).
    Returns (mean, ci_lower, ci_upper).
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)

    mask = ~(np.isnan(v) | np.isnan(w) | (w <= 0))
    v, w = v[mask], w[mask]
    n = len(v)

    if n == 0:
        return np.nan, np.nan, np.nan
    if n == 1:
        return float(v[0]), float(v[0]), float(v[0])

    V1 = w.sum()
    V2 = (w ** 2).sum()
    x_bar = (w * v).sum() / V1

    s2 = (V1 / (V1 ** 2 - V2)) * (w * (v - x_bar) ** 2).sum()
    var_xbar = s2 * V2 / V1 ** 2
    se = np.sqrt(var_xbar)

    t_crit = stats.t.ppf(1 - (1 - confidence) / 2, df=n - 1)
    return float(x_bar), float(x_bar - t_crit * se), float(x_bar + t_crit * se)


# ---------------------------------------------------------------------------
# Compute group statistics (mean + CI) for every group × year
# ---------------------------------------------------------------------------
def compute_group_stats(metric_df, pop_df, labels):
    """DataFrame with columns: group, year, mean, ci_lower, ci_upper."""
    rows = []
    for grp in range(5):
        mask = labels == grp
        for y in YEARS:
            vals = metric_df.loc[mask, y].values.astype(float)
            pops = pop_df.loc[mask, y].values.astype(float)
            m, lo, hi = weighted_mean_ci(vals, pops)
            rows.append({"group": grp, "year": int(y),
                         "mean": m, "ci_lower": lo, "ci_upper": hi})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Unweighted quartiles (Q1, median, Q3) for every group × year
# ---------------------------------------------------------------------------
def compute_group_quartiles(metric_df, labels):
    """DataFrame with columns: group, year, q1, median, q3 (unweighted)."""
    rows = []
    for grp in range(5):
        mask = labels == grp
        for y in YEARS:
            vals = metric_df.loc[mask, y].dropna().values.astype(float)
            if len(vals) == 0:
                q1 = med = q3 = np.nan
            else:
                q1, med, q3 = np.percentile(vals, [25, 50, 75])
            rows.append({"group": grp, "year": int(y),
                         "q1": q1, "median": med, "q3": q3})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figure: all 5 GDP groups on one chart, with vertical CI bars for LE
# ---------------------------------------------------------------------------
def plot_all_groups_with_ci(life_exp_df, obesity_df, pop_df,
                            grouping_year, labels, quantiles):
    le_stats = compute_group_stats(life_exp_df, pop_df, labels)
    ob_stats = compute_group_stats(obesity_df, pop_df, labels)

    intervals = [
        (int(round(quantiles[i])), int(round(quantiles[i + 1])))
        for i in range(5)
    ]

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    fig, ax = plt.subplots(figsize=(12, 8))

    for grp in range(5):
        le_g = le_stats[le_stats["group"] == grp].sort_values("year")
        ob_g = ob_stats[ob_stats["group"] == grp].sort_values("year")

        x = ob_g["mean"].values
        y = le_g["mean"].values
        y_lo = le_g["ci_lower"].values
        y_hi = le_g["ci_upper"].values

        lo, hi = intervals[grp]
        label = f"Group {grp + 1}. GDP Interval ({lo} - {hi})"
        c = colors[grp]

        ax.errorbar(
            x, y,
            yerr=[y - y_lo, y_hi - y],
            fmt="o", markersize=4, color=c,
            ecolor=c, elinewidth=0.9, capsize=2.5, capthick=0.9,
            alpha=0.85, label=label,
        )

    ax.set_title(
        "Dependency between life expectancy and obesity\n"
        f"(GDP grouping year: {grouping_year})",
        fontsize=18,
    )
    ax.set_xlabel("Obesity", fontsize=14)
    ax.set_ylabel("Life expectancy", fontsize=14)
    ax.legend(loc="lower left", fontsize=10, framealpha=0.9)
    ax.grid(False)
    fig.tight_layout()

    out_dir = os.path.join(OUTPUT_DIR, "ci_all_groups")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"all_groups_obes_vs_le_ci_{grouping_year}.png")
    fig.savefig(path, dpi=200)
    plt.close("all")
    print(f"  Saved: {path}")

    return le_stats, ob_stats


# ---------------------------------------------------------------------------
# Figure: all 5 GDP groups – unweighted MEDIANS only (no error bars)
# ---------------------------------------------------------------------------
def plot_all_groups_median(life_exp_df, obesity_df,
                           grouping_year, labels, quantiles):
    le_quart = compute_group_quartiles(life_exp_df, labels)
    ob_quart = compute_group_quartiles(obesity_df, labels)

    intervals = [
        (int(round(quantiles[i])), int(round(quantiles[i + 1])))
        for i in range(5)
    ]

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    fig, ax = plt.subplots(figsize=(12, 8))

    for grp in range(5):
        le_g = le_quart[le_quart["group"] == grp].sort_values("year")
        ob_g = ob_quart[ob_quart["group"] == grp].sort_values("year")

        x = ob_g["median"].values
        y = le_g["median"].values

        lo, hi = intervals[grp]
        label = f"Group {grp + 1}. GDP Interval ({lo} - {hi})"
        c = colors[grp]

        ax.scatter(x, y, s=30, color=c, label=label, alpha=0.85)

    ax.set_title(
        "Dependency between life expectancy and obesity (medians)\n"
        f"(GDP grouping year: {grouping_year})",
        fontsize=18,
    )
    ax.set_xlabel("Obesity (median)", fontsize=14)
    ax.set_ylabel("Life expectancy (median)", fontsize=14)
    ax.set_ylim(45, 85)
    ax.legend(loc="lower left", fontsize=10, framealpha=0.9)
    ax.grid(False)
    fig.tight_layout()

    out_dir = os.path.join(OUTPUT_DIR, "median_all_groups")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir,
                        f"all_groups_obes_vs_le_median_{grouping_year}.png")
    fig.savefig(path, dpi=200)
    plt.close("all")
    print(f"  Saved: {path}")

    return le_quart, ob_quart


# ---------------------------------------------------------------------------
# Figure: single-country scatter (Israel / Argentina)
# ---------------------------------------------------------------------------
def plot_country_scatter(life_exp_df, obesity_df, country):
    idx = life_exp_df.index[life_exp_df["Country Name"] == country]
    if len(idx) == 0:
        print(f"  WARNING: '{country}' not found in data")
        return
    i = idx[0]

    obes = obesity_df.loc[i, YEARS].values.astype(float)
    le = life_exp_df.loc[i, YEARS].values.astype(float)
    ylabels = [y[2:] for y in YEARS]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(obes, le, s=35, color="#4878a8", alpha=0.85, zorder=5)

    for ov, lv, yl in zip(obes, le, ylabels):
        ax.annotate(
            yl, (ov, lv),
            fontsize=9,
            ha="center", va="top",
            xytext=(0, -6), textcoords="offset points",
        )

    ax.set_title(
        f"Dependency between Life Expectancy and Obesity in {country}",
        fontsize=15, weight="bold",
    )
    ax.set_xlabel("Obesity", fontsize=13)
    ax.set_ylabel("Life expectancy", fontsize=13)
    ax.set_ylim(65, 85)
    ax.grid(False)
    fig.tight_layout()

    out_dir = os.path.join(OUTPUT_DIR, "ci_country_scatter")
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{safe_filename(country)}.png"
    fig.savefig(os.path.join(out_dir, fname), dpi=150)
    plt.close("all")
    print(f"  Saved: ci_country_scatter/{fname}")


# ---------------------------------------------------------------------------
# CSV tables
# ---------------------------------------------------------------------------
def save_ci_tables(all_tables):
    out_dir = os.path.join(OUTPUT_DIR, "ci_tables")
    os.makedirs(out_dir, exist_ok=True)

    for grouping_year, le_stats, ob_stats, le_quart, ob_quart in all_tables:
        merged = (
            le_stats.rename(columns={"mean": "le_mean",
                                     "ci_lower": "le_ci_lower",
                                     "ci_upper": "le_ci_upper"})
            .merge(
                ob_stats.rename(columns={"mean": "obes_mean",
                                         "ci_lower": "obes_ci_lower",
                                         "ci_upper": "obes_ci_upper"}),
                on=["group", "year"],
            )
            .merge(
                le_quart.rename(columns={"q1": "le_q1",
                                         "median": "le_median",
                                         "q3": "le_q3"}),
                on=["group", "year"],
            )
            .merge(
                ob_quart.rename(columns={"q1": "obes_q1",
                                         "median": "obes_median",
                                         "q3": "obes_q3"}),
                on=["group", "year"],
            )
        )
        merged["group_name"] = merged["group"].map(GROUP_NAMES)
        merged["grouping_year"] = grouping_year

        cols = [
            "grouping_year", "group", "group_name", "year",
            "le_mean", "le_ci_lower", "le_ci_upper",
            "le_q1", "le_median", "le_q3",
            "obes_mean", "obes_ci_lower", "obes_ci_upper",
            "obes_q1", "obes_median", "obes_q3",
        ]
        merged = merged[cols].sort_values(["group", "year"])

        path = os.path.join(out_dir, f"ci_table_{grouping_year}.csv")
        merged.to_csv(path, index=False, float_format="%.4f")
        print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== Downloading data ===")
    download_data()

    print("\n=== Loading & cleaning ===")
    gdp = load_gdp()
    life_exp = load_life_exp()
    population = load_population()
    obesity = load_obesity()

    gdp, life_exp, population, obesity = align_datasets(
        gdp, life_exp, population, obesity,
    )
    print(f"  Aligned to {len(gdp)} common countries")

    all_tables = []

    print("\n=== CI figures & median figures: all groups (4 GDP-grouping years) ===")
    for gy in GROUPING_YEARS:
        print(f"\n--- Grouping year: {gy} ---")
        labels, quantiles = assign_gdp_labels_for_year(gdp, gy)

        le_stats, ob_stats = plot_all_groups_with_ci(
            life_exp, obesity, population, gy, labels, quantiles,
        )
        le_quart, ob_quart = plot_all_groups_median(
            life_exp, obesity, gy, labels, quantiles,
        )
        all_tables.append((gy, le_stats, ob_stats, le_quart, ob_quart))

    print("\n=== Individual country scatter plots ===")
    for country in INDIVIDUAL_COUNTRIES:
        plot_country_scatter(life_exp, obesity, country)

    print("\n=== Saving CI tables ===")
    save_ci_tables(all_tables)

    print(f"\nDone. All CI figures and tables saved under '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    main()
