"""Data Sources page: document all 9 sources, API procedures, merge methodology, schema.

This page serves as comprehensive technical documentation explaining how the
multi-source dataset was built — from raw API calls to the final merged CSV.
It covers the rationale behind each source choice, the collection methodology,
authentication procedures, the fuzzy-matching merge strategy, and known limitations.
"""

import pandas as pd
import streamlit as st
from components import info_card, metric_card, pipeline_step, section_header, source_card
from config import DATA_DIR, ROOT


@st.cache_data
def _load_dataset_info() -> dict:
    """Load dataset for schema display."""
    for name in ["Ventes_jeux_video_v3.csv", "Ventes_jeux_video_final.csv"]:
        path = DATA_DIR / name
        if path.exists():
            df = pd.read_csv(path, nrows=5)
            with open(path) as f:
                row_count = sum(1 for _ in f) - 1
            return {"df_sample": df, "rows": row_count, "cols": len(df.columns), "name": name}
    return {"df_sample": pd.DataFrame(), "rows": 0, "cols": 0, "name": "N/A"}


@st.cache_data
def _load_raw_stats() -> list[dict]:
    """Load row counts and file sizes for each raw data source."""
    raw_dir = ROOT / "data" / "raw"
    sources = [
        ("VGChartz", "vgchartz_2024.csv"),
        ("SteamSpy", "steamspy_all.csv"),
        ("RAWG", "rawg_all.csv"),
        ("IGDB", "igdb_all.csv"),
        ("Wikipedia", "wikipedia_sales.csv"),
        ("OpenCritic", "opencritic.csv"),
        ("HLTB", "hltb_all.csv"),
        ("Steam Store", "steam_store.csv"),
        ("Gamedatacrunch", "gamedatacrunch.csv"),
    ]
    stats = []
    for label, filename in sources:
        path = raw_dir / filename
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            with open(path) as f:
                rows = sum(1 for _ in f) - 1
            stats.append({
                "Source": label,
                "File": filename,
                "Rows": f"{rows:,}",
                "Size": f"{size_mb:.1f} MB",
                "Status": "Collected",
            })
        else:
            stats.append({
                "Source": label,
                "File": filename,
                "Rows": "—",
                "Size": "—",
                "Status": "Not collected",
            })
    return stats


def data_sources_page() -> None:
    """Render the Data Sources documentation page."""
    st.title("Data Sources")
    st.caption(
        "Complete documentation of the 9 data sources, collection methodology, "
        "and merge strategy used to build the unified dataset"
    )

    info = _load_dataset_info()

    # Overview metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Games", f"{info['rows']:,}", icon="🎮")
    with c2:
        metric_card("Columns", info["cols"], icon="📋")
    with c3:
        metric_card("Sources", "9", icon="🔗")
    with c4:
        metric_card("Reliability Tiers", "4", icon="🏅")

    st.divider()

    # --------------------------------------------------------------------------
    # Why Multiple Sources?
    # --------------------------------------------------------------------------
    section_header(
        "Why Multiple Sources?",
        "The challenge of building a comprehensive video game dataset",
    )

    info_card(
        "The Problem: No Single Complete Source Exists",
        """
        <p>No single public database captures the full picture of video game sales
        and metadata. Each source has strengths and blind spots:</p>
        <ul style="margin:8px 0;padding-left:20px;line-height:1.7">
            <li><b>VGChartz</b> tracks physical retail sales — but digital sales
            (70%+ of modern revenue) are missing entirely</li>
            <li><b>SteamSpy</b> estimates Steam ownership — but only covers PC,
            and ownership ≠ sales (bundles, free games)</li>
            <li><b>RAWG / IGDB</b> have excellent metadata — but no sales data</li>
            <li><b>Wikipedia</b> has publisher-verified figures — but only for
            ~800 best-selling titles</li>
        </ul>
        <p><b>Our approach:</b> Combine 9 complementary sources using fuzzy name
        matching to create a unified dataset with both sales data and rich
        metadata (genres, themes, completion times, critic scores, pricing).
        This multi-source strategy improves feature diversity for the ML
        models while maintaining data quality through a tiered reliability
        framework.</p>
        """,
    )

    info_card(
        "Physical vs. Digital Sales — A Critical Distinction",
        """
        <p>Understanding the sales landscape is essential for interpreting our data:</p>
        <table style="width:100%;border-collapse:collapse;margin:8px 0">
            <tr style="border-bottom:1px solid #334155">
                <th style="text-align:left;padding:6px;color:#94A3B8">Type</th>
                <th style="text-align:left;padding:6px;color:#94A3B8">Sources</th>
                <th style="text-align:left;padding:6px;color:#94A3B8">Coverage</th>
            </tr>
            <tr style="border-bottom:1px solid #1E293B">
                <td style="padding:6px"><b>Physical</b></td>
                <td style="padding:6px">VGChartz</td>
                <td style="padding:6px">Retail store sales (cartridges, discs)</td>
            </tr>
            <tr style="border-bottom:1px solid #1E293B">
                <td style="padding:6px"><b>Digital estimates</b></td>
                <td style="padding:6px">SteamSpy, Gamedatacrunch</td>
                <td style="padding:6px">Steam ownership/revenue (PC only)</td>
            </tr>
            <tr style="border-bottom:1px solid #1E293B">
                <td style="padding:6px"><b>Combined/verified</b></td>
                <td style="padding:6px">Wikipedia</td>
                <td style="padding:6px">Publisher-confirmed totals (best-sellers only)</td>
            </tr>
        </table>
        <p style="margin-top:8px;color:#94A3B8;font-size:0.85rem">
        <b>Note:</b> Our target variable (Global_Sales) comes from VGChartz
        (physical sales). We use digital metrics as <i>features</i> that correlate
        with physical sales, not as direct sales measurements.</p>
        """,
    )

    st.divider()

    # --------------------------------------------------------------------------
    # Source Reliability Framework
    # --------------------------------------------------------------------------
    section_header(
        "Source Reliability Framework",
        "Each source is classified by data reliability tier, "
        "used for conflict resolution during merge",
    )

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        info_card(
            "Tier 1 — Official",
            "<b>Wikipedia</b><br>Verified publisher figures, NPD/GfK reports. "
            "Highest confidence for sales numbers.",
            accent="#10B981",
        )
    with t2:
        info_card(
            "Tier 2 — API",
            "<b>RAWG, IGDB, OpenCritic, Steam Store</b><br>"
            "Structured APIs with versioned data. High reliability for metadata.",
            accent="#3B82F6",
        )
    with t3:
        info_card(
            "Tier 3 — Estimates",
            "<b>SteamSpy, Gamedatacrunch</b><br>"
            "Algorithmic estimates from public signals. Good directional data.",
            accent="#F59E0B",
        )
    with t4:
        info_card(
            "Tier 4 — Compiled",
            "<b>VGChartz (Kaggle)</b><br>"
            "Community-compiled physical sales. Our base dataset (64K games).",
            accent="#8B5CF6",
        )

    st.divider()

    # --------------------------------------------------------------------------
    # Primary Sources
    # --------------------------------------------------------------------------
    section_header(
        "Primary Sources",
        "The base dataset and primary sales/engagement data",
    )

    source_card(
        name="VGChartz (Kaggle) — Base Dataset",
        description=(
            "Community-compiled physical video game sales spanning 1980–2024. "
            "Covers all major platforms (PS, Xbox, Nintendo, PC). "
            "Provides the **target variable** (Global_Sales) and regional breakdowns. "
            "Downloaded as a static CSV from Kaggle — no API key required.\n\n"
            "**Collection:** `scripts/data_collection/download_kaggle.py` downloads the CSV "
            "from Kaggle Datasets using the kaggle CLI or direct HTTP.\n\n"
            "**Limitation:** Physical sales only. Does not capture digital distribution "
            "(Steam, PSN, Xbox Store), which now accounts for 70%+ of total game revenue."
        ),
        row_count="64,000+",
        fields="Name, Platform, Year, Genre, Publisher, Global_Sales, "
        "NA_Sales, EU_Sales, JP_Sales, Other_Sales, meta_score",
        url="https://www.kaggle.com/datasets/asaniczka/video-game-sales-2024",
    )

    c1, c2 = st.columns(2)
    with c1:
        source_card(
            name="Wikipedia — Verified Official Sales",
            description=(
                "Scrapes 13 Wikipedia best-selling game lists using the MediaWiki "
                "Parse API. These contain **publisher-confirmed** sales figures — "
                "the most reliable sales data available.\n\n"
                "**Pages scraped:** Best-selling games of all time, plus per-platform "
                "lists (Switch, PS4, PS5, Xbox One, Wii, Wii U, Game Boy, DS, 3DS, "
                "PS3, PS2, Xbox 360).\n\n"
                "**API:** `https://en.wikipedia.org/w/api.php` (free, no key). "
                "Requires proper User-Agent header per Wikipedia policy.\n\n"
                "**Collection:** `scripts/data_collection/collect_wikipedia.py` — "
                "parses HTML tables, extracts sales numbers (handles '30 million', "
                "'30,000,000' formats), deduplicates keeping highest sales per game."
            ),
            row_count="~800",
            fields="wiki_name, wiki_sales_millions, wiki_platform, "
            "wiki_publisher, wiki_developer, wiki_release_date, wiki_sales_type",
            url="https://en.wikipedia.org/wiki/List_of_best-selling_video_games",
            accent="#10B981",
        )
    with c2:
        source_card(
            name="SteamSpy — Digital PC Estimates",
            description=(
                "Provides estimated owner counts, review ratios, playtime, and "
                "pricing for Steam games. Uses Steam's public API signals to "
                "reverse-engineer ownership ranges.\n\n"
                "**API:** `https://steamspy.com/api.php` (free, no key). "
                "Rate limited — collector uses 2s delays between pages.\n\n"
                "**Collection:** `scripts/data_collection/collect_steamspy.py` — "
                "paginated collection sorted by owners. Each page returns ~1000 games. "
                "Progress saved to disk for resumability.\n\n"
                "**Limitation:** Estimates only (not exact). Ownership ≠ sales "
                "(free games, bundles inflate numbers). PC/Steam only."
            ),
            row_count="60,000+",
            fields="appid, name, owners, owners_midpoint, positive, negative, "
            "review_pct, average_forever, median_forever, price, ccu, tags",
            url="https://steamspy.com",
            accent="#8B5CF6",
        )

    st.divider()

    # --------------------------------------------------------------------------
    # Metadata Sources
    # --------------------------------------------------------------------------
    section_header(
        "Metadata Sources",
        "Rich game metadata: ratings, genres, themes, completion times",
    )

    c1, c2 = st.columns(2)
    with c1:
        source_card(
            name="RAWG API — Game Metadata",
            description=(
                "The largest open video game database. Provides Metacritic scores, "
                "average playtime, ESRB ratings, genres, tags, platform availability, "
                "developers, and publishers.\n\n"
                "**API:** `https://api.rawg.io/api` — requires a free API key "
                "(register at rawg.io/apidocs). 20,000 requests/month.\n\n"
                "**Collection:** `scripts/data_collection/collect_rawg.py` — "
                "paginated (40 games/page), sorted by relevance. Extracts top-5 tags, "
                "developer/publisher names, ESRB rating. Resumable.\n\n"
                "**Key value:** Metacritic scores, ESRB ratings, and structured "
                "genre/tag taxonomy used for feature engineering."
            ),
            row_count="500,000+",
            fields="rawg_id, rawg_name, rawg_metacritic, rawg_rating, "
            "rawg_playtime, rawg_esrb, rawg_genres, rawg_tags_top5, "
            "rawg_platforms, rawg_developers, rawg_publishers",
            url="https://rawg.io/apidocs",
            accent="#10B981",
        )
    with c2:
        source_card(
            name="IGDB / Twitch API — Themes & Franchises",
            description=(
                "Owned by Twitch/Amazon. Provides unique metadata not available "
                "elsewhere: **themes** (horror, sci-fi, survival), **game modes** "
                "(single-player, co-op, MMO), **player perspectives** (first-person, "
                "isometric), **franchises**, and pre-release **hype counts**.\n\n"
                "**Auth:** OAuth2 client_credentials flow via Twitch. Register a "
                "Twitch app at dev.twitch.tv, get Client ID + Secret, exchange for "
                "a Bearer token (auto-handled by our pipeline).\n\n"
                "**API:** `https://api.igdb.com/v4/games` — POST with Apicalypse "
                "query language. 4 requests/second limit.\n\n"
                "**Collection:** `scripts/data_collection/collect_igdb.py` — "
                "batch of 500 games per request, sorted by ID. Saves JSON batches "
                "to disk, then consolidates to CSV. Resumable."
            ),
            row_count="700,000+",
            fields="igdb_id, igdb_name, igdb_total_rating, igdb_rating_count, "
            "igdb_themes, igdb_game_modes, igdb_perspectives, igdb_franchises, "
            "igdb_hypes, igdb_follows, igdb_developers, igdb_publishers",
            url="https://api.igdb.com",
            accent="#F59E0B",
        )

    c1, c2 = st.columns(2)
    with c1:
        source_card(
            name="OpenCritic — Aggregated Critic Scores",
            description=(
                "Aggregates reviews from 100+ outlets (IGN, GameSpot, Eurogamer, etc.). "
                "More diverse than Metacritic — includes YouTube reviewers and "
                "smaller outlets. Provides a **tier system** (Mighty, Strong, Fair, Weak).\n\n"
                "**API:** `https://api.opencritic.com/api` (free, no key). "
                "Returns 20 games per page.\n\n"
                "**Collection:** `scripts/data_collection/collect_opencritic.py` — "
                "paginated by skip/offset. Optional detailed mode fetches per-game "
                "platforms, genres, and company info. Resumable.\n\n"
                "**Key value:** Independent critic consensus score, "
                "percent recommended metric, quality tier classification."
            ),
            row_count="5,000+",
            fields="oc_id, oc_name, oc_top_critic_score, oc_percent_recommended, "
            "oc_num_reviews, oc_num_top_critic_reviews, oc_tier, oc_first_release_date",
            url="https://opencritic.com",
            accent="#3B82F6",
        )
    with c2:
        source_card(
            name="HowLongToBeat — Completion Times",
            description=(
                "Community-reported game completion times. Provides four metrics: "
                "**main story**, **main + extras**, **completionist**, and "
                "**all styles** average.\n\n"
                "**API:** Web scraping via the howlongtobeatpy library. "
                "No API key needed, but rate limited.\n\n"
                "**Collection:** `scripts/data_collection/collect_hltb.py` — "
                "searches by game name, extracts completion times. Resumable.\n\n"
                "**Key value:** Game length is a strong predictor of engagement "
                "and perceived value. Short games (< 5h) vs. long RPGs (50h+) "
                "have very different sales patterns."
            ),
            row_count="~10,000",
            fields="hltb_name, hltb_main, hltb_main_extra, "
            "hltb_completionist, hltb_all_styles",
            url="https://howlongtobeat.com",
            accent="#EF4444",
        )

    st.divider()

    # --------------------------------------------------------------------------
    # Digital Analytics Sources
    # --------------------------------------------------------------------------
    section_header(
        "Digital Analytics Sources",
        "Steam-specific pricing, DLC, reviews, and revenue estimates",
    )

    c1, c2 = st.columns(2)
    with c1:
        source_card(
            name="Steam Store API — Pricing & DLC",
            description=(
                "Official Steam Store API for detailed game information: exact USD "
                "pricing, free-to-play status, DLC count, store categories "
                "(single-player, co-op, achievements), genre tags, Metacritic score, "
                "platform availability (Windows/Mac/Linux), and total recommendation count.\n\n"
                "**API:** `https://store.steampowered.com/api/appdetails` (free, no key). "
                "1.5s rate limit between requests.\n\n"
                "**Collection:** `scripts/data_collection/collect_steam_store.py` — "
                "uses SteamSpy app IDs as input. Fetches details per app, filters to "
                "type='game' only. Resumable with batch saves.\n\n"
                "**Key value:** Exact pricing data, DLC ecosystem indicator, "
                "platform reach, official Metacritic integration."
            ),
            row_count="5,000+",
            fields="steam_store_appid, steam_store_price_usd, steam_store_is_free, "
            "steam_store_dlc_count, steam_store_metacritic, steam_store_categories, "
            "steam_store_genres, steam_store_recommendations",
            url="https://store.steampowered.com",
            accent="#6366F1",
        )
    with c2:
        source_card(
            name="Gamedatacrunch — Revenue Estimates",
            description=(
                "Free Steam analytics platform providing revenue estimates, "
                "peak concurrent player counts (CCU), regional pricing, review "
                "breakdowns, and tag/genre classification.\n\n"
                "**API:** `https://www.gamedatacrunch.com/api` (free, no key). "
                "Conservative 2s rate limit.\n\n"
                "**Collection:** `scripts/data_collection/collect_gamedatacrunch.py` — "
                "paginated by revenue rank. Saves progress every 10 pages. Resumable.\n\n"
                "**Status:** Site may be intermittently unavailable. "
                "Data is collected when accessible and skipped gracefully otherwise.\n\n"
                "**Key value:** Revenue estimates bridge the gap between owner counts "
                "(SteamSpy) and actual revenue, accounting for pricing and discounts."
            ),
            row_count="Variable",
            fields="gdc_appid, gdc_revenue_estimate, gdc_owners_estimate, "
            "gdc_ccu_max, gdc_price_usd, gdc_review_score, gdc_review_count, "
            "gdc_tags, gdc_genres",
            url="https://www.gamedatacrunch.com",
            accent="#EC4899",
        )

    st.divider()

    # --------------------------------------------------------------------------
    # Collection Pipeline
    # --------------------------------------------------------------------------
    section_header(
        "Collection Pipeline",
        "How the data flows from source APIs to the unified dataset",
    )

    st.markdown(
        "**Orchestrator:** `scripts/data_collection/run_pipeline.py` — "
        "runs all 9 collectors sequentially, then merges into the final dataset. "
        "Each step is **resumable** (progress saved to disk) and can be "
        "individually skipped with `--skip-<source>` flags."
    )

    st.markdown("")  # spacing

    c1, c2 = st.columns(2)
    with c1:
        pipeline_step(
            1, "Kaggle VGChartz Download",
            "Static CSV download (64K games). Provides the base dataset "
            "and target variable (Global_Sales).",
            accent="#8B5CF6",
        )
        pipeline_step(
            2, "SteamSpy API Collection",
            "Paginated REST API (60K+ games). Digital ownership estimates, "
            "pricing, reviews, playtime for Steam/PC games.",
            accent="#8B5CF6",
        )
        pipeline_step(
            3, "RAWG API Collection",
            "REST API with API key (20K games/run). Metacritic scores, "
            "ESRB ratings, genres, tags, platform lists.",
            accent="#3B82F6",
        )
        pipeline_step(
            4, "IGDB / Twitch API Collection",
            "OAuth2 authenticated POST API (200K games). Themes, game modes, "
            "perspectives, franchises, hype counts.",
            accent="#3B82F6",
        )
        pipeline_step(
            5, "HowLongToBeat Scraping",
            "Web scraping via howlongtobeatpy. Searches by game name for "
            "completion times (main story, completionist, etc.).",
            accent="#3B82F6",
        )
    with c2:
        pipeline_step(
            6, "Wikipedia Sales Scraping",
            "MediaWiki Parse API (13 best-selling lists). Extracts "
            "publisher-verified sales figures from HTML tables.",
            accent="#10B981",
        )
        pipeline_step(
            7, "Steam Store API Collection",
            "Public REST API. Fetches pricing, DLC counts, categories, "
            "Metacritic scores, platform availability per app ID.",
            accent="#3B82F6",
        )
        pipeline_step(
            8, "OpenCritic API Collection",
            "Public REST API (5K games). Aggregated critic scores from "
            "100+ outlets, quality tier (Mighty/Strong/Fair/Weak).",
            accent="#3B82F6",
        )
        pipeline_step(
            9, "Gamedatacrunch Collection",
            "Public REST API. Revenue estimates, peak concurrent users, "
            "review breakdowns. Site may be intermittently unavailable.",
            accent="#F59E0B",
        )
        pipeline_step(
            10, "Fuzzy-Match Merge",
            "Exact + fuzzy name matching (rapidfuzz WRatio >= 85%) across "
            "all sources. Computes derived features. Outputs unified CSV.",
            accent="#EF4444",
        )

    st.code(
        "# Run the full pipeline\n"
        "python scripts/data_collection/run_pipeline.py\n\n"
        "# Skip specific sources\n"
        "python scripts/data_collection/run_pipeline.py --skip-igdb --skip-hltb\n\n"
        "# Force re-collection of all sources\n"
        "python scripts/data_collection/run_pipeline.py --force",
        language="bash",
    )

    st.divider()

    # --------------------------------------------------------------------------
    # Raw Data Inventory
    # --------------------------------------------------------------------------
    section_header(
        "Raw Data Inventory",
        "Current state of collected data files on disk",
    )

    raw_stats = _load_raw_stats()
    st.dataframe(
        pd.DataFrame(raw_stats),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(width="small"),
        },
    )

    st.divider()

    # --------------------------------------------------------------------------
    # Merge Methodology
    # --------------------------------------------------------------------------
    section_header("Merge Methodology", "How 9 sources are unified into one dataset")

    info_card(
        "Matching Strategy",
        """
        <ol style="margin:0;padding-left:20px;line-height:1.8">
            <li><b>Name Normalization</b>: lowercase, strip punctuation,
            remove edition suffixes (Remastered, GOTY, Deluxe, Complete Edition...)
            and leading articles (The, A, An)</li>
            <li><b>Exact Match</b>: normalized name lookup (O(1) hash map)</li>
            <li><b>Fuzzy Match</b>: rapidfuzz WRatio with 85% threshold
            for remaining unmatched names (handles typos, regional name differences)</li>
            <li><b>Match Score Tracking</b>: every source match preserves its
            confidence score (0-100) for quality auditing</li>
            <li><b>Conflict Resolution</b>: when sources disagree,
            higher-tier data wins (Wikipedia &gt; API &gt; estimates)</li>
        </ol>
        """,
    )

    info_card(
        "Derived Features",
        """
        <p>After merging, the pipeline computes additional features:</p>
        <ul style="margin:0;padding-left:20px;line-height:1.6">
            <li><b>cross_platform_count</b> — number of platforms per game</li>
            <li><b>is_multi_platform</b> — binary flag (>1 platform)</li>
            <li><b>release_month/quarter/day_of_week</b> — from RAWG release dates</li>
            <li><b>esrb_encoded</b> — ordinal encoding of ESRB rating</li>
            <li><b>has_franchise</b> — from IGDB franchise data</li>
            <li><b>is_remake / is_remaster</b> — from IGDB game category</li>
            <li><b>price_tier</b> — free / indie / standard / premium / deluxe</li>
            <li><b>critic_score_combined</b> — OpenCritic preferred, Metacritic fallback</li>
            <li><b>has_verified_sales</b> — Wikipedia-confirmed sales figure exists</li>
            <li><b>has_dlc</b> — game has DLC on Steam Store</li>
        </ul>
        """,
    )

    st.divider()

    # --------------------------------------------------------------------------
    # API Keys & Authentication
    # --------------------------------------------------------------------------
    section_header(
        "API Keys & Authentication",
        "Required credentials for running the collection pipeline",
    )

    auth_data = [
        {
            "Source": "VGChartz (Kaggle)",
            "Auth": "None (static CSV)",
            "Cost": "Free",
            "Rate Limit": "N/A",
        },
        {
            "Source": "SteamSpy",
            "Auth": "None",
            "Cost": "Free",
            "Rate Limit": "~1 req/2s",
        },
        {
            "Source": "RAWG",
            "Auth": "API Key (RAWG_API_KEY)",
            "Cost": "Free (20K req/month)",
            "Rate Limit": "~5 req/s",
        },
        {
            "Source": "IGDB / Twitch",
            "Auth": "OAuth2 (TWITCH_CLIENT_ID + SECRET)",
            "Cost": "Free",
            "Rate Limit": "4 req/s",
        },
        {
            "Source": "HowLongToBeat",
            "Auth": "None (web scraping)",
            "Cost": "Free",
            "Rate Limit": "~1 req/s",
        },
        {
            "Source": "Wikipedia",
            "Auth": "None (User-Agent required)",
            "Cost": "Free",
            "Rate Limit": "~1 req/s",
        },
        {
            "Source": "Steam Store",
            "Auth": "None",
            "Cost": "Free",
            "Rate Limit": "~1 req/1.5s",
        },
        {
            "Source": "OpenCritic",
            "Auth": "None",
            "Cost": "Free",
            "Rate Limit": "~1 req/s",
        },
        {
            "Source": "Gamedatacrunch",
            "Auth": "None",
            "Cost": "Free",
            "Rate Limit": "~1 req/2s",
        },
    ]
    st.dataframe(
        pd.DataFrame(auth_data),
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "**Setup:** Copy `.env.example` to `.env` and fill in your RAWG API key and "
        "Twitch Client ID/Secret. All other sources require no authentication.",
        icon="🔑",
    )

    st.divider()

    # --------------------------------------------------------------------------
    # IGDB OAuth2 Authentication (detailed)
    # --------------------------------------------------------------------------
    with st.expander("IGDB / Twitch OAuth2 — How It Works"):
        st.markdown(
            """
**IGDB** is owned by Twitch (Amazon) and requires OAuth2 authentication.
Here is the full flow our pipeline uses:

1. **Register a Twitch app** at [dev.twitch.tv/console](https://dev.twitch.tv/console)
   — this gives you a `Client ID` and `Client Secret`
2. **Exchange credentials for a Bearer token** via the
   `client_credentials` OAuth2 grant:
   ```
   POST https://id.twitch.tv/oauth2/token
   ?client_id=YOUR_CLIENT_ID
   &client_secret=YOUR_CLIENT_SECRET
   &grant_type=client_credentials
   ```
3. **Use the Bearer token** in every IGDB API request:
   ```
   POST https://api.igdb.com/v4/games
   Headers: Client-ID: YOUR_CLIENT_ID
            Authorization: Bearer YOUR_TOKEN
   Body: fields name,total_rating,...; limit 500; offset 0;
   ```
4. Tokens last ~60 days. Our `api_config.py` obtains a fresh token
   each time the pipeline runs — no manual refresh needed.

**Rate limit:** 4 requests/second. Our collector uses 0.25s sleep between
requests to stay within limits.

**Query language:** IGDB uses "Apicalypse" — a POST body syntax
(not URL params) that supports filtering, sorting, and field selection.
            """
        )

    st.divider()

    # --------------------------------------------------------------------------
    # Schema
    # --------------------------------------------------------------------------
    section_header("Dataset Schema", f"File: {info['name']}")

    if not info["df_sample"].empty:
        schema_data = []
        for col in info["df_sample"].columns:
            dtype = str(info["df_sample"][col].dtype)
            source = _infer_source(col)
            schema_data.append({"Column": col, "Type": dtype, "Source": source})

        st.dataframe(
            pd.DataFrame(schema_data),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Data preview (first 5 rows)"):
            st.dataframe(info["df_sample"], use_container_width=True, hide_index=True)

    st.divider()

    # --------------------------------------------------------------------------
    # Limitations & Known Issues
    # --------------------------------------------------------------------------
    section_header(
        "Limitations & Known Issues",
        "Transparency about what this dataset can and cannot tell us",
    )

    info_card(
        "Data Limitations",
        """
        <ul style="margin:0;padding-left:20px;line-height:1.8">
            <li><b>Physical sales bias:</b> Our target variable (Global_Sales)
            only covers physical retail sales. Digital-only games (many indie
            titles) have Global_Sales = 0 despite potentially millions of
            digital copies sold.</li>
            <li><b>Temporal coverage:</b> VGChartz data is strongest for
            2000–2020. Older titles (pre-2000) have sparser coverage, and
            very recent titles may not yet have final sales tallied.</li>
            <li><b>Platform asymmetry:</b> PC games are well-covered by
            SteamSpy and Steam Store data, but console-only titles lack
            equivalent digital metrics.</li>
            <li><b>Fuzzy matching imprecision:</b> Games with very similar
            names (e.g., "FIFA 18" vs "FIFA 19") may be incorrectly matched.
            The 85% threshold balances recall vs. precision.</li>
            <li><b>SteamSpy ownership ranges:</b> Post-2018 Steam privacy
            changes mean SteamSpy provides ranges (e.g., "1M–2M") rather
            than exact counts. We use midpoints as estimates.</li>
            <li><b>Missing sources:</b> Some sources may not be collected
            for every run (API keys missing, sites down). The merge
            handles this gracefully — missing sources are simply skipped.</li>
        </ul>
        """,
        accent="#F59E0B",
    )

    info_card(
        "Reproducibility Notes",
        """
        <ul style="margin:0;padding-left:20px;line-height:1.8">
            <li>All collection scripts are <b>resumable</b> — if interrupted,
            they pick up where they left off via progress JSON files.</li>
            <li>Raw API responses are saved as intermediate JSON files in
            <code>data/raw/&lt;source&gt;/</code> before CSV consolidation.</li>
            <li>The merge script uses <code>random_state=42</code> where
            applicable and is fully deterministic given the same inputs.</li>
            <li>All API endpoints and collection parameters are documented
            in the scripts and in <code>.env.example</code>.</li>
        </ul>
        """,
        accent="#3B82F6",
    )


def _infer_source(col: str) -> str:
    """Infer the data source from column name prefix."""
    if col.startswith("steam_store_"):
        return "Steam Store"
    if col.startswith("steam_"):
        return "SteamSpy"
    if col.startswith("rawg_"):
        return "RAWG"
    if col.startswith("igdb_"):
        return "IGDB"
    if col.startswith("hltb_"):
        return "HLTB"
    if col.startswith("wiki_"):
        return "Wikipedia"
    if col.startswith("oc_"):
        return "OpenCritic"
    if col.startswith("gdc_"):
        return "Gamedatacrunch"
    if col in (
        "cross_platform_count", "is_multi_platform", "release_month",
        "release_quarter", "release_day_of_week", "esrb_encoded",
        "has_franchise", "is_remake", "is_remaster", "price_tier",
        "critic_score_combined", "has_verified_sales", "has_revenue_estimate",
        "has_dlc", "Rank",
    ):
        return "Derived"
    return "VGChartz"
