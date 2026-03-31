"""
Visualizations: GDP, Obesity & Life Expectancy across all countries (1980-2015)

Produces 9 figure sets:

  Pairplots
    1. pairplots/                      — one pairplot per country
    2. pairplots_group/                — one pairplot per GDP quintile group
    3. pairplot_groups.png             — single pairplot with all 5 groups (hue)

  Life Expectancy & Obesity  (ylim 65-85)
    4. scatter_obes_vs_lifeexp/        — one scatter per country
    5. scatter_obes_vs_lifeexp_group/  — one scatter per GDP group
    6. all_groups_obesity_vs_lifeexp   — all groups on one chart

  Life Expectancy & GDP  (ylim 65-85)
    7. gdp_vs_lifeexp/                 — one scatter per country
    8. gdp_vs_lifeexp_group/           — one scatter per GDP group
    9. all_groups_gdp_vs_lifeexp       — all groups on one chart
"""

import os
import math
import urllib.request
import warnings

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

YEARS = [str(y) for y in range(1980, 2016)]
QUANTILE_YEAR = "1997"

BASE_URL = "https://raw.githubusercontent.com/semensorokin/NLP_projects/master/gregrsGraf"
FILES = {
    "gdp": "imf-dm-export-20200224.csv",
    "life_exp": "new_Life_Exp.csv",
    "obesity": "IHME_GBD_2015_OBESITY_PREVALENCE_1980_2015_Y2017M06D12.CSV",
    "population": "res_population.csv",
}

LOCATION_NAMES = [
    "China", "North Korea", "Taiwan", "Cambodia", "Indonesia", "Laos",
    "Malaysia", "Maldives", "Myanmar", "Philippines", "Sri Lanka", "Thailand",
    "Timor-Leste", "Vietnam", "Oceania", "Fiji", "Kiribati",
    "Marshall Islands", "Federated States of Micronesia",
    "Papua New Guinea", "Samoa", "Solomon Islands", "Tonga", "Vanuatu",
    "Armenia", "Azerbaijan", "Georgia", "Kazakhstan", "Kyrgyzstan",
    "Mongolia", "Tajikistan", "Turkmenistan", "Uzbekistan", "Albania",
    "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Czech Republic",
    "Hungary", "Macedonia", "Montenegro", "Poland", "Romania", "Serbia",
    "Slovakia", "Slovenia", "Belarus", "Estonia", "Latvia", "Lithuania",
    "Moldova", "Russia", "Ukraine", "Brunei", "Japan", "South Korea",
    "Singapore", "Australasia", "Australia", "New Zealand", "Andorra",
    "Austria", "Belgium", "Cyprus", "Denmark", "Finland", "France",
    "Germany", "Greece", "Iceland", "Ireland", "Israel", "Italy",
    "Luxembourg", "Malta", "Netherlands", "Norway", "Portugal", "Spain",
    "Sweden", "Switzerland", "United Kingdom", "Argentina", "Chile",
    "Uruguay", "Canada", "United States",
    "Latin America and Caribbean", "Caribbean", "Antigua and Barbuda",
    "The Bahamas", "Barbados", "Belize", "Cuba", "Dominica",
    "Dominican Republic", "Grenada", "Guyana", "Haiti", "Jamaica",
    "Suriname", "Trinidad and Tobago", "Andean Latin America", "Bolivia",
    "Ecuador", "Peru", "Colombia", "Costa Rica", "El Salvador",
    "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama", "Brazil",
    "Paraguay", "Algeria", "Bahrain", "Iraq", "Jordan", "Kuwait",
    "Lebanon", "Libya", "Morocco", "Palestine", "Oman", "Qatar",
    "Saudi Arabia", "Syria", "Tunisia", "Turkey", "United Arab Emirates",
    "Yemen", "South Asia", "Afghanistan", "Bangladesh", "Bhutan", "India",
    "Nepal", "Pakistan", "Angola", "Central African Republic", "Congo",
    "Democratic Republic of the Congo", "Equatorial Guinea", "Gabon",
    "Burundi", "Comoros", "Djibouti", "Eritrea", "Ethiopia", "Kenya",
    "Madagascar", "Malawi", "Mauritius", "Mozambique", "Rwanda",
    "Seychelles", "Somalia", "Tanzania", "Uganda", "Zambia", "Botswana",
    "Lesotho", "Namibia", "Swaziland", "Zimbabwe", "Benin",
    "Burkina Faso", "Cameroon", "Cape Verde", "Chad", "Cote d'Ivoire",
    "The Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Liberia", "Mali",
    "Mauritania", "Niger", "Nigeria", "Sao Tome and Principe", "Senegal",
    "Sierra Leone", "Togo", "American Samoa", "Bermuda", "Greenland",
    "Guam", "Northern Mariana Islands", "Puerto Rico",
    "Virgin Islands, U.S.", "South Sudan", "Sudan",
]

OUTPUT_DIR = "figures"


# ---------------------------------------------------------------------------
# Data download
# ---------------------------------------------------------------------------
def download_data():
    for key, fname in FILES.items():
        if not os.path.exists(fname):
            print(f"Downloading {fname} ...")
            urllib.request.urlretrieve(f"{BASE_URL}/{fname}", fname)
        else:
            print(f"Already exists: {fname}")


# ---------------------------------------------------------------------------
# Data loading & cleaning
# ---------------------------------------------------------------------------
def load_gdp() -> pd.DataFrame:
    raw = pd.read_csv(FILES["gdp"], sep=";")
    long_col = "GDP per capita, current prices (Purchasing power parity; international dollars per capita)"
    df = raw[[long_col] + YEARS].copy()
    df.columns = ["Country Name"] + YEARS
    for y in YEARS:
        df[y] = pd.to_numeric(df[y], errors="coerce")
    df = df.dropna()
    return df


def load_life_exp() -> pd.DataFrame:
    df = pd.read_csv(FILES["life_exp"], encoding="windows-1252", sep=";")
    df = df[["Country Name"] + YEARS].copy()
    for y in YEARS:
        df[y] = pd.to_numeric(df[y], errors="coerce")
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(lambda row: row.fillna(row.mean()), axis=1)
    df = df.fillna(0)
    return df


def load_population() -> pd.DataFrame:
    df = pd.read_csv(FILES["population"])
    df = df[["Country Name"] + YEARS].copy()
    for y in YEARS:
        df[y] = pd.to_numeric(df[y], errors="coerce")
    return df


def load_obesity() -> pd.DataFrame:
    raw = pd.read_csv(FILES["obesity"])
    mask = (
        (raw["sex"] == "Both")
        & (raw["age_group_name"].str.contains("adults.*20.*age-standardized", case=False, na=False))
        & (raw["metric"] == "Percent")
    )
    filtered = raw.loc[mask, ["location_name", "year_id", "mean"]]
    pivoted = filtered.pivot_table(index="location_name", columns="year_id", values="mean")
    pivoted = pivoted.reset_index().sort_values("location_name")
    pivoted.columns = [str(c) for c in pivoted.columns]
    pivoted = pivoted.rename(columns={"location_name": "Country Name"})
    return pivoted


def align_datasets(gdp, life_exp, population, obesity):
    """Keep only countries present in all four datasets AND in LOCATION_NAMES."""
    loc_set = set(LOCATION_NAMES)

    gdp_countries = set(gdp["Country Name"])
    le_countries = set(life_exp["Country Name"])
    pop_countries = set(population["Country Name"])
    ob_countries = set(obesity["Country Name"])

    common = gdp_countries & le_countries & pop_countries & ob_countries & loc_set

    gdp = gdp[gdp["Country Name"].isin(common)].reset_index(drop=True)
    life_exp = life_exp[life_exp["Country Name"].isin(common)].reset_index(drop=True)
    population = population[population["Country Name"].isin(common)].reset_index(drop=True)
    obesity = obesity[obesity["Country Name"].isin(common)].reset_index(drop=True)

    for df in (gdp, life_exp, population, obesity):
        df.sort_values("Country Name", inplace=True)
        df.reset_index(drop=True, inplace=True)

    return gdp, life_exp, population, obesity


# ---------------------------------------------------------------------------
# GDP quintile labeling
# ---------------------------------------------------------------------------
def assign_gdp_labels(gdp: pd.DataFrame) -> pd.DataFrame:
    quantiles = gdp[QUANTILE_YEAR].quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]).tolist()
    bins = quantiles
    bins[-1] += 1  # include the max value
    labels_col = pd.cut(gdp[QUANTILE_YEAR], bins=bins, labels=[0, 1, 2, 3, 4], include_lowest=True)
    gdp = gdp.copy()
    gdp["label"] = labels_col.astype(int)
    return gdp


# ---------------------------------------------------------------------------
# Population-weighted group means
# ---------------------------------------------------------------------------
def pop_weighted_group_mean(metric_df, pop_df, labels):
    """Compute population-weighted mean of `metric_df` per GDP group."""
    weighted = metric_df[YEARS].values * pop_df[YEARS].values
    tmp = pd.DataFrame(weighted, columns=YEARS)
    tmp["label"] = labels
    pop_tmp = pop_df[YEARS].copy()
    pop_tmp["label"] = labels

    weighted_sum = tmp.groupby("label")[YEARS].sum()
    pop_sum = pop_tmp.groupby("label")[YEARS].sum()
    return weighted_sum / pop_sum


# ---------------------------------------------------------------------------
# Build long-form per-country data (for pairplot)
# ---------------------------------------------------------------------------
def build_country_long(gdp, life_exp, obesity, labels):
    """One row per (country, year) with columns: country, year, gdp, lifeExp, obes, label."""
    rows = []
    countries = gdp["Country Name"].tolist()
    for idx, country in enumerate(countries):
        for y in YEARS:
            g = gdp.loc[idx, y]
            le = life_exp.loc[idx, y]
            ob = obesity.loc[idx, y]
            lbl = labels[idx]
            if g > 0:
                rows.append((country, int(y), math.log(g), le, ob, lbl))
    return pd.DataFrame(rows, columns=["country", "year", "gdp", "lifeExp", "obes", "label"])


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
GROUP_NAMES = {
    0: "Quintile 1 (poorest)",
    1: "Quintile 2",
    2: "Quintile 3",
    3: "Quintile 4",
    4: "Quintile 5 (richest)",
}


def safe_filename(name: str) -> str:
    return name.replace(" ", "_").replace("'", "").replace(",", "").replace(".", "")


# ---- Vis 1: one pairplot per country ----

def plot_pairplots_per_country(long_df: pd.DataFrame):
    out = os.path.join(OUTPUT_DIR, "pairplots")
    os.makedirs(out, exist_ok=True)

    countries = sorted(long_df["country"].unique())
    total = len(countries)
    for i, country in enumerate(countries, 1):
        cdf = long_df[long_df["country"] == country][["obes", "lifeExp", "gdp"]].copy()
        g = sns.pairplot(cdf, vars=["obes", "lifeExp", "gdp"], height=3, aspect=1)
        g.figure.suptitle(f"{country} (1980–2015)", y=1.03, fontsize=14, weight="bold")
        fname = f"{safe_filename(country)}.png"
        g.savefig(os.path.join(out, fname), dpi=150, bbox_inches="tight")
        plt.close("all")
        print(f"  [{i}/{total}] pairplots/{fname}")

    print(f"  -> {total} pairplots saved to {out}/")


# ---- Vis 1b: one pairplot per GDP group ----

def plot_pairplots_per_group(long_df: pd.DataFrame):
    out = os.path.join(OUTPUT_DIR, "pairplots_group")
    os.makedirs(out, exist_ok=True)

    for grp in range(5):
        gdf = long_df[long_df["label"] == grp][["obes", "lifeExp", "gdp"]].copy()
        g = sns.pairplot(gdf, vars=["obes", "lifeExp", "gdp"], height=3, aspect=1)
        g.figure.suptitle(
            f"{GROUP_NAMES[grp]} (1980–2015)", y=1.03, fontsize=14, weight="bold",
        )
        fname = f"group_{grp}_{safe_filename(GROUP_NAMES[grp])}.png"
        g.savefig(os.path.join(out, fname), dpi=150, bbox_inches="tight")
        plt.close("all")
        print(f"  [{grp+1}/5] pairplots_group/{fname}")

    print(f"  -> 5 group pairplots saved to {out}/")


# ---- Vis 3: pairplot comparing all 5 GDP groups ----

def plot_pairplot_groups(gdp_df, life_exp_df, obesity_df, pop_df, labels):
    """Pairplot of (obesity, life expectancy, log GDP) with hue = GDP quintile group.

    Each data point is one (group, year) pair using population-weighted averages.
    """
    grp_le = pop_weighted_group_mean(life_exp_df, pop_df, labels)
    grp_ob = pop_weighted_group_mean(obesity_df, pop_df, labels)
    grp_gdp = pop_weighted_group_mean(gdp_df, pop_df, labels)

    rows = []
    for grp in range(5):
        for y in YEARS:
            rows.append({
                "GDP Group": GROUP_NAMES[grp],
                "Obesity": grp_ob.loc[grp, y],
                "Life Expectancy": grp_le.loc[grp, y],
                "Log GDP": np.log(grp_gdp.loc[grp, y]),
                "Year": int(y),
            })
    df = pd.DataFrame(rows)

    palette = ["#d73027", "#fc8d59", "#fee08b", "#91bfdb", "#4575b4"]
    g = sns.pairplot(
        df,
        vars=["Obesity", "Life Expectancy", "Log GDP"],
        hue="GDP Group",
        palette=palette,
        height=4.5,
        aspect=1,
        plot_kws={"alpha": 0.75, "s": 55},
        diag_kws={"alpha": 0.5},
    )
    g.figure.suptitle(
        "GDP Quintile Groups — Obesity, Life Expectancy & Log GDP  (1980–2015)",
        y=1.03, fontsize=15, weight="bold",
    )
    path = os.path.join(OUTPUT_DIR, "pairplot_groups.png")
    g.savefig(path, dpi=200, bbox_inches="tight")
    plt.close("all")
    print(f"  Saved: pairplot_groups.png")


# ---- Vis 5: obesity vs life expectancy per GDP group (year labels, ylim 45-85) ----

def plot_obes_vs_lifeexp_per_group(life_exp_df, obesity_df, pop_df, labels):
    out = os.path.join(OUTPUT_DIR, "scatter_obes_vs_lifeexp_group")
    os.makedirs(out, exist_ok=True)

    grp_le = pop_weighted_group_mean(life_exp_df, pop_df, labels)
    grp_ob = pop_weighted_group_mean(obesity_df, pop_df, labels)
    years_int = [int(y) for y in YEARS]

    for grp in range(5):
        obes = grp_ob.loc[grp, YEARS].values.astype(float)
        le = grp_le.loc[grp, YEARS].values.astype(float)

        scatter_df = pd.DataFrame({
            "Obesity prevalence": obes,
            "Life expectancy": le,
            "Year": years_int,
        })

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(obes, le, s=40, color="#4878a8", alpha=0.85)
        for _, row in scatter_df.iterrows():
            ax.annotate(
                str(int(row["Year"]))[2:],
                (row["Obesity prevalence"], row["Life expectancy"]),
                fontsize=8, ha="center", va="bottom",
            )
        ax.set_title(
            f"Life Expectancy vs Obesity — {GROUP_NAMES[grp]}",
            fontsize=15, weight="bold",
        )
        ax.set_xlabel("Population-weighted obesity prevalence (fraction)", fontsize=13)
        ax.set_ylabel("Life expectancy (years)", fontsize=13)
        ax.set_ylim(45, 85)
        ax.grid(False)
        fig.tight_layout()
        fname = f"group_{grp}_{safe_filename(GROUP_NAMES[grp])}.png"
        fig.savefig(os.path.join(out, fname), dpi=150)
        plt.close("all")
        print(f"  [{grp+1}/5] scatter_obes_vs_lifeexp_group/{fname}")

    print(f"  -> 5 group plots saved to {out}/")


# ---- Vis 6: obesity vs life expectancy all groups together (ylim 45-85) ----

def plot_obes_vs_lifeexp_all_groups(gdp_df, life_exp_df, obesity_df, pop_df, labels):
    grp_le = pop_weighted_group_mean(life_exp_df, pop_df, labels)
    grp_ob = pop_weighted_group_mean(obesity_df, pop_df, labels)

    quantiles = gdp_df[QUANTILE_YEAR].quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]).tolist()
    intervals = []
    for i in range(5):
        lo = int(round(quantiles[i]))
        hi = int(round(quantiles[i + 1]))
        intervals.append((lo, hi))

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    fig, ax = plt.subplots(figsize=(12, 8))
    for grp in range(5):
        obes = grp_ob.loc[grp, YEARS].values.astype(float)
        le = grp_le.loc[grp, YEARS].values.astype(float)
        lo, hi = intervals[grp]
        label = f"Group {grp+1}. GDP Interval ({lo} - {hi})"
        ax.scatter(obes, le, s=30, color=colors[grp], label=label, alpha=0.85)

    ax.set_title("Dependency between life expectancy and obesity", fontsize=18)
    ax.set_xlabel("Obesity", fontsize=14)
    ax.set_ylabel("Life expectancy", fontsize=14)
    ax.set_ylim(45, 85)
    ax.legend(loc="lower left", fontsize=10, framealpha=0.9)
    ax.grid(False)
    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, "all_groups_obesity_vs_lifeexp.png")
    fig.savefig(path, dpi=200)
    plt.close("all")
    print(f"  Saved: all_groups_obesity_vs_lifeexp.png")


# ---- Vis 7: GDP vs Life Expectancy scatter per country (year labels, ylim 65-85) ----

def plot_gdp_vs_lifeexp_per_country(gdp_df, life_exp_df):
    out = os.path.join(OUTPUT_DIR, "gdp_vs_lifeexp")
    os.makedirs(out, exist_ok=True)

    countries = gdp_df["Country Name"].tolist()
    total = len(countries)
    for i, country in enumerate(countries):
        gdp_vals = gdp_df.loc[i, YEARS].values.astype(float)
        le_vals = life_exp_df.loc[i, YEARS].values.astype(float)
        year_labels = [y[2:] for y in YEARS]

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(gdp_vals, le_vals, s=35, color="#4878a8", alpha=0.85)
        for gv, lv, yl in zip(gdp_vals, le_vals, year_labels):
            ax.annotate(yl, (gv, lv), fontsize=8, ha="center", va="bottom")

        ax.set_title(
            f"Dependency between life expectancy and GDP in {country}",
            fontsize=15, weight="bold",
        )
        ax.set_xlabel("GDP", fontsize=13)
        ax.set_ylabel("Life expectancy", fontsize=13)
        if le_vals.min() >= 65 and le_vals.max() <= 85:
            ax.set_ylim(65, 85)
        ax.grid(False)
        fig.tight_layout()
        fname = f"{safe_filename(country)}.png"
        fig.savefig(os.path.join(out, fname), dpi=150)
        plt.close("all")
        print(f"  [{i+1}/{total}] gdp_vs_lifeexp/{fname}")

    print(f"  -> {total} plots saved to {out}/")


# ---- Vis 4: Obesity vs Life Expectancy scatter per country (year labels, ylim 65-85) ----

def plot_obes_vs_lifeexp_scatter_per_country(life_exp_df, obesity_df):
    out = os.path.join(OUTPUT_DIR, "scatter_obes_vs_lifeexp")
    os.makedirs(out, exist_ok=True)

    countries = life_exp_df["Country Name"].tolist()
    total = len(countries)
    for i, country in enumerate(countries):
        obes_vals = obesity_df.loc[i, YEARS].values.astype(float)
        le_vals = life_exp_df.loc[i, YEARS].values.astype(float)
        year_labels = [y[2:] for y in YEARS]

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(obes_vals, le_vals, s=35, color="#4878a8", alpha=0.85)
        for ov, lv, yl in zip(obes_vals, le_vals, year_labels):
            ax.annotate(yl, (ov, lv), fontsize=8, ha="center", va="bottom")

        ax.set_title(
            f"Dependency between Life Expectancy and Obesity in {country}",
            fontsize=15, weight="bold",
        )
        ax.set_xlabel("Obesity", fontsize=13)
        ax.set_ylabel("Life expectancy", fontsize=13,)
        if le_vals.min() >= 65 and le_vals.max() <= 85:
            ax.set_ylim(65, 85)
        ax.grid(False)
        fig.tight_layout()
        fname = f"{safe_filename(country)}.png"
        fig.savefig(os.path.join(out, fname), dpi=150)
        plt.close("all")
        print(f"  [{i+1}/{total}] scatter_obes_vs_lifeexp/{fname}")

    print(f"  -> {total} plots saved to {out}/")


# ---- Vis 8: GDP vs Life Expectancy per GDP group (year labels, ylim 45-85) ----

def plot_gdp_vs_lifeexp_per_group(gdp_df, life_exp_df, pop_df, labels):
    out = os.path.join(OUTPUT_DIR, "gdp_vs_lifeexp_group")
    os.makedirs(out, exist_ok=True)

    grp_le = pop_weighted_group_mean(life_exp_df, pop_df, labels)
    grp_gdp = pop_weighted_group_mean(gdp_df, pop_df, labels)
    years_int = [int(y) for y in YEARS]

    for grp in range(5):
        gdp_vals = np.log(grp_gdp.loc[grp, YEARS].values.astype(float))
        le_vals = grp_le.loc[grp, YEARS].values.astype(float)

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(gdp_vals, le_vals, s=40, color="#4878a8", alpha=0.85)
        for gv, lv, yr in zip(gdp_vals, le_vals, years_int):
            ax.annotate(str(yr)[2:], (gv, lv), fontsize=8, ha="center", va="bottom")

        ax.set_title(
            f"Life Expectancy vs Log GDP — {GROUP_NAMES[grp]}",
            fontsize=15, weight="bold",
        )
        ax.set_xlabel("Population-weighted log GDP per capita (PPP)", fontsize=13)
        ax.set_ylabel("Population-weighted life expectancy (years)", fontsize=13)
        ax.set_ylim(45, 85)
        ax.grid(False)
        fig.tight_layout()
        fname = f"group_{grp}_{safe_filename(GROUP_NAMES[grp])}.png"
        fig.savefig(os.path.join(out, fname), dpi=150)
        plt.close("all")
        print(f"  [{grp+1}/5] gdp_vs_lifeexp_group/{fname}")

    print(f"  -> 5 group plots saved to {out}/")


# ---- Vis 9: GDP vs Life Expectancy all groups together (ylim 45-85) ----

def plot_gdp_vs_lifeexp_all_groups(gdp_df, life_exp_df, pop_df, labels):
    grp_le = pop_weighted_group_mean(life_exp_df, pop_df, labels)
    grp_gdp = pop_weighted_group_mean(gdp_df, pop_df, labels)

    quantiles = gdp_df[QUANTILE_YEAR].quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]).tolist()
    intervals = []
    for i in range(5):
        lo = int(round(quantiles[i]))
        hi = int(round(quantiles[i + 1]))
        intervals.append((lo, hi))

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    fig, ax = plt.subplots(figsize=(12, 8))
    for grp in range(5):
        gdp_vals = np.log(grp_gdp.loc[grp, YEARS].values.astype(float))
        le_vals = grp_le.loc[grp, YEARS].values.astype(float)
        lo, hi = intervals[grp]
        label = f"Group {grp+1}. GDP Interval ({lo} - {hi})"
        ax.scatter(gdp_vals, le_vals, s=30, color=colors[grp], label=label, alpha=0.85)

    ax.set_title("Dependency between life expectancy and GDP", fontsize=18)
    ax.set_xlabel("Population-weighted log GDP per capita (PPP)", fontsize=14)
    ax.set_ylabel("Life expectancy", fontsize=14)
    ax.set_ylim(45, 85)
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax.grid(False)
    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, "all_groups_gdp_vs_lifeexp.png")
    fig.savefig(path, dpi=200)
    plt.close("all")
    print(f"  Saved: all_groups_gdp_vs_lifeexp.png")


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

    print(f"  GDP:        {gdp.shape}")
    print(f"  Life exp:   {life_exp.shape}")
    print(f"  Population: {population.shape}")
    print(f"  Obesity:    {obesity.shape}")

    gdp, life_exp, population, obesity = align_datasets(gdp, life_exp, population, obesity)
    n = len(gdp)
    print(f"\n  Aligned to {n} common countries")

    print("\n=== Assigning GDP quintile labels ===")
    gdp = assign_gdp_labels(gdp)
    labels = gdp["label"].values

    print("\n=== Building long-form dataset ===")
    long_df = build_country_long(gdp, life_exp, obesity, labels)
    print(f"  Rows: {len(long_df)}")

    print("\n=== 1/9  Pairplots (one per country) ===")
    plot_pairplots_per_country(long_df)

    print("\n=== 2/9  Pairplots (one per GDP group) ===")
    plot_pairplots_per_group(long_df)

    print("\n=== 3/9  Pairplot: 5 GDP groups compared ===")
    plot_pairplot_groups(gdp, life_exp, obesity, population, labels)

    print("\n=== 4/9  Obesity vs Life Exp scatter (one per country, ylim 65-85) ===")
    plot_obes_vs_lifeexp_scatter_per_country(life_exp, obesity)

    print("\n=== 5/9  Obesity vs Life Exp scatter (one per GDP group, ylim 65-85) ===")
    plot_obes_vs_lifeexp_per_group(life_exp, obesity, population, labels)

    print("\n=== 6/9  Obesity vs Life Exp scatter (all groups, ylim 65-85) ===")
    plot_obes_vs_lifeexp_all_groups(gdp, life_exp, obesity, population, labels)

    print("\n=== 7/9  GDP vs Life Exp (one per country, ylim 65-85) ===")
    plot_gdp_vs_lifeexp_per_country(gdp, life_exp)

    print("\n=== 8/9  GDP vs Life Exp (one per GDP group, ylim 65-85) ===")
    plot_gdp_vs_lifeexp_per_group(gdp, life_exp, population, labels)

    print("\n=== 9/9  GDP vs Life Exp (all groups, ylim 65-85) ===")
    plot_gdp_vs_lifeexp_all_groups(gdp, life_exp, population, labels)

    print(f"\nDone. All figures saved under '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    main()
