# Notebook Analysis: GDP, Obesity, Life Expectancy & Population (1980–2015)

## Research Question

The notebook investigates the **relationship between economic development (GDP per capita PPP), obesity prevalence, life expectancy, and population** across ~119 countries over 1980–2015. Core questions:

- How do countries at different GDP levels differ in life expectancy and obesity trends?
- Is there a measurable correlation between obesity prevalence and life expectancy?
- How does weighting by population change these group-level relationships?

---

## Datasets


| #   | File                                                            | Description                                                                                                   |
| --- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 1   | `imf-dm-export-20200224.csv`                                    | **GDP per capita** (PPP, international dollars) by country, 1980–2015. Source: IMF.                           |
| 2   | `new_Life_Exp.csv`                                              | **Life expectancy** by country and year, 1980–2015.                                                           |
| 3   | `IHME_GBD_2015_OBESITY_PREVALENCE_1980_2015_Y2017M06D12.CSV`    | **Obesity prevalence** (IHME Global Burden of Disease 2015) by country, year, sex, age group, metric. ~96 MB. |
| 4   | `IHME_GBD_2015_OVERWEIGHT_PREVALENCE_1980_2015_Y2017M06D12.CSV` | **Overweight prevalence** (IHME GBD 2015). Downloaded but **not used** in the analysis.                       |
| 5   | `res_population.csv`                                            | **Population** by country and year, 1980–2015.                                                                |
| 6   | `count.csv`                                                     | Supplementary file with country names (120 unique). Loaded near the end but not meaningfully integrated.      |


All files are fetched via `wget` from a GitHub repository.

---

## Data Cleaning & Manipulation

### GDP

1. Read CSV with `;` separator.
2. Selected GDP per capita column (renamed to `Country Name`) + year columns 1980–2015 → shape (139, 37).
3. Cast all year columns to `float`.
4. Manually renamed one row's country to `'Russia'`.
5. Dropped rows with NaN → 139 countries.
6. Defined a master list of 195 real country names (excluding aggregate regions/continents).
7. Filtered to countries present in both GDP data and the master list → **119 countries**.

### Life Expectancy

1. Read CSV with `windows-1252` encoding, `;` separator.
2. Selected `Country Name` + year columns 1980–2015.
3. Filled NaN per row using each row's mean, then remaining NaN with 0.
4. Filtered to the same 119 countries → shape (119, 37).

### Population

1. Read CSV, selected `Country Name` + year columns 1980–2015.
2. Filtered to the same 119 countries → shape (119, 37).

### Obesity

1. Read the large IHME CSV.
2. Filtered for: `sex == 'Both'`, `age_group_name == 'adults (20+) age-standardized'`, `metric == 'Percent'`.
3. Further filtered to 119 countries.
4. Selected `location_name`, `year_id`, `mean`.
5. Pivoted: index = `location_name`, columns = `year_id`, values = `mean`.
6. Sorted by `location_name` → shape (119, 37).

---

## Derived Features / Variables

### GDP Quintile Labels

- Computed quantiles (0%, 20%, 40%, 60%, 80%, 100%) on GDP values for reference year **1997**.
- Created 5 bins and assigned each country a label (0–4): **0 = poorest, 4 = richest**.

### Grouped GDP Means

- Grouped countries by GDP label, computed mean GDP per capita per group across all years → 5 rows × 36 year columns.

### Population-Weighted Life Expectancy by GDP Group

- Computed `life_exp × population` for all 119 countries.
- Grouped by GDP label, summed, then divided by total group population.
- Result (1980 → 2015):
  - Group 0 (poorest): 48.2 → 64.4
  - Group 1: 55.0 → 68.1
  - Group 2: 62.5 → 73.0
  - Group 3: 68.6 → 78.0
  - Group 4 (richest): 74.0 → 80.6

### Population-Weighted Obesity Prevalence by GDP Group

- Same weighting approach as life expectancy.
- Result (1980 → 2015):
  - Group 0: 11.1% → 21.3%
  - Group 1: 10.9% → 21.4%
  - Group 2: 11.5% → 19.0%
  - Group 3: 9.3% → 17.1%
  - Group 4: 6.3% → 15.3%

### Normalized Obesity (Baseline = 1995)

- For each country/year, subtracted that country's 1995 obesity value → shows **change relative to 1995**.

### Per-Country Analysis Function (`one_country_()`)

- For a given country, builds a DataFrame with 3 columns: `gdp` (log-transformed), `lifeExp`, `obes`.
- Used for pairplot visualization.

---

## Visualizations


| #   | Type                            | Data Shown                                                                                  | Key Insight                                                                             |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 1   | **Heatmap** (seaborn)           | Mean life expectancy per GDP quintile group across years                                    | Clear gradient — higher GDP → higher life expectancy. All groups trend upward.          |
| 2   | **Heatmap** (seaborn)           | Mean obesity prevalence per GDP quintile group across years                                 | Obesity rises in all groups. Pattern across groups is not strictly monotonic with GDP.  |
| 3   | **Interactive scatter** (Bokeh) | GDP group 2 countries: X = obesity, Y = life expectancy, bubble size = log(population)      | Shows per-country trajectories in obesity–life expectancy space over time.              |
| 4   | **Pairplot** (seaborn)          | Single country (e.g. Argentina): pairwise scatter + regression for `obes`, `lifeExp`, `gdp` | Strong positive correlation between all three variables over time for Argentina.        |
| 5   | **Regression plot** (seaborn)   | Obesity vs life expectancy, all 119 countries, year 2005                                    | **Broken cell** — references `norm_life_exp` which was commented out. Would not render. |
| 6   | **Regression plot** (seaborn)   | Group-level mean obesity vs mean life expectancy (5 GDP groups), year 2005                  | Positive relationship — both increase with GDP.                                         |


---

## Statistical Methods


| Method                                 | Usage                              | Details                                                                |
| -------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| Quantile-based binning                 | GDP grouping                       | Countries split into 5 quintiles based on 1997 GDP                     |
| Linear regression (via `sns.regplot`)  | Obesity vs Life Expectancy plots   | Seaborn auto-fits and displays linear regression + confidence interval |
| Linear regression (via `sns.pairplot`) | Per-country analysis               | Pairplot shows regression for each variable pair                       |
| Population weighting                   | Life expectancy & obesity by group | Weighted avg = Σ(metric × pop) / Σ(pop) per group                      |


No formal ML models (sklearn, etc.) are trained. The notebook is purely **exploratory/descriptive**.

---

## Key Findings

1. **GDP and life expectancy are strongly correlated.** A persistent ~16-year gap exists between poorest and richest quintiles across the entire 1980–2015 period, though all groups improve over time.
2. **Obesity is rising universally.** Every GDP group shows increasing obesity (roughly doubling or tripling from 1980 to 2015).
3. **Positive ecological correlation between obesity and life expectancy** at both country and group level. This is likely driven by the confounding variable of economic development — richer countries tend to have both higher obesity and higher life expectancy.
4. **Population weighting matters.** Low-middle income groups contain massive populations (India, Pakistan, Bangladesh — ~~2 billion by 2015) vs. high income (~~0.8–1.5 billion), so weighted averages differ significantly from simple country-level means.
5. **Significant heterogeneity within GDP groups.** Individual country trajectories vary even within the same quintile.

---

## Issues / Incomplete Code

- `norm_life_exp` variable was commented out but later referenced, causing a `NameError`.
- The overweight prevalence dataset was downloaded but never used.
- Several cells contain only commented-out code.
- `count.csv` is loaded near the end but not meaningfully integrated.

