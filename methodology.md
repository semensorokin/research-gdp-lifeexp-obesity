# Methodology: Data Preparation and Chart Construction

This document describes, step by step, how the raw data are transformed and how every chart is produced. It is written for a researcher who needs to verify that the calculations match the intended methodology of the paper. No programming knowledge is required.

---

## 1. Data Sources

We use four datasets, all covering the period **1980–2015** (36 annual observations):

| Dataset | Source | What it contains |
|---|---|---|
| **GDP per capita** | IMF (file `imf-dm-export-20200224.csv`) | GDP per capita in purchasing-power-parity international dollars, one value per country per year |
| **Life expectancy** | `new_Life_Exp.csv` | Life expectancy at birth (years), one value per country per year |
| **Obesity prevalence** | IHME Global Burden of Disease 2015 (file `IHME_GBD_2015_OBESITY_PREVALENCE_1980_2015_Y2017M06D12.CSV`) | Prevalence of obesity as a fraction (0–1), many breakdowns by sex, age group, metric |
| **Population** | `res_population.csv` | Total population, one value per country per year |

---

## 2. Data Cleaning

### 2.1 GDP

- The raw file uses semicolons as separators.
- We keep only the column "GDP per capita, current prices (Purchasing power parity; international dollars per capita)" and the 36 year columns (1980–2015).
- All year values are converted to numbers. Rows where any value cannot be converted are dropped entirely.

### 2.2 Life Expectancy

- The raw file uses semicolons as separators and Windows-1252 character encoding.
- We keep only the "Country Name" column and the 36 year columns.
- **Handling missing years**: if a country has some years missing, we fill those gaps with the average of that country's available years. If a country still has missing values after this step, they are set to zero. (In practice this only affects countries that are later excluded during alignment.)

### 2.3 Population

- Straightforward: we keep "Country Name" and the 36 year columns, converting all values to numbers.

### 2.4 Obesity

- The IHME file contains many rows per country (different sexes, age groups, and metrics). We apply three filters simultaneously:
  1. **Sex** = "Both" (i.e., male and female combined)
  2. **Age group** = "adults (20+) age-standardized"
  3. **Metric** = "Percent"
- After filtering, we keep only the country name, the year, and the "mean" value (the point estimate of prevalence).
- We then reshape (pivot) the data so that each row is one country and each column is one year, matching the layout of the other three datasets.

---

## 3. Aligning the Four Datasets

We maintain a fixed list of approximately 170 recognized country/territory names. A country is included in the analysis **only if it appears in all four datasets AND in this master list**. This intersection produces roughly **119 countries**.

All four tables are then sorted alphabetically by country name so that row *i* in every table refers to the same country. This alignment is critical because later calculations combine values across tables row by row.

---

## 4. Assigning Countries to GDP Quintile Groups

### 4.1 Choosing the reference year

Countries are ranked and divided into five equal-sized groups (quintiles) based on their GDP per capita **in a single reference year**. The main analysis uses **1997** as the reference year. The confidence-interval analysis repeats the grouping for four reference years: **1990, 1997, 2005, and 2013**.

### 4.2 How the quintiles are computed

1. Take all ~119 GDP values for the reference year.
2. Find the values at the 0th, 20th, 40th, 60th, 80th, and 100th percentiles. These six numbers define five intervals (bins).
3. Assign each country to the bin its GDP falls into:
   - **Group 1 (Quintile 1)** — the poorest 20% of countries
   - **Group 2 (Quintile 2)**
   - **Group 3 (Quintile 3)**
   - **Group 4 (Quintile 4)**
   - **Group 5 (Quintile 5)** — the richest 20% of countries

**Boundary rule**: the bins are constructed as half-open intervals — (a, b] — except for the very first bin, which is closed on both sides [a, b]. This means that if a country's GDP is exactly equal to a boundary value (e.g. the 20th-percentile threshold), it always falls into the **lower** group. No country can fall into two groups at once.

### 4.3 A note on group composition

Once groups are assigned using the reference year, **the same group assignments are used for all 36 years (1980–2015)**. A country that was in Group 3 based on 1997 GDP stays in Group 3 for every year's calculations, regardless of how its GDP changed in other years.

---

## 5. Population-Weighted Group Averages

Many of our charts show a single value per group per year (e.g., "the obesity prevalence of Group 2 in 2004"). This value is a **population-weighted average**, computed as follows:

> For a given group in a given year, multiply each country's metric value by that country's population in that same year, sum the products, then divide by the total population of the group in that year.

In formula terms, for a group containing countries 1, 2, ..., k in year Y:

    Weighted average = (metric₁ × pop₁ + metric₂ × pop₂ + ... + metricₖ × popₖ) / (pop₁ + pop₂ + ... + popₖ)

This is done independently for each year, so the populations used as weights change from year to year (reflecting demographic growth). It is also done separately for each metric (life expectancy, obesity, GDP).

The effect: large countries (e.g., India, China) contribute more to their group's average than small countries (e.g., Bhutan, Maldives).

---

## 6. Confidence Intervals (CI Analysis)

In addition to population-weighted means, we also compute **95% confidence intervals** for the weighted means. The methodology is the analytic-weights (reliability-weights) formulation:

1. Let w₁, w₂, ..., wₙ be the population weights of the n countries in a group for a given year.
2. Let x₁, x₂, ..., xₙ be their metric values (e.g., life expectancy).
3. Compute:
   - V₁ = sum of all weights = w₁ + w₂ + ... + wₙ
   - V₂ = sum of squared weights = w₁² + w₂² + ... + wₙ²
   - Weighted mean: x̄ = (w₁·x₁ + w₂·x₂ + ... + wₙ·xₙ) / V₁
   - Bessel-corrected weighted variance: s² = [V₁ / (V₁² − V₂)] × Σ wᵢ·(xᵢ − x̄)²
   - Variance of the weighted mean: Var(x̄) = s² × V₂ / V₁²
   - Standard error: SE = √Var(x̄)
4. The 95% confidence interval is: **x̄ ± t(n−1, 0.975) × SE**, where t(n−1, 0.975) is the critical value from Student's t-distribution with n−1 degrees of freedom.

This CI quantifies how precisely we can estimate the group-level average, given the variation among countries within the group. Larger groups and more uniform values produce narrower intervals.

### Unweighted Medians and Quartiles

Separately, we also compute the **unweighted** 25th percentile (Q1), median, and 75th percentile (Q3) of each metric within each group and year. These are simple order-based statistics treating every country equally, regardless of population size.

---

## 7. GDP Transformation: Logarithm

Whenever GDP values are used as a chart axis or as a variable in pairplots, we apply the **natural logarithm** (ln) to the raw GDP per capita values. This is standard practice because GDP distributions are highly skewed — a few very rich countries have GDP values many times larger than most others. The logarithm compresses these differences and makes the relationship with life expectancy more nearly linear.

On charts, this axis is labeled "Log GDP" or "Population-weighted log GDP per capita (PPP)".

---

## 8. Charts Produced

### 8.1 Per-Country Pairplots

**What is shown**: For each of the ~119 countries individually, a 3×3 grid of scatter plots showing every pairwise combination of obesity, life expectancy, and log GDP. Each dot is one year (1980–2015). The diagonal panels show the distribution of each variable.

**Data used**: Raw country-level values (not grouped, not weighted). GDP is log-transformed.

**Purpose**: Allows visual inspection of whether a given country's obesity, life expectancy, and GDP move together over time.

### 8.2 Per-Group Pairplots

**What is shown**: Same 3×3 pairplot grid, but pooling all countries within a GDP quintile group. Each dot is one (country, year) pair.

**Data used**: Raw country-level values. GDP is log-transformed. Countries are colored/grouped by their quintile assignment.

### 8.3 All-Groups Pairplot (Combined)

**What is shown**: A single 3×3 pairplot where each dot represents one (group, year) combination — so there are 5 groups × 36 years = 180 dots total. Dots are color-coded by GDP quintile group.

**Data used**: **Population-weighted** group averages for obesity, life expectancy, and log GDP.

**Purpose**: Summarizes the group-level relationships across all groups simultaneously.

### 8.4 Obesity vs. Life Expectancy — Per Country

**What is shown**: For each country, a scatter plot with obesity on the horizontal axis and life expectancy on the vertical axis. Each dot is one year, labeled with the last two digits of the year (e.g., "97" for 1997).

**Data used**: Raw country-level values (not weighted).

**Y-axis range**: Automatically set to 65–85 only if all of the country's life expectancy values fall within that range; otherwise, the axis adjusts to fit the data.

### 8.5 Obesity vs. Life Expectancy — Per Group

**What is shown**: For each of the five GDP quintile groups, a scatter plot with obesity on the horizontal axis and life expectancy on the vertical axis. Each dot is one year.

**Data used**: **Population-weighted** group averages. Each dot's x-coordinate is the weighted average obesity of the group in that year; the y-coordinate is the weighted average life expectancy.

**Y-axis range**: Fixed at 45–85 to accommodate all five groups on a comparable scale.

### 8.6 Obesity vs. Life Expectancy — All Groups Together

**What is shown**: All five GDP groups on a single chart. Each group is a different color. The legend indicates the GDP per capita interval (in dollars) that defines each group.

**Data used**: **Population-weighted** group averages.

**Y-axis range**: Fixed at 45–85.

**Legend labels**: "Group N. GDP Interval (low – high)" where low and high are the quintile boundaries for that group, expressed in dollars.

### 8.7 GDP vs. Life Expectancy — Per Country

**What is shown**: For each country, a scatter plot with GDP per capita (raw, not logged) on the horizontal axis and life expectancy on the vertical axis. Year labels on each dot.

**Data used**: Raw country-level values.

**Y-axis range**: 65–85 if data fits; otherwise auto-adjusted.

### 8.8 GDP vs. Life Expectancy — Per Group

**What is shown**: For each of the five groups, a scatter plot with **log GDP** on the horizontal axis and life expectancy on the vertical axis. Year labels on each dot.

**Data used**: **Population-weighted** group averages. GDP is log-transformed for the horizontal axis.

**Y-axis range**: Fixed at 45–85.

### 8.9 GDP vs. Life Expectancy — All Groups Together

**What is shown**: All five groups on a single chart, same layout as 8.6 but with log GDP on the x-axis instead of obesity.

**Data used**: **Population-weighted** group averages. GDP is log-transformed.

### 8.10 Obesity vs. Life Expectancy with Confidence Intervals (CI Charts)

**What is shown**: All five GDP groups on one chart, similar to 8.6, but each dot has vertical error bars representing the 95% confidence interval of the life expectancy weighted mean.

**Data used**: Population-weighted means and their confidence intervals (see Section 6). Produced for **four different GDP-grouping years** (1990, 1997, 2005, 2013), so the group composition changes across charts.

### 8.11 Obesity vs. Life Expectancy — Medians (No Error Bars)

**What is shown**: Same layout as 8.10, but using **unweighted medians** instead of weighted means, and without error bars.

**Data used**: Unweighted median obesity and median life expectancy within each group.

**Y-axis range**: Fixed at 45–85. Produced for each of the four grouping years.

### 8.12 Individual Country Scatter (Israel, Argentina)

**What is shown**: Obesity vs. life expectancy scatter for Israel and Argentina individually, with year labels.

**Y-axis range**: Fixed at 65–85.

---

## 9. CSV Tables

For each of the four GDP-grouping years (1990, 1997, 2005, 2013), a CSV table is exported containing, for every (group, year) combination:

| Column | Description |
|---|---|
| `grouping_year` | Which year was used to assign countries to GDP groups |
| `group` | Group number (0–4) |
| `group_name` | Human-readable group name (e.g., "Quintile 3") |
| `year` | The data year (1980–2015) |
| `le_mean` | Population-weighted mean life expectancy |
| `le_ci_lower` | Lower bound of 95% CI for life expectancy |
| `le_ci_upper` | Upper bound of 95% CI for life expectancy |
| `le_q1` | 25th percentile (unweighted) of life expectancy |
| `le_median` | Median (unweighted) of life expectancy |
| `le_q3` | 75th percentile (unweighted) of life expectancy |
| `obes_mean` | Population-weighted mean obesity prevalence |
| `obes_ci_lower` | Lower bound of 95% CI for obesity |
| `obes_ci_upper` | Upper bound of 95% CI for obesity |
| `obes_q1` | 25th percentile (unweighted) of obesity |
| `obes_median` | Median (unweighted) of obesity |
| `obes_q3` | 75th percentile (unweighted) of obesity |

These tables allow the researcher to verify any plotted value by looking up the exact numbers.

---

## 10. Summary of Key Methodological Choices

1. **Time range**: 1980–2015 (36 years), all years used in all charts.
2. **Country set**: ~119 countries that appear in all four source datasets and in the recognized-name list.
3. **Obesity filter**: both sexes combined, adults 20+, age-standardized, measured as a percentage (fraction).
4. **GDP grouping**: quintiles based on a single reference year; group membership is fixed across all years.
5. **Weighting**: all group-level averages in charts are population-weighted (larger countries count more).
6. **GDP scale**: natural logarithm applied wherever GDP is used as a variable in charts.
7. **Confidence intervals**: analytic-weights formulation with Bessel correction and t-distribution critical values.
8. **Missing life expectancy data**: filled with the country's own mean across available years before alignment.
