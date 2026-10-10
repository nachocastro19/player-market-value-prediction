# Player Market Value Prediction

Applied Data Science capstone project: a supervised machine-learning application that estimates professional football player market value from historical player profile, performance, competition, and valuation data.

## Project at a glance

Historical player-season data from 2020/21 through 2025/26 supports an expanding-window evaluation of Ridge, Random Forest, and XGBoost regressors against a previous-value baseline. Two XGBoost pipelines are used in the application: one uses a player's previous valuation, and the other provides an estimate when that value is unavailable. The held-out evaluation uses 2025/26; the production pipelines were subsequently refitted through that season for 2026/27 projections.

The Streamlit application provides player discovery, individual projections, scenario analysis, model explanations, similar-player suggestions, and player comparison. See [the report](docs/report.md) for methods, results, and limitations. The application estimates published market values, not transfer fees.

## Folder guide

| Folder | Purpose |
|---|---|
| `data/raw/` | Downloaded source CSVs, excluded from Git. |
| `data/processed/` | Modeling and inference datasets, mappings, and the generated local database. |
| `notebooks/` | EDA, modeling, production refit, and current-season data preparation. |
| `scripts/` and `sql/` | Database setup, asset preparation, and data checks. |
| `app/` | Streamlit application code. |
| `models/` | Evaluated and production model artifacts with metadata. |
| `docs/` | Report, figures, data dictionary, and entity diagrams. |
| `tests/` | Automated application and prediction checks. |
| `app/assets/club_badges/` | Club badges bundled with the app for deployment. |

## Dependency files

| File | Use it for | Includes |
|---|---|---|
| `requirements.txt` | Running or deploying the Streamlit app | Only the app's runtime dependencies. |
| `requirements-dev.txt` | Reproducing the analysis, preparing data, running notebooks, or running tests | All runtime dependencies (via `-r requirements.txt`) plus research and test tools such as DuckDB, SoccerData, Matplotlib, an IPython notebook kernel, and pytest. |

Install **one** file for your purpose. A development installation already includes the app dependencies; installing both files separately is unnecessary.

## Local setup

Validated locally with Python 3.13. Create an isolated environment:

```powershell
py -m venv .venv
```

To run or deploy the app, install only the runtime dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

The app also needs `data/processed/current_season_inference_2026_27.csv`, `models/production_metadata.json`, and both `*_production.joblib` files. These small deployment artifacts must be included when publishing the repository. Downloaded source CSVs and the generated DuckDB database are excluded from Git.

Club badges in `app/assets/club_badges/` are bundled with the app so deployment does not depend on a Git submodule. The images come from [luukhopman/football-logos](https://github.com/luukhopman/football-logos); club crests remain the property of their respective rights holders. To refresh the badges, clone or download that repository separately, then run `python scripts/prepare_club_badges.py --source PATH_TO_FOOTBALL_LOGOS/logos` and commit the updated assets.

Run the Streamlit application:

```powershell
.\.venv\Scripts\python -m streamlit run app\app.py
```

For notebooks, the database build script, and automated checks, use the development requirements instead. This command can also add the extra packages to an environment that already has the runtime dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Run the automated checks:

```powershell
.\.venv\Scripts\python -m pytest -q tests
```

The historical source CSVs are available from the [Transfermarkt-derived Kaggle dataset](https://www.kaggle.com/datasets/davidcariboo/player-scores). Place the 12 source tables in `data/raw/` before running `scripts/build_local_database.py`. Research notebooks use additional processed datasets; see their first cells for input paths. Current-season FBref data is collected separately in `notebooks/05_new_data_scraping.ipynb`, and results may change when the source website changes.
