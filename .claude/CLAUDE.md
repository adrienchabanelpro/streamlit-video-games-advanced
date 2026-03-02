# Video Game Sales Prediction — Streamlit App

## Quick Reference

- **Run:** `streamlit run source/main.py` → http://localhost:8501
- **Language:** UI in French, docs in English, code mixed
- **Python:** 3.11+ required

## Architecture

- `source/main.py` — Entry point, sidebar nav routing to 11 pages
- `source/config.py` — Paths, constants, Plotly layout
- `source/style.py` — CSS injection (modern dark slate theme, Inter + JetBrains Mono)
- `source/components.py` — Shared UI components (metric_card, info_card, etc.)
- `source/pages/` — 11 Streamlit page modules
- `source/ml/predict.py` — Inference pipeline (loads models + transformers)
- `source/analyse_avis_utilisateurs.py` — NLP sentiment analysis
- `scripts/training/` — Modular v3 training pipeline (data_prep, models, stacking, evaluation)
- `scripts/data_collection/` — 5-source collection (RAWG, IGDB, HLTB, SteamSpy, Kaggle) + merge

## Pages (11)

| Page | File | Content |
|------|------|---------|
| Accueil | `home.py` | Dashboard overview, key metrics, pipeline diagram |
| Sources de Donnees | `data_sources.py` | 5 sources documented, merge methodology, schema |
| Analyse Exploratoire | `dataviz.py` | Interactive Plotly charts with global filters |
| Feature Engineering | `feature_engineering.py` | Feature explanations |
| Entrainement | `model_training.py` | Model comparison, stacking architecture, SHAP |
| Predictions | `prediction.py` | Single + batch prediction UI |
| Interpretabilite | `interpretability.py` | SHAP beeswarm, feature descriptions |
| What-If | `what_if.py` | Interactive variable sweep analysis |
| Tendances | `market_insights.py` | Genre/platform/publisher analytics |
| Sentiment NLP | `perception.py` | DistilBERT sentiment analysis |
| A Propos | `about.py` | Methodology, tech stack, limitations |

## Data & Models

- `data/Ventes_jeux_video_v3.csv` — Unified dataset (5 sources merged)
- `data/Ventes_jeux_video_final.csv` — v2 fallback (64K rows, VGChartz + SteamSpy)
- `models/model_v3_*.{txt,json,cbm,joblib}` — v3 stacking ensemble (5 base + meta-learner)
- `models/model_v2_*.{txt,json,cbm}` — v2 models (LGB + XGB + CB average)
- `reports/training_log_v3.json` — v3 training metadata + metrics

## Key Conventions

- Streamlit CSS via `components.html()` JS injection (bypasses sanitizer)
- Models: `joblib.load()` for sklearn, `lgb.Booster(model_file=...)` for LightGBM
- Plotly for interactive charts (dark theme)
- `@st.cache_data` for data loading, `@st.cache_resource` for model loading
- See `IMPROVEMENT.md` for full roadmap
