# GDP, Obesity & Life Expectancy — Research Data and Visualizations

Cross-country analysis of the relationship between GDP per capita, obesity prevalence, and life expectancy (1980–2015). Countries are grouped into GDP quintiles; group-level averages are weighted by population.

## Repository Contents

| File / Folder | Description |
|---|---|
| `visualize_all_countries.py` | Main script — downloads data, produces pairplots, scatter plots per country and per GDP group |
| `visualize_ci.py` | Confidence-interval script — produces CI charts, median charts, individual country plots, and CSV tables |
| `methodology.md` | Plain-English description of every data-preparation step and chart (for researcher verification) |
| `requirements.txt` | Python dependencies |
| `figures/` | Output folder created automatically when scripts run |

## Setup

Requires **Python 3.10+**.

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the Scripts

The two scripts are independent and can be run in any order. Both download the source CSV files automatically on first run.

### Script 1 — Main visualizations

```bash
python visualize_all_countries.py
```

Produces ~9 sets of figures under `figures/`: pairplots per country and per group, obesity-vs-life-expectancy scatters, GDP-vs-life-expectancy scatters (individual countries and grouped).

### Script 2 — Confidence intervals and medians

```bash
python visualize_ci.py
```

Produces figures under `figures/ci_all_groups/`, `figures/median_all_groups/`, `figures/ci_country_scatter/`, and CSV tables under `figures/ci_tables/`. Repeats the analysis for four GDP-grouping years (1990, 1997, 2005, 2013).
