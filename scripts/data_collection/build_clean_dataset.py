"""Build a clean, quality-filtered dataset from the merged v3 data.

Applies quality tiers, filters out zero-sales rows, and produces a
training-ready dataset with documented provenance.

Input:  data/Ventes_jeux_video_v3.csv  (raw merge, ~64K rows)
Output: data/Ventes_jeux_video_clean.csv  (~17K rows, quality-filtered)
        reports/data_quality_report.json  (audit trail)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

INPUT_PATH = DATA_DIR / "Ventes_jeux_video_v3.csv"
OUTPUT_PATH = DATA_DIR / "Ventes_jeux_video_clean.csv"
REPORT_PATH = REPORTS_DIR / "data_quality_report.json"


def assign_quality_tier(row: pd.Series) -> str:
    """Assign a data quality tier based on available sales evidence."""
    has_vgchartz = row.get("Global_Sales", 0) > 0
    has_wiki = pd.notna(row.get("wiki_sales_millions"))
    steam_owners = row.get("steam_owners_midpoint", 0)
    has_steam = pd.notna(steam_owners) and steam_owners > 0

    if has_wiki and has_vgchartz:
        return "tier_1_verified"
    if has_vgchartz and row["Global_Sales"] >= 0.1:
        return "tier_2_physical"
    if has_vgchartz and row["Global_Sales"] > 0:
        return "tier_3_marginal"
    if has_steam and steam_owners > 100_000:
        return "tier_4_digital_only"
    return "tier_5_no_sales"


def compute_sales_estimate(row: pd.Series) -> tuple[float, str]:
    """Compute best available sales estimate with provenance.

    Returns (estimate_in_millions, provenance_string).
    """
    wiki = row.get("wiki_sales_millions")
    if pd.notna(wiki) and wiki > 0:
        return float(wiki), "wikipedia_verified"

    vgchartz = row.get("Global_Sales", 0)
    if vgchartz > 0:
        return float(vgchartz), "vgchartz_physical"

    return 0.0, "no_sales_data"


def build_clean_dataset(
    min_tier: str = "tier_3_marginal",
    force: bool = False,
) -> Path:
    """Build a quality-filtered dataset.

    Parameters
    ----------
    min_tier:
        Minimum quality tier to include. Default keeps tiers 1-3
        (all rows with non-zero VGChartz physical sales).
    force:
        Overwrite output even if it exists.
    """
    REPORTS_DIR.mkdir(exist_ok=True)

    if OUTPUT_PATH.exists() and not force:
        print(f"[clean] Already exists: {OUTPUT_PATH} (use --force)")
        return OUTPUT_PATH

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Merged v3 dataset not found at {INPUT_PATH}")

    # Load
    df = pd.read_csv(INPUT_PATH)
    original_count = len(df)
    print(f"[clean] Loaded {original_count:,} rows, {len(df.columns)} columns")

    # ── Step 1: Assign quality tiers ──
    df["quality_tier"] = df.apply(assign_quality_tier, axis=1)
    tier_counts = df["quality_tier"].value_counts().sort_index()
    print("\n[clean] Quality tier distribution:")
    for tier, count in tier_counts.items():
        print(f"  {tier}: {count:,} ({count/len(df)*100:.1f}%)")

    # ── Step 2: Build sales estimate + provenance ──
    results = df.apply(compute_sales_estimate, axis=1, result_type="expand")
    df["sales_estimate"] = results[0]
    df["sales_provenance"] = results[1]

    provenance_counts = df["sales_provenance"].value_counts()
    print("\n[clean] Sales provenance:")
    for prov, count in provenance_counts.items():
        print(f"  {prov}: {count:,}")

    # ── Step 3: Add binary flags ──
    df["has_verified_sales"] = (
        df["wiki_sales_millions"].notna() & (df["wiki_sales_millions"] > 0)
    ).astype(int) if "wiki_sales_millions" in df.columns else 0

    # ── Step 4: Basic validation filters ──
    before_filter = len(df)
    df = df[df["Year"].notna()]
    df = df[df["Year"].between(1980, 2024)]
    df = df[df["Publisher"].notna()]
    df = df[df["Genre"].notna()]
    print(f"\n[clean] Validation filters: {before_filter:,} → {len(df):,} rows")

    # ── Step 5: Quality filter ──
    tier_order = [
        "tier_1_verified", "tier_2_physical", "tier_3_marginal",
        "tier_4_digital_only", "tier_5_no_sales",
    ]
    min_idx = tier_order.index(min_tier)
    allowed_tiers = tier_order[:min_idx + 1]

    df_clean = df[df["quality_tier"].isin(allowed_tiers)].copy()
    print(f"[clean] Quality filter (>= {min_tier}): {len(df):,} → {len(df_clean):,} rows")

    # ── Step 6: Feature coverage report ──
    coverage = {}
    coverage_cols = {
        "SteamSpy": "steam_owners_midpoint",
        "RAWG": "rawg_rating",
        "IGDB": "igdb_total_rating",
        "HLTB": "hltb_main",
        "OpenCritic": "oc_top_critic_score",
        "Wikipedia": "wiki_sales_millions",
        "Steam Store": "steam_store_price_usd",
        "meta_score": "meta_score",
    }
    print("\n[clean] Feature coverage in filtered dataset:")
    for name, col in coverage_cols.items():
        if col in df_clean.columns:
            valid = df_clean[col].notna().sum()
            if col in ("steam_owners_midpoint", "hltb_main", "oc_top_critic_score"):
                valid = (pd.to_numeric(df_clean[col], errors="coerce") > 0).sum()
            pct = valid / len(df_clean) * 100
            coverage[name] = {"count": int(valid), "pct": round(pct, 1)}
            print(f"  {name}: {valid:,} ({pct:.1f}%)")

    # ── Step 7: Sales distribution in clean dataset ──
    sales = df_clean["Global_Sales"]
    print("\n[clean] Sales distribution (Global_Sales):")
    print(f"  Mean: {sales.mean():.3f}M")
    print(f"  Median: {sales.median():.3f}M")
    print(f"  Min: {sales.min():.3f}M, Max: {sales.max():.3f}M")
    print(f"  Zero: {(sales == 0).sum()}")

    # ── Step 8: Save ──
    df_clean = df_clean.sort_values("Global_Sales", ascending=False).reset_index(drop=True)
    df_clean["Rank"] = range(1, len(df_clean) + 1)

    df_clean.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[clean] Saved {len(df_clean):,} rows → {OUTPUT_PATH}")

    # ── Step 9: Quality report ──
    report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(INPUT_PATH.name),
        "input_rows": original_count,
        "output_rows": len(df_clean),
        "min_quality_tier": min_tier,
        "tier_distribution": {
            tier: int(tier_counts.get(tier, 0)) for tier in tier_order
        },
        "filtered_tier_distribution": df_clean["quality_tier"].value_counts().to_dict(),
        "provenance_distribution": df_clean["sales_provenance"].value_counts().to_dict(),
        "sales_stats": {
            "mean": round(float(sales.mean()), 4),
            "median": round(float(sales.median()), 4),
            "std": round(float(sales.std()), 4),
            "min": round(float(sales.min()), 4),
            "max": round(float(sales.max()), 4),
        },
        "feature_coverage": coverage,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[clean] Quality report → {REPORT_PATH}")

    return OUTPUT_PATH


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build clean dataset from v3 merge")
    parser.add_argument(
        "--min-tier", default="tier_3_marginal",
        choices=[
            "tier_1_verified", "tier_2_physical", "tier_3_marginal",
            "tier_4_digital_only", "tier_5_no_sales",
        ],
        help="Minimum quality tier to include (default: tier_3_marginal)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    args = parser.parse_args()

    build_clean_dataset(min_tier=args.min_tier, force=args.force)
