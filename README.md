# Player Market Value Prediction

Applied Data Science capstone project: a supervised machine-learning application that estimates professional football player market value from historical player profile, performance, competition, and valuation data.

## Approved project direction

- Use a Transfermarkt-derived public dataset as the primary source.
- Study the five major European leagues across the available historical window, expected to include 2025-26 if the required records are complete.
- Create one modeling observation for a player at a valuation snapshot.
- Use information available before the snapshot to predict the recorded market value at that snapshot.
- Train and evaluate the model with a time-aware split.
- Compare a baseline, Elastic Net, and Random Forest models.
- Build a Streamlit application with known-player search and manual or what-if inputs.
- Include model explanations and document limitations.
- Treat the LLM scouting report as a stretch goal after the core ML and UI work is complete.

## Repository purpose

This repository is the technical workspace for code, notebooks, documentation, and reproducible project files.

## Folder guide

| Folder | Purpose |
|---|---|
| `data/raw/` | Original downloaded data. Kept out of Git unless we deliberately decide otherwise. |
| `data/processed/` | Cleaned extracts used for modeling. Large generated files stay out of Git. |
| `notebooks/` | Exploratory analysis and documented experiments. |
| `src/` | Reusable Python code for loading, cleaning, feature engineering, training, and evaluation. |
| `app/` | Streamlit application code. |
| `models/` | Saved preprocessing and model artifacts. |
| `reports/` | Figures, tables, and written analysis outputs. |
| `docs/` | Data dictionary, decisions, setup notes, and project documentation. |
| `tests/` | Small checks for reusable code as it develops. |

## Learning rules for this project

1. Before coding, write down the question or hypothesis the work should answer.
2. Use notebooks for investigation and explanation; move repeated or reusable logic into `src/`.
3. Keep a short record of important decisions, assumptions, and rejected alternatives.
4. Make small Git commits with messages that explain the change.
5. Never commit passwords, API keys, `.env` files, or private credentials.
6. Do not trust a metric until we understand the split, target alignment, leakage risks, and business meaning.

## Planned setup

The initial environment will use Python with the packages listed in `requirements.txt`. Exact package versions will be recorded after the working environment is created and tested.

## Current status

Repository scaffold created. The next learning milestone is to create the environment, record the Python and package versions, and inspect the source data before writing modeling code.
