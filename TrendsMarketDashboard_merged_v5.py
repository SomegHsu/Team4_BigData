#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trends Market Dashboard v4
Redesigned with role-based views (Platform Operator vs Seller)
Based on v3 by Isabel O'Grady & Ashwini Manokar
"""
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from openai import AzureOpenAI


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(
    page_title="Funnel Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Role card styling */
    .role-card {
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        background: white;
    }
    .role-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 8px 24px rgba(59,130,246,0.15);
        transform: translateY(-2px);
    }

    /* Signal pill styling */
    .signal-fix {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #dc2626;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-block;
    }
    .signal-scale {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #16a34a;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-block;
    }
    .signal-normal {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #64748b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-block;
    }

    /* Opportunity card */
    .opp-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin-bottom: 12px;
    }
    .opp-amount {
        font-size: 24px;
        font-weight: 700;
        font-family: 'DM Mono', monospace;
    }

    /* KPI card */
    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        font-family: 'DM Mono', monospace;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 13px;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }

    /* Health indicator */
    .health-red { color: #dc2626; font-size: 28px; }
    .health-yellow { color: #d97706; font-size: 28px; }
    .health-green { color: #16a34a; font-size: 28px; }

    /* Section header */
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #f1f5f9;
    }

    /* Back button style */
    .stButton button {
        border-radius: 8px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
    }

    /* Chat message */
    .chat-context-badge {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 13px;
        display: inline-block;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------
BASE_PATH = Path(os.getenv(
    "TRENDS_MARKET_DATA_PATH",
    "data"
))
PRODUCTS_FILE       = BASE_PATH / "dashboard_products_v2.csv"
EVENTS_FILE         = BASE_PATH / "dashboard_events.csv"
SIGNAL_SUMMARY_FILE = BASE_PATH / "dashboard_signal_summary.csv"
SIGNAL_SUMMARY_V2_FILE = BASE_PATH / "dashboard_signal_summary_v2.csv"
BRAND_FILE          = BASE_PATH / "dashboard_brand_v2.csv"
CATEGORY_FILE       = BASE_PATH / "dashboard_category_v2.csv"
SIGNAL_V2_FILE      = BASE_PATH / "dashboard_signal_summary_v2.csv"

# --------------------------------------------------
# AZURE OPENAI CONFIG
# --------------------------------------------------
# Set these in Terminal before running:
# export AZURE_OPENAI_ENDPOINT="https://student-trendsmarket-temp.openai.azure.com/"
# export AZURE_OPENAI_API_KEY="your_key_here"
# export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
# export AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT", "https://student-trendsmarket-temp.openai.azure.com/")
AZURE_API_KEY     = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT  = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# --------------------------------------------------
# SIGNAL LABEL MAPPING  (technical → plain English)
# --------------------------------------------------
SIGNAL_LABELS = {
    "Low Cart Rate — fix product page":          "Low Add-to-Cart Rate",
    "Low Direct Purchase Rate — fix visibility":  "Low Direct Purchase Rate",
    "Low Checkout Rate — fix checkout":           "Low Checkout Completion",
    "Low Overall CR — review traffic quality":    "Low Overall Conversion",
    "High Direct Purchase (Path B)":              "Strong Converter — Increase Exposure",
    "Strong Performer":                           "Strong Performer",
    "Normal":                                     "Normal",
    "Underperformer":                             "Underperformer",
    "Insufficient data":                          "Insufficient Data",
}

SIGNAL_DESCRIPTION = {
    "Low Add-to-Cart Rate":               "Users view but don't add to cart. Possible causes: product images, description quality, or pricing.",
    "Low Direct Purchase Rate":           "Users aren't purchasing directly. Possible causes: low product visibility or weak appeal.",
    "Low Checkout Completion":            "Users add to cart but don't complete purchase. Possible causes: checkout friction or shipping cost.",
    "Low Overall Conversion":             "Overall conversion is below category average. Possible causes: audience mismatch or weak product fit.",
    "Strong Converter — Increase Exposure": "These products convert well whenever users find them. Opportunity: increase exposure to grow revenue.",
    "Strong Performer":                   "Performing above category average.",
    "Normal":                             "Performing within expected range.",
    "Underperformer":                     "Below expected performance.",
    "Insufficient Data":                  "Not enough data to classify.",
}

SIGNAL_TYPE = {
    "Low Add-to-Cart Rate":               "fix",
    "Low Direct Purchase Rate":           "fix",
    "Low Checkout Completion":            "fix",
    "Low Overall Conversion":             "fix",
    "Strong Converter — Increase Exposure": "scale",
    "Strong Performer":                   "normal",
    "Normal":                             "normal",
    "Underperformer":                     "fix",
    "Insufficient Data":                  "normal",
}

SIGNAL_ICON = {
    "fix":    "🔴",
    "scale":  "🟢",
    "normal": "⚪",
}

ACTION_LABEL = {
    "fix":   "Below Category Average",
    "scale": "Strong Converters",
}


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data
def load_real_data():
    products_df       = pd.read_csv(PRODUCTS_FILE)
    events_df         = pd.read_csv(EVENTS_FILE)
    signal_summary_df = pd.read_csv(SIGNAL_SUMMARY_FILE if SIGNAL_SUMMARY_FILE.exists() else SIGNAL_SUMMARY_V2_FILE)
    brand_df          = pd.read_csv(BRAND_FILE)
    category_df       = pd.read_csv(CATEGORY_FILE)
    signal_v2_df      = pd.read_csv(SIGNAL_V2_FILE)

    if "event_time" in events_df.columns:
        events_df["event_time"] = pd.to_datetime(events_df["event_time"], utc=True, errors="coerce")

    text_cols = [
        "category_code", "cat_level_1", "cat_level_2", "brand", "signal",
        "priority_tier", "priority_focus", "recommended_actions",
        "business_hypothesis", "quadrant", "benchmark_level", "popularity_label"
    ]
    for col in text_cols:
        if col in products_df.columns:
            products_df[col] = products_df[col].fillna("Unknown")

    # Map signal to plain English label
    sig_col = "signal_v2" if "signal_v2" in products_df.columns else "signal"
    if sig_col in products_df.columns:
        products_df["signal_label"] = products_df[sig_col].map(SIGNAL_LABELS).fillna(products_df[sig_col])
    else:
        products_df["signal_label"] = "Normal"

    products_df["signal_type"] = products_df["signal_label"].map(SIGNAL_TYPE).fillna("normal")

    # Opportunity tier based on lost revenue
    if "lost_revenue_est" in products_df.columns:
        products_df["lost_revenue_est"] = pd.to_numeric(products_df["lost_revenue_est"], errors="coerce").fillna(0)
        q33 = products_df["lost_revenue_est"].quantile(0.33)
        q66 = products_df["lost_revenue_est"].quantile(0.66)
        products_df["opportunity_tier"] = products_df["lost_revenue_est"].apply(
            lambda x: "High" if x >= q66 else ("Medium" if x >= q33 else "Low")
        )

    if "category_code" in events_df.columns:
        events_df["category_code"] = events_df["category_code"].fillna("Unknown")
    if "brand" in events_df.columns:
        events_df["brand"] = events_df["brand"].fillna("Unknown")

    return products_df, events_df, signal_summary_df, brand_df, category_df, signal_v2_df


# --------------------------------------------------
# BUILD LLM CONTEXT
# --------------------------------------------------
@st.cache_data
def build_llm_context(products_df, events_df, signal_summary_df, brand_df, category_df, signal_v2_df):
    total_views     = products_df["view"].sum()
    total_purchases = products_df["purchase"].sum()
    overall_cr      = (total_purchases / total_views * 100) if total_views > 0 else 0

    cat_summary = (
        products_df.groupby("cat_level_1")
        .agg(views=("view","sum"), purchases=("purchase","sum"), products=("product_id","count"))
        .assign(conversion_rate=lambda x: (x["purchases"] / x["views"] * 100).round(2))
        .sort_values("views", ascending=False)
    )

    priority_counts = products_df["opportunity_tier"].value_counts().to_dict() if "opportunity_tier" in products_df.columns else {}

    top_products = (
        products_df[products_df.get("opportunity_tier", pd.Series()) == "High"]
        .sort_values("lost_revenue_est", ascending=False)
        .head(5)[["product_id","brand","cat_level_2","view","purchase","conversion_rate","lost_revenue_est"]]
    ) if "opportunity_tier" in products_df.columns else pd.DataFrame()

    products_summary = f"""
=== PRODUCT-LEVEL FUNNEL METRICS ===
Total Products: {len(products_df):,} | Views: {total_views:,} | Purchases: {total_purchases:,} | Overall CR: {overall_cr:.2f}%
BY CATEGORY:
{cat_summary.to_string()}
OPPORTUNITY TIERS: {priority_counts}
TOP 5 HIGH-OPPORTUNITY PRODUCTS (by lost revenue):
{top_products.to_string() if not top_products.empty else 'N/A'}
"""

    event_counts    = events_df["event_type"].value_counts().to_dict()
    unique_users    = events_df["user_id"].nunique()
    unique_products = events_df["product_id"].nunique()
    events_df["date"] = events_df["event_time"].dt.date
    top_cats = (
        events_df[events_df["category_code"] != "Unknown"]
        .groupby("category_code").size()
        .sort_values(ascending=False).head(10)
    )

    events_summary = f"""
=== RAW CLICKSTREAM EVENTS ===
Total Events: {len(events_df):,} | Unique Users: {unique_users:,} | Unique Products: {unique_products:,}
Event Types: {event_counts}
TOP 10 CATEGORIES BY VOLUME:
{top_cats.to_string()}
"""

    return f"""You have access to e-commerce funnel data from October 2019.

{products_summary}

{events_summary}

=== BRAND PERFORMANCE BY CATEGORY ===
{brand_df.to_string(index=False)}

=== CATEGORY-LEVEL FUNNEL SITUATIONS ===
{category_df.to_string(index=False)}

=== SIGNAL SUMMARY V2 ===
{signal_v2_df.to_string(index=False)}

=== SIGNAL SUMMARY (original) ===
{signal_summary_df.to_string(index=False)}
"""


# --------------------------------------------------
# LLM CHAT
# --------------------------------------------------
def ask_llm(user_question, conversation_history, full_context, role="platform", product_context="", signal_context=""):
    if not AZURE_API_KEY:
        return (
            "Azure OpenAI is not configured yet. Set `AZURE_OPENAI_API_KEY` in Terminal and rerun the app.",
            conversation_history,
        )

    client = AzureOpenAI(
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
    )

    role_instruction = (
        "You are helping a platform operator understand overall funnel performance across categories and brands."
        if role == "platform"
        else f"You are helping a seller diagnose and improve their specific product performance. {product_context}"
    )

    signal_block = f"\nCurrent signal context: {signal_context}" if signal_context else ""

    system_prompt = f"""You are an expert e-commerce conversion analyst embedded in a live dashboard.
{role_instruction}{signal_block}

Important: Our signals are data-driven observations, not definitive diagnoses.
When giving recommendations, frame them as possibilities to investigate, not certainties.
Always cite specific numbers, brands, or categories from the data. Be concise but actionable.

{full_context}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_history,
        {"role": "user", "content": user_question}
    ]

    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=messages,
            max_tokens=700
        )
        answer = response.choices[0].message.content
    except Exception as e:
        err = str(e)
        if "404" in err or "Resource not found" in err:
            answer = (
                "Azure OpenAI returned a 404 Resource not found error. "
                "This usually means the endpoint, deployment name, or API version does not match the Azure OpenAI resource.\n\n"
                f"Current settings: endpoint={AZURE_ENDPOINT}, deployment={AZURE_DEPLOYMENT}, api_version={AZURE_API_VERSION}.\n\n"
                "Check that AZURE_OPENAI_ENDPOINT points to your Azure OpenAI resource, "
                "AZURE_OPENAI_DEPLOYMENT exactly matches the deployment name in Azure AI Foundry, "
                "and AZURE_OPENAI_API_VERSION is supported by that resource. The dashboard itself is still usable; only the AI analyst call failed."
            )
        else:
            answer = f"The AI analyst could not complete the request: {e}"
    conversation_history.append({"role": "user",      "content": user_question})
    conversation_history.append({"role": "assistant", "content": answer})
    return answer, conversation_history


# --------------------------------------------------
# SIGNAL CARD (reusable component)
# --------------------------------------------------
def render_signal_card(label, count, value, signal_type, card_key, full_context):
    icon = SIGNAL_ICON.get(signal_type, "⚪")
    color_map  = {"fix": "#fef2f2", "scale": "#f0fdf4", "normal": "#f8fafc"}
    border_map = {"fix": "#fecaca", "scale": "#bbf7d0", "normal": "#e2e8f0"}
    bg     = color_map.get(signal_type, "#f8fafc")
    border = border_map.get(signal_type, "#e2e8f0")
    desc   = SIGNAL_DESCRIPTION.get(label, "")

    # value label differs by signal type
    value_label = "Current Revenue ($)" if signal_type == "scale" else "Conversion Opportunity ($)"

    st.markdown(f"""
    <div style="background:{bg}; border:1.5px solid {border}; border-radius:12px; padding:16px 20px; margin-bottom:4px;">
        <div style="font-size:15px; font-weight:600; color:#1e293b;">{icon} {label}</div>
        <div style="font-size:12px; color:#64748b; margin-top:4px;">{desc}</div>
        <div style="display:flex; gap:24px; margin-top:10px;">
            <div>
                <div style="font-size:20px; font-weight:700; font-family:'DM Mono',monospace; color:#1e293b;">{count:,}</div>
                <div style="font-size:12px; color:#64748b;">products</div>
            </div>
            <div>
                <div style="font-size:20px; font-weight:700; font-family:'DM Mono',monospace; color:#1e293b;">${value:,.0f}</div>
                <div style="font-size:12px; color:#64748b;">{value_label}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"💬 Ask AI about this", key=f"ask_ai_{card_key}"):
        signal_ctx = f"The user is asking about the '{label}' signal group. There are {count:,} products in this group with a total value of ${value:,.0f}. {desc}"
        with st.spinner("Analysing..."):
            ans, _ = ask_llm(
                f"Explain the '{label}' signal and what the platform should do about the {count} products in this group.",
                [],
                full_context,
                role="platform",
                signal_context=signal_ctx
            )
        st.info(ans)
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)


# --------------------------------------------------
# PLATFORM VIEW
# --------------------------------------------------
# --------------------------------------------------
SITUATION_CONFIG = {
    "Situation 1: Cart barrier": {
        "icon":         "🛑",
        "short":        "Cart Barrier",
        "description":  "Users view products but don't add to cart. The product page is the bottleneck.",
        "who":          "Platform action",
        "who_color":    "#dc2626",
        "what":         "Identify the lowest-performing sellers in this category and recommend improvements to their product pages. Consider deprioritising their exposure until quality improves.",
        "platform_actions": [
            "Identify sellers with the lowest View→Cart rate in this category",
            "Recommend adding more reviews or improving product page quality",
            "Consider reallocating exposure to better-performing sellers",
        ],
        "gap_metric":   "v2c_pct",
        "gap_label":    "View→Cart Rate vs Platform Avg (%)",
        "color_bg":     "#fef9ec",
        "color_border": "#FAC775",
    },
    "Situation 2: Discovery/appeal problem": {
        "icon":         "🔍",
        "short":        "Discovery Gap",
        "description":  "Buyers in this category tend to purchase directly without adding to cart. However, the View→Purchase rate is below the category average, suggesting the product is not converting the viewers it attracts.",
        "who":          "Platform action",
        "who_color":    "#1d4ed8",
        "what":         "Proactively reach out to sellers in this category to discuss advertising partnerships. Adjust recommendation placements to increase visibility.",
        "platform_actions": [
            "Contact sellers in this category to discuss advertising or promotional partnerships",
            "Adjust recommendation algorithm to increase category visibility",
        ],
        "gap_metric":   "v2c_pct",
        "gap_label":    "View→Purchase Rate vs Platform Avg (%)",
        "color_bg":     "#fef2f2",
        "color_border": "#F7C1C1",
    },
    "Situation 3: Checkout friction": {
        "icon":         "⚠️",
        "short":        "Checkout Friction",
        "description":  "Users add to cart but don't complete purchase. High cart abandonment in this category suggests pricing or incentive issues.",
        "who":          "Platform action",
        "who_color":    "#1d4ed8",
        "what":         "Work with sellers in this category to introduce free shipping thresholds or limited-time promotions to reduce cart abandonment.",
        "platform_actions": [
            "Partner with sellers in this category to offer free shipping thresholds",
            "Explore category-specific promotions or discounts to reduce cart abandonment",
        ],
        "gap_metric":   "c2p_pct",
        "gap_label":    "Cart→Purchase Rate vs Platform Avg (%)",
        "color_bg":     "#eff6ff",
        "color_border": "#B5D4F4",
    },
}


def platform_view(product_df, events_df, brand_df, category_df, full_context):
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("## 🏪 Platform Overview")
    st.caption("Understand where your funnel is breaking down — and what actions to take.")

    st.markdown("---")

    # ── KPI Row ───────────────────────────────────────────────────────────────
    avg_v2c = avg_c2p = avg_path_b = total_actionable = 0
    if not category_df.empty:
        avg_v2c        = category_df["v2c_pct"].mean()         if "v2c_pct"        in category_df.columns else 0
        avg_c2p        = category_df["c2p_pct"].mean()         if "c2p_pct"        in category_df.columns else 0
        avg_path_b     = category_df["path_b_rate"].mean()     if "path_b_rate"    in category_df.columns else 0
        valid_situations = [
            "Situation 1: Cart barrier",
            "Situation 2: Discovery/appeal problem",
            "Situation 3: Checkout friction",
        ]
        total_actionable = int(
            category_df[category_df["situation"].isin(valid_situations)]["actionable_product_count"].sum()
        ) if "situation" in category_df.columns and "actionable_product_count" in category_df.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-value">{avg_v2c:.1f}%</div><div class="kpi-label">Avg View → Cart</div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-value">{avg_c2p:.1f}%</div><div class="kpi-label">Avg Cart → Purchase</div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-value">{avg_path_b:.1f}%</div><div class="kpi-label">Direct Purchase Rate</div>', unsafe_allow_html=True)
    with k4:
        color = "#dc2626" if total_actionable > 0 else "#16a34a"
        st.markdown(f'<div class="kpi-value" style="color:{color}">{total_actionable:,}</div><div class="kpi-label">Products Needing Attention</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Situation Cards ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Where is your funnel breaking down?</div>', unsafe_allow_html=True)
    st.caption("Each situation represents a different type of funnel problem. Click a card to see which categories are affected and what to do.")

    sit_cols = st.columns(4)
    for idx, (sit_key, cfg) in enumerate(SITUATION_CONFIG.items()):
        with sit_cols[idx]:
            n_cats = n_prods = 0
            worst_cat = ""
            if not category_df.empty and "situation" in category_df.columns:
                sit_df = category_df[category_df["situation"] == sit_key]
                if sit_df.empty:
                    sit_num = sit_key.split(":")[0]
                    sit_df = category_df[category_df["situation"].astype(str).str.contains(sit_num, case=False, na=False)]
                n_cats    = len(sit_df)
                n_prods   = int(sit_df["actionable_product_count"].sum()) if "actionable_product_count" in sit_df.columns else 0
                # Worst category = largest gap on primary metric
                gap_col = cfg["gap_metric"]
                if gap_col in sit_df.columns and not sit_df.empty:
                    worst_row = sit_df.loc[sit_df[gap_col].idxmin()]
                    worst_cat = worst_row.get("cat_level_2", "")

            with st.container(border=True):
                st.markdown(f"### {cfg['icon']} {cfg['short']}")
                st.caption(cfg["description"])
                if worst_cat:
                    st.caption(f"⚠️ Most critical: {worst_cat}")
                card_m1, card_m2 = st.columns(2)
                card_m1.metric("Categories", f"{n_cats:,}")
                card_m2.metric("Products", f"{n_prods:,}")

            if st.button(f"Explore →", key=f"sit_btn_{idx}"):
                st.session_state.selected_situation = sit_key
                st.session_state.active_tab = "Platform Analysis"
                st.rerun()

    # ── Situation Detail ──────────────────────────────────────────────────────
    selected_sit = st.session_state.get("selected_situation", None)

    if selected_sit and selected_sit in SITUATION_CONFIG:
        cfg = SITUATION_CONFIG[selected_sit]
        st.markdown("---")
        st.markdown(f"### {cfg['icon']} {cfg['short']}")
        st.markdown(f"_{cfg['description']}_")

        # Platform actions
        st.markdown("**Recommended platform actions:**")
        for action in cfg["platform_actions"]:
            st.markdown(f"→ {action}")

        st.markdown("<br>", unsafe_allow_html=True)

        if not category_df.empty and "situation" in category_df.columns:
            sit_cats = category_df[category_df["situation"] == selected_sit].copy()
            if sit_cats.empty:
                sit_num = selected_sit.split(":")[0]
                sit_cats = category_df[category_df["situation"].astype(str).str.contains(sit_num, case=False, na=False)].copy()
            # Filter out categories with no actionable products
            if "actionable_product_count" in sit_cats.columns:
                sit_cats = sit_cats[sit_cats["actionable_product_count"] > 0]

            # Sort by primary metric gap (worst first = lowest v2c_pct or c2p_pct)
            # Left chart: sort by primary metric ascending (lowest = most severe)
            gap_col = cfg["gap_metric"]
            sit_cats_severity = sit_cats.sort_values(gap_col, ascending=True) if gap_col in sit_cats.columns else sit_cats
            # Right chart: sort by revenue opportunity descending
            sit_cats_revenue = sit_cats.sort_values("actionable_lost_revenue", ascending=True) if "actionable_lost_revenue" in sit_cats.columns else sit_cats

            if sit_cats.empty:
                st.info("No categories found for this situation.")
            else:
                chart_col1, chart_col2 = st.columns(2)

                # Chart 1: Problem severity — primary metric rate (lower = worse)
                with chart_col1:
                    if gap_col in sit_cats_severity.columns and "cat_level_2" in sit_cats_severity.columns:
                        fig1 = px.bar(
                            sit_cats_severity.head(10),
                            x=gap_col,
                            y="cat_level_2",
                            orientation="h",
                            color=gap_col,
                            color_continuous_scale=["#dc2626", "#dbeafe"],
                            labels={
                                gap_col: cfg["gap_label"].split("vs")[0].strip() + " (%)",
                                "cat_level_2": "",
                            },
                            title="Problem Severity"
                        )
                        fig1.update_layout(
                            coloraxis_showscale=False,
                            plot_bgcolor="white", paper_bgcolor="white",
                            margin=dict(l=0, r=0, t=40, b=10),
                            yaxis=dict(autorange="reversed"),
                            height=min(400, len(sit_cats) * 35 + 80),
                            font=dict(family="DM Sans")
                        )
                        fig1.update_traces(marker_line_width=0)
                        st.plotly_chart(fig1, use_container_width=True)
                        st.caption("🔴 Red = below platform average — more severe")

                # Chart 2: Revenue opportunity — est. gap vs benchmark
                with chart_col2:
                    if "actionable_lost_revenue" in sit_cats_revenue.columns and "cat_level_2" in sit_cats_revenue.columns:
                        fig2 = px.bar(
                            sit_cats_revenue.head(10),
                            x="actionable_lost_revenue",
                            y="cat_level_2",
                            orientation="h",
                            color="actionable_rate" if "actionable_rate" in sit_cats_revenue.columns else "actionable_lost_revenue",
                            color_continuous_scale=["#dbeafe", "#1d4ed8"],
                            labels={
                                "actionable_lost_revenue": "Estimated Revenue Recovery ($)",
                                "cat_level_2": "",
                                "actionable_rate": "% Products Affected"
                            },
                            title="Revenue Recovery Opportunity"
                        )
                        fig2.update_layout(
                            coloraxis_showscale=False,
                            plot_bgcolor="white", paper_bgcolor="white",
                            margin=dict(l=0, r=0, t=40, b=10),
                            yaxis=dict(autorange="reversed"),
                            height=min(400, len(sit_cats) * 35 + 80),
                            font=dict(family="DM Sans")
                        )
                        fig2.update_traces(marker_line_width=0)
                        st.plotly_chart(fig2, use_container_width=True)

                # Table
                display_cols = [c for c in [
                    "cat_level_2", "actionable_product_count",
                    "actionable_rate", "v2c_pct", "c2p_pct", "path_b_rate"
                ] if c in sit_cats.columns]

                st.dataframe(
                    sit_cats[display_cols].rename(columns={
                        "cat_level_2":              "Category",
                        "actionable_product_count": "Products to Address",
                        "actionable_rate":           "% of Category Affected",
                        "v2c_pct":                   "View→Cart %",
                        "c2p_pct":                   "Cart→Purchase %",
                        "path_b_rate":               "Direct Purchase Rate",
                    }),
                    use_container_width=True, hide_index=True
                )

                # AI button
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"💬 Ask AI: What should the platform do about {cfg['short']}?", key="sit_ask_ai"):
                    sit_ctx = (
                        f"Situation: {selected_sit}. {cfg['description']} "
                        f"Categories affected: {', '.join(sit_cats['cat_level_2'].tolist() if 'cat_level_2' in sit_cats.columns else [])}. "
                        f"Total products needing attention: {int(sit_cats['actionable_product_count'].sum()) if 'actionable_product_count' in sit_cats.columns else 'N/A'}."
                    )
                    with st.spinner("Thinking..."):
                        ans, _ = ask_llm(
                            f"What should the platform do about the {cfg['short']} situation? Be specific about which categories to prioritise and what actions to take.",
                            [], full_context, role="platform", signal_context=sit_ctx
                        )
                    st.info(ans)

        else:
            st.info("Category situation data not available.")

        if st.button("✕ Close", key="close_situation"):
            st.session_state.pop("selected_situation", None)
            st.rerun()

    st.markdown("---")

    # ── Brand Section ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Brand Performance</div>', unsafe_allow_html=True)

    if not brand_df.empty:
        sort_col   = "total_actionable_lost_revenue" if "total_actionable_lost_revenue" in brand_df.columns else brand_df.columns[0]
        fix_brands   = brand_df[brand_df["action_type"] == "Fix"].sort_values(sort_col, ascending=False).head(10)
        scale_brands = brand_df[brand_df["action_type"] == "Scale"].sort_values(sort_col, ascending=False).head(10)

        b1, b2 = st.columns(2)
        with b1:
            st.markdown("**🔴 Brands Needing Attention**")
            if not fix_brands.empty:
                fix_cols = [c for c in [
                    "brand", "cat_level_2",
                    "brand_rank_label",
                    "situation_summary",
                    "actionable_product_count",
                ] if c in fix_brands.columns]
                st.dataframe(
                    fix_brands[fix_cols].rename(columns={
                        "cat_level_2":              "Category",
                        "brand_rank_label":         "Rank in Category",
                        "situation_summary":        "Issue",
                        "actionable_product_count": "Products to Address",
                    }),
                    use_container_width=True, hide_index=True
                )
                if st.button("💬 Ask AI: Which brands to prioritise?", key="brand_fix_ai"):
                    with st.spinner("Thinking..."):
                        ans, _ = ask_llm(
                            "Which underperforming brands should the platform prioritise contacting and why?",
                            [], full_context, role="platform",
                        )
                    st.info(ans)

        with b2:
            st.markdown("**🟢 Strong Converters — Scale Their Exposure**")
            st.caption("These brands convert well. Increasing their exposure can grow platform revenue.")
            if not scale_brands.empty:
                scale_cols = [c for c in [
                    "brand", "cat_level_2",
                    "brand_rank_label",
                    "actionable_product_count",
                ] if c in scale_brands.columns]
                st.dataframe(
                    scale_brands[scale_cols].rename(columns={
                        "cat_level_2":              "Category",
                        "brand_rank_label":         "Rank in Category",
                        "actionable_product_count": "Products",
                    }),
                    use_container_width=True, hide_index=True
                )
                if st.button("💬 Ask AI: Which brands to scale?", key="brand_scale_ai"):
                    with st.spinner("Thinking..."):
                        ans, _ = ask_llm(
                            "Which strong-converting brands should the platform give more exposure to, and what would be the estimated revenue impact?",
                            [], full_context, role="platform",
                        )
                    st.info(ans)

    st.markdown("---")

    # AI chat intentionally removed from this tab.
    # Use the sidebar AI Analyst so the chatbot appears in only one place.


# --------------------------------------------------
# SELLER VIEW
# --------------------------------------------------
SELLER_ACTIONS = {
    "Situation 1: Cart barrier": {
        "short": "Cart Barrier",
        "icon": "🛑",
        "explanation": "Users view your products but aren't adding them to cart. Your product page may not be convincing enough.",
        "actions": [
            "Improve product images — use high-quality photos from multiple angles",
            "Review your pricing — compare with similar products in this category",
            "Add or improve product descriptions to highlight key benefits",
            "Increase review count — consider reaching out to past buyers",
        ]
    },
    "Situation 2: Discovery/appeal problem": {
        "short": "Discovery Gap",
        "icon": "🔍",
        "explanation": "Your products aren't getting enough exposure to the right buyers. Consider investing in visibility.",
        "actions": [
            "Purchase platform advertising to increase your product's placement",
            "Participate in platform promotional campaigns or flash sales",
            "Optimise product titles and keywords for better search visibility",
            "Contact the platform about featuring your products in category pages",
        ]
    },
    "Situation 3: Checkout friction": {
        "short": "Checkout Friction",
        "icon": "⚠️",
        "explanation": "Buyers add your products to cart but don't complete the purchase. Price or shipping may be the barrier.",
        "actions": [
            "Offer free shipping or reduce shipping costs",
            "Run a limited-time discount to convert hesitant buyers",
            "Strengthen trust signals — add warranty, return policy, or certifications",
            "Review your pricing relative to competitors in this category",
        ]
    },
    "Strong Performer": {
        "short": "Strong Performer",
        "icon": "🟢",
        "explanation": "This product is performing above the category average. Focus on maintaining performance and scaling exposure.",
        "actions": [
            "Maintain current pricing and product page quality",
            "Consider increasing inventory to meet potential demand",
            "Use this product as a template for improving other products",
        ]
    },
}


def seller_view(product_df, events_df, full_context):
    st.markdown("## 🛍️ Seller Dashboard")
    st.caption("Select your brand to see a diagnosis of your products and recommended actions.")
    st.markdown("---")

    # ── Brand Selection ───────────────────────────────────────────────────
    if "brand" not in product_df.columns:
        st.warning("Brand data not available.")
        return

    all_brands = sorted(product_df["brand"].dropna().unique().tolist())
    all_brands = [b for b in all_brands if b not in ["Unknown", ""]]

    selected_brand = st.selectbox("Select your brand", ["— Select a brand —"] + all_brands, key="seller_brand_select")

    if selected_brand == "— Select a brand —":
        # Show all products overview before brand selection
        st.markdown("### All Products Overview")
        st.caption("Browse all products or select a brand above to see a detailed diagnosis.")

        overview_cols = [c for c in [
            "product_id", "brand", "cat_level_2", "signal_label", "view", "conversion_rate"
        ] if c in product_df.columns]

        overview_df = product_df[overview_cols].copy()
        overview_df = overview_df.rename(columns={
            "product_id": "Product ID",
            "brand": "Brand",
            "cat_level_2": "Category",
            "signal_label": "Signal",
            "view": "Views",
            "conversion_rate": "Conv. Rate",
        })
        st.dataframe(overview_df, use_container_width=True, hide_index=True)
        return

    # ── Brand Overview ────────────────────────────────────────────────────
    brand_products = product_df[product_df["brand"] == selected_brand].copy()

    if brand_products.empty:
        st.warning(f"No products found for brand: {selected_brand}")
        return

    st.markdown(f"### {selected_brand}")

    # KPI summary
    total_prods    = len(brand_products)
    n_fix          = brand_products["signal_type"].eq("fix").sum() if "signal_type" in brand_products.columns else 0
    n_scale        = brand_products["signal_type"].eq("scale").sum() if "signal_type" in brand_products.columns else 0
    n_normal       = total_prods - n_fix - n_scale
    categories     = brand_products["cat_level_2"].nunique() if "cat_level_2" in brand_products.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi-value">{total_prods}</div><div class="kpi-label">Total Products</div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi-value" style="color:#dc2626">{n_fix}</div><div class="kpi-label">Need Attention</div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-value" style="color:#16a34a">{n_scale}</div><div class="kpi-label">Strong Converters</div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi-value">{categories}</div><div class="kpi-label">Categories</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Situation Breakdown ───────────────────────────────────────────────
    st.markdown("### Your Products by Situation")
    st.caption("Each situation explains why conversion is low and what you can do about it.")

    situation_order = [
        "Situation 1: Cart barrier",
        "Situation 2: Discovery/appeal problem",
        "Situation 3: Checkout friction",
    ]

    has_any_situation = False

    # Track normal/healthy products to show separately
    normal_products_all = pd.DataFrame()

    for sit_key in situation_order:
        # Only show fix products in situation expanders
        sit_products = brand_products[
            (brand_products["situation"] == sit_key) &
            (brand_products["signal_type"] == "fix")
        ].copy() if "situation" in brand_products.columns else pd.DataFrame()

        # Collect normal products for separate expander
        sit_normal = brand_products[
            (brand_products["situation"] == sit_key) &
            (~brand_products["signal_type"].isin(["fix", "scale"]))
        ].copy() if "situation" in brand_products.columns else pd.DataFrame()
        normal_products_all = pd.concat([normal_products_all, sit_normal])

        if sit_products.empty:
            continue

        has_any_situation = True
        cfg = SELLER_ACTIONS.get(sit_key, {})

        # Determine primary metric and benchmark for this situation
        if sit_key == "Situation 1: Cart barrier":
            metric_col     = "view_to_cart_pct"
            benchmark_col  = "cat_v2c_benchmark"
            metric_label   = "View→Cart %"
            benchmark_label = "Category Avg V→C %"
        elif sit_key == "Situation 2: Discovery/appeal problem":
            metric_col     = "view_to_purchase_pct"
            benchmark_col  = "cat_v2p_benchmark" if "cat_v2p_benchmark" in sit_products.columns else "cat_v2c_benchmark"
            metric_label   = "View→Purchase %"
            benchmark_label = "Category Avg V→P %"
        else:  # Situation 3
            metric_col     = "cart_to_purchase_pct"
            benchmark_col  = "cat_c2p_benchmark"
            metric_label   = "Cart→Purchase %"
            benchmark_label = "Category Avg C→P %"

        # Compute gap and sort (worst first)
        if metric_col in sit_products.columns and benchmark_col in sit_products.columns:
            sit_products["_gap"] = (
                sit_products[benchmark_col] - sit_products[metric_col]
            ).round(1)
            sit_products = sit_products.sort_values("_gap", ascending=False)

        # Percentile to text
        def percentile_label(p):
            if pd.isna(p):
                return "N/A"
            if p <= 10:   return f"Bottom 10%"
            if p <= 25:   return f"Bottom 25%"
            if p <= 50:   return f"Below Average"
            if p <= 75:   return f"Above Average"
            return f"Top 25%"

        with st.expander(f"{cfg.get('icon','📌')} {cfg.get('short', sit_key)} — {len(sit_products)} products needing attention", expanded=True):
            st.markdown(f"_{cfg.get('explanation', '')}_")
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("**What you can do:**")
            for action in cfg.get("actions", []):
                st.markdown(f"→ {action}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Build focused table
            table_data = []
            for _, row in sit_products.iterrows():
                metric_val    = row.get(metric_col, None)
                benchmark_val = row.get(benchmark_col, None)
                gap           = row.get("_gap", None)
                pct           = row.get("primary_percentile", None)

                table_data.append({
                    "Product ID":       row.get("product_id", ""),
                    "Category":         row.get("cat_level_2", ""),
                    metric_label:       f"{metric_val:.1f}%" if pd.notna(metric_val) else "N/A",
                    benchmark_label:    f"{benchmark_val:.1f}%" if pd.notna(benchmark_val) else "N/A",
                    "Gap vs Avg":       f"▼ {gap:.1f}%" if pd.notna(gap) and gap > 0 else (f"▲ {abs(gap):.1f}%" if pd.notna(gap) else "N/A"),
                    "Standing":         percentile_label(pct),
                    "Views":            int(row.get("view", 0)),
                })

            if table_data:
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

            # Product deep dive
            if "product_id" in sit_products.columns:
                product_options = (
                    sit_products.assign(
                        label=lambda d: d["product_id"].astype(str) + " | " +
                                       d.get("cat_level_2", pd.Series([""] * len(d))).astype(str)
                    )
                    .set_index("label")["product_id"].to_dict()
                )
                selected_label = st.selectbox(
                    "Inspect a product in detail",
                    ["— Select —"] + list(product_options.keys()),
                    key=f"seller_product_{sit_key}"
                )

                if selected_label != "— Select —":
                    selected_id  = product_options[selected_label]
                    product_row  = sit_products[sit_products["product_id"] == selected_id].iloc[0]
                    signal_label = product_row.get("signal_label", "Normal")
                    lost_rev     = product_row.get("lost_revenue_est", 0)

                    dc1, dc2 = st.columns(2)

                    with dc1:
                        m1, m2, m3 = st.columns(3)
                        if "view_to_cart_pct" in product_row.index:
                            m1.metric("View → Cart", f"{product_row['view_to_cart_pct']:.1f}%",
                                      delta=f"{product_row['view_to_cart_pct'] - product_row.get('cat_v2c_benchmark', product_row['view_to_cart_pct']):.1f}% vs avg"
                                      if "cat_v2c_benchmark" in product_row.index else None)
                        if "view_to_purchase_pct" in product_row.index:
                            m2.metric("View → Purchase", f"{product_row['view_to_purchase_pct']:.1f}%")
                        if "cart_to_purchase_pct" in product_row.index:
                            val = product_row["cart_to_purchase_pct"]
                            m3.metric("Cart → Purchase", "N/A" if pd.isna(val) else f"{val:.1f}%",
                                      delta=f"{val - product_row.get('cat_c2p_benchmark', val):.1f}% vs avg"
                                      if "cat_c2p_benchmark" in product_row.index and not pd.isna(val) else None)

                        if "price" in product_row.index:
                            st.metric("Price", f"${product_row['price']:.2f}")
                        if "primary_percentile" in product_row.index:
                            pct = product_row["primary_percentile"]
                            st.metric("Percentile in Category", f"{pct:.0f}th" if not pd.isna(pct) else "N/A")

                    with dc2:
                        # Benchmark bar chart
                        if "cat_level_2" in product_row.index and all(c in product_df.columns for c in ["view_to_cart_pct", "view_to_purchase_pct"]):
                            cat_group = product_df[product_df["cat_level_2"] == product_row["cat_level_2"]]
                            if len(cat_group) > 1:
                                compare_df = pd.DataFrame({
                                    "Metric": ["View→Cart %", "View→Purchase %"],
                                    "This Product": [
                                        product_row.get("view_to_cart_pct", 0),
                                        product_row.get("view_to_purchase_pct", 0)
                                    ],
                                    "Category Average": [
                                        product_row.get("cat_v2c_benchmark", cat_group["view_to_cart_pct"].median()),
                                        product_row.get("cat_v2p_benchmark", cat_group["view_to_purchase_pct"].median())
                                    ]
                                })
                                fig_compare = px.bar(
                                    compare_df.melt(id_vars="Metric", var_name="Type", value_name="Value"),
                                    x="Metric", y="Value", color="Type", barmode="group",
                                    color_discrete_map={"This Product": "#1d4ed8", "Category Average": "#cbd5e1"},
                                    title=f"vs Category Average ({product_row.get('cat_level_2', '')})"
                                )
                                fig_compare.update_layout(
                                    plot_bgcolor="white", paper_bgcolor="white",
                                    legend_title="", height=280,
                                    margin=dict(l=0, r=0, t=40, b=0),
                                    font=dict(family="DM Sans")
                                )
                                st.plotly_chart(fig_compare, use_container_width=True)

                    # Funnel
                    if all(c in product_row.index for c in ["view", "cart", "purchase"]):
                        funnel_df = pd.DataFrame({
                            "Stage": ["View", "Cart", "Purchase"],
                            "Count": [product_row["view"], product_row["cart"], product_row["purchase"]]
                        })
                        fig_funnel = go.Figure(go.Funnel(
                            y=funnel_df["Stage"], x=funnel_df["Count"],
                            marker=dict(color=["#bfdbfe", "#60a5fa", "#1d4ed8"]),
                            textinfo="value+percent initial"
                        ))
                        fig_funnel.update_layout(
                            title="Product Funnel",
                            plot_bgcolor="white", paper_bgcolor="white",
                            margin=dict(l=0, r=0, t=40, b=0),
                            font=dict(family="DM Sans"), height=250
                        )
                        st.plotly_chart(fig_funnel, use_container_width=True)

                    # AI chat for this product
                    product_context = (
                        f"Seller is looking at product {selected_id} (brand: {selected_brand}, "
                        f"category: {product_row.get('cat_level_2','Unknown')}, situation: {sit_key}). "
                        f"View→Cart: {product_row.get('view_to_cart_pct','N/A')}% vs category avg {product_row.get('cat_v2c_benchmark','N/A')}%. "
                        f"Cart→Purchase: {product_row.get('cart_to_purchase_pct','N/A')}% vs category avg {product_row.get('cat_c2p_benchmark','N/A')}%. "
                        f"Percentile in category: {product_row.get('primary_percentile','N/A')}."
                    )

                    st.markdown("**💬 Ask AI about this product:**")
                    seller_suggestions = [
                        f"Why is product {selected_id} underperforming in its category?",
                        f"What is the most impactful action I can take for product {selected_id}?",
                    ]
                    sc1, sc2 = st.columns(2)
                    for i, sug in enumerate(seller_suggestions):
                        if [sc1, sc2][i].button(sug, key=f"seller_sug_{sit_key}_{selected_id}_{i}"):
                            with st.spinner("Thinking..."):
                                ans, _ = ask_llm(sug, [], full_context, role="seller", product_context=product_context)
                            st.info(ans)

                    user_input = st.chat_input(f"Ask about product {selected_id}...", key=f"seller_chat_{sit_key}_{selected_id}")
                    if user_input:
                        with st.spinner("Thinking..."):
                            ans, _ = ask_llm(user_input, [], full_context, role="seller", product_context=product_context)
                        st.info(ans)

    # ── Strong Performers ─────────────────────────────────────────────────
    strong = brand_products[brand_products["signal_type"] == "scale"].copy() if "signal_type" in brand_products.columns else pd.DataFrame()
    if not strong.empty:
        with st.expander(f"🟢 Strong Converters — {len(strong)} products", expanded=False):
            st.caption("These products are performing well. Focus on maintaining and scaling their exposure.")
            cfg = SELLER_ACTIONS.get("Strong Performer", {})
            for action in cfg.get("actions", []):
                st.markdown(f"→ {action}")
            st.markdown("<br>", unsafe_allow_html=True)
            strong_cols = [c for c in ["product_id", "cat_level_2", "signal_label", "view_to_cart_pct", "view_to_purchase_pct", "primary_percentile", "view"] if c in strong.columns]
            st.dataframe(strong[strong_cols].rename(columns={
                "product_id": "Product ID",
                "cat_level_2": "Category",
                "signal_label": "Signal",
                "view_to_cart_pct": "View→Cart %",
                "view_to_purchase_pct": "View→Purchase %",
                "primary_percentile": "Percentile in Category",
                "view": "Views",
            }), use_container_width=True, hide_index=True)

    # ── Normal / Healthy Products ─────────────────────────────────────────
    EXCLUDE_FROM_HEALTHY = ["Insufficient data", "Insufficient Data", "Underperformer"]
    healthy_products = brand_products[
        (
            brand_products["signal_type"].isin(["normal"]) |
            brand_products["situation"].isin(["Healthy"])
        ) &
        (~brand_products["signal_v2"].isin(EXCLUDE_FROM_HEALTHY) if "signal_v2" in brand_products.columns else True)
    ].copy() if "signal_type" in brand_products.columns else pd.DataFrame()

    if not healthy_products.empty:
        with st.expander(f"⚪ Healthy & Normal Products — {len(healthy_products)} products", expanded=False):
            st.caption("These products are performing within or above the expected range for their category.")
            healthy_cols = [c for c in [
                "product_id", "cat_level_2", "signal_label",
                "view_to_cart_pct", "view_to_purchase_pct", "primary_percentile", "view"
            ] if c in healthy_products.columns]
            st.dataframe(
                healthy_products[healthy_cols].rename(columns={
                    "product_id":           "Product ID",
                    "cat_level_2":          "Category",
                    "signal_label":         "Signal",
                    "view_to_cart_pct":     "View→Cart %",
                    "view_to_purchase_pct": "View→Purchase %",
                    "primary_percentile":   "Percentile in Category",
                    "view":                 "Views",
                }),
                use_container_width=True, hide_index=True
            )

    if not has_any_situation and strong.empty:
        st.success(f"✅ No products from {selected_brand} have been flagged as needing attention.")


# --------------------------------------------------
# LANDING PAGE
# --------------------------------------------------
def landing_page():
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; margin-bottom:48px;">
        <div style="font-size:40px; font-weight:700; color:#1e293b; letter-spacing:-0.02em;">
            Funnel Intelligence Dashboard
        </div>
        <div style="font-size:18px; color:#64748b; margin-top:8px;">
            E-commerce conversion analysis — October 2019
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_mid, col_right = st.columns([1, 4, 1])
    with col_mid:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""
            <div style="border:2px solid #e2e8f0; border-radius:16px; padding:32px; text-align:center; background:white;">
                <div style="font-size:48px;">🏪</div>
                <div style="font-size:20px; font-weight:700; color:#1e293b; margin-top:12px;">Platform Operator</div>
                <div style="font-size:14px; color:#64748b; margin-top:8px; line-height:1.5;">
                    Monitor overall funnel health.<br>
                    Find which categories and brands<br>
                    are losing the most revenue.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Enter as Platform Operator →", use_container_width=True, type="primary"):
                st.session_state.role = "platform"
                st.rerun()

        with c2:
            st.markdown("""
            <div style="border:2px solid #e2e8f0; border-radius:16px; padding:32px; text-align:center; background:white;">
                <div style="font-size:48px;">🛍️</div>
                <div style="font-size:20px; font-weight:700; color:#1e293b; margin-top:12px;">Seller</div>
                <div style="font-size:14px; color:#64748b; margin-top:8px; line-height:1.5;">
                    Diagnose your products.<br>
                    Understand why conversion is low<br>
                    and what to do about it.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Enter as Seller →", use_container_width=True):
                st.session_state.role = "seller"
                st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#94a3b8; font-size:13px;">
        1,300 products · 6 signal types · LLM-powered recommendations
    </div>
    """, unsafe_allow_html=True)



# --------------------------------------------------
# V4 SIDEBAR FILTERS + BUSINESS VALUE TAB HELPERS
# --------------------------------------------------
def apply_product_filters(product_df, selected_level_1, selected_level_2, selected_signals, selected_priority, price_range, product_search):
    filtered = product_df.copy()
    if "price" in filtered.columns:
        filtered = filtered[filtered["price"].between(price_range[0], price_range[1])]
    if selected_level_1 and "cat_level_1" in filtered.columns:
        filtered = filtered[filtered["cat_level_1"].isin(selected_level_1)]
    if selected_level_2 and "cat_level_2" in filtered.columns:
        filtered = filtered[filtered["cat_level_2"].isin(selected_level_2)]
    sig_col = "signal_v2" if "signal_v2" in filtered.columns else "signal"
    if selected_signals and sig_col in filtered.columns:
        filtered = filtered[filtered[sig_col].isin(selected_signals)]
    if selected_priority and "priority_tier" in filtered.columns:
        filtered = filtered[filtered["priority_tier"].isin(selected_priority)]
    if product_search.strip():
        mask = filtered["product_id"].astype(str).str.contains(product_search, case=False, na=False)
        for col in ["brand", "category_code", "cat_level_2"]:
            if col in filtered.columns:
                mask = mask | filtered[col].astype(str).str.contains(product_search, case=False, na=False)
        filtered = filtered[mask]
    return filtered


ACTIONABLE_SIGNAL_TYPES = [
    "Low Cart Rate — fix product page",
    "Low Direct Purchase Rate — fix visibility",
    "Low Checkout Rate — fix checkout",
    "Low Overall CR — review traffic quality",
]

def build_signal_kpis(filtered_products):
    total_products = len(filtered_products)
    sig_col = "signal_v2" if "signal_v2" in filtered_products.columns else "signal"
    if sig_col in filtered_products.columns:
        actionable_mask   = filtered_products[sig_col].isin(ACTIONABLE_SIGNAL_TYPES)
        flagged_products  = int(actionable_mask.sum())
        # Primary opportunity = situation with most actionable products
        if "situation" in filtered_products.columns:
            sit_counts = filtered_products[actionable_mask]["situation"].value_counts()
            sit_labels = {
                "Situation 1: Cart barrier":               "Cart Barrier",
                "Situation 2: Discovery/appeal problem":   "Discovery Gap",
                "Situation 3: Checkout friction":          "Checkout Friction",
            }
            top_signal = sit_labels.get(sit_counts.index[0], sit_counts.index[0]) + f" ({sit_counts.iloc[0]:,} products)" if not sit_counts.empty else "None"
        else:
            actionable_counts = filtered_products[actionable_mask][sig_col].value_counts()
            top_signal = SIGNAL_LABELS.get(actionable_counts.index[0], actionable_counts.index[0]) if not actionable_counts.empty else "None"
    else:
        flagged_products = 0
        top_signal       = "None"
    total_revenue  = filtered_products["revenue_proxy"].sum() if "revenue_proxy" in filtered_products.columns else 0
    avg_conversion = filtered_products["conversion_rate"].mean() if "conversion_rate" in filtered_products.columns and len(filtered_products) > 0 else 0
    return {"total_products": total_products, "flagged_products": flagged_products, "total_revenue": total_revenue, "avg_conversion": avg_conversion, "top_signal": top_signal}


def executive_summary_text(kpis):
    return (
        f"**Total Platform Revenue:** ${kpis['total_revenue']:,.0f}  \n"
        f"**Primary Opportunity:** {kpis['top_signal']}  \n"
        f"**Products Requiring Attention:** {kpis['flagged_products']:,}  \n\n"
        "This dashboard identifies where the e-commerce funnel is underperforming and surfaces which categories and sellers need action."
    )


def render_sidebar_chat(full_context):
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI Analyst")
    st.sidebar.caption("Ask a question without leaving the dashboard.")
    if "sidebar_chat_history" not in st.session_state:
        st.session_state.sidebar_chat_history = []
    if "sidebar_chat_messages" not in st.session_state:
        st.session_state.sidebar_chat_messages = []
    with st.sidebar.expander("Suggested prompts", expanded=False):
        suggestions = ["What is the biggest revenue opportunity right now?", "Which seller actions should we prioritize first?", "Which categories appear weakest for shoppers?"]
        for i, suggestion in enumerate(suggestions):
            if st.button(suggestion, key=f"sidebar_prompt_{i}"):
                answer, st.session_state.sidebar_chat_history = ask_llm(suggestion, st.session_state.sidebar_chat_history, full_context, role="platform")
                st.session_state.sidebar_chat_messages.append({"role": "user", "content": suggestion})
                st.session_state.sidebar_chat_messages.append({"role": "assistant", "content": answer})
                st.rerun()
    user_input = st.sidebar.text_area("Ask the AI analyst", placeholder="What should leadership focus on first?", height=100)
    if st.sidebar.button("Send to AI", use_container_width=True):
        if user_input.strip():
            answer, st.session_state.sidebar_chat_history = ask_llm(user_input, st.session_state.sidebar_chat_history, full_context, role="platform")
            st.session_state.sidebar_chat_messages.append({"role": "user", "content": user_input})
            st.session_state.sidebar_chat_messages.append({"role": "assistant", "content": answer})
            st.rerun()
    if st.session_state.sidebar_chat_messages:
        st.sidebar.markdown("**Recent answers**")
        for msg in st.session_state.sidebar_chat_messages[-4:]:
            prefix = "You" if msg["role"] == "user" else "AI"
            st.sidebar.write(f"**{prefix}:** {msg['content']}")
        if st.sidebar.button("Clear AI chat", use_container_width=True):
            st.session_state.sidebar_chat_history = []
            st.session_state.sidebar_chat_messages = []
            st.rerun()
            
def render_executive_snapshot_tab(filtered_products, category_df, brand_df):
    st.markdown("## Executive Snapshot")
    st.caption("A client-ready summary of the biggest funnel opportunities and recommended priorities.")

    valid_situations = [
        "Situation 1: Cart barrier",
        "Situation 2: Discovery/appeal problem",
        "Situation 3: Checkout friction",
    ]

    total_products = len(filtered_products)
    total_revenue = filtered_products["revenue_proxy"].sum() if "revenue_proxy" in filtered_products.columns else 0
    avg_cr = filtered_products["conversion_rate"].mean() if "conversion_rate" in filtered_products.columns else 0

    actionable_products = 0
    top_category = "N/A"
    top_opportunity = 0
    top_situation = "N/A"

    if category_df is not None and not category_df.empty:
        actionable_df = category_df[category_df["situation"].isin(valid_situations)].copy()

        if "actionable_product_count" in actionable_df.columns:
            actionable_products = int(actionable_df["actionable_product_count"].sum())

        if "actionable_lost_revenue" in actionable_df.columns and not actionable_df.empty:
            top_row = actionable_df.sort_values("actionable_lost_revenue", ascending=False).iloc[0]
            top_category = top_row.get("cat_level_2", "N/A")
            top_opportunity = top_row.get("actionable_lost_revenue", 0)
            
        top_situation = (
            str(top_row.get("situation", "N/A"))
            .replace("Situation 1: ", "")
            .replace("Situation 2: ", "")
            .replace("Situation 3: ", "")

        )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products Analyzed", f"{total_products:,}")
    c2.metric("Products Needing Action", f"{actionable_products:,}")
    c3.metric("Current Revenue", f"${total_revenue:,.0f}")
    c4.metric("Avg Conversion", f"{avg_cr:.2%}")

    st.markdown("---")

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e3a5f 0%,#2d5a8e 100%);
                border-radius:16px; padding:28px; color:white; margin-bottom:20px;">
        <div style="font-size:15px; opacity:0.85; text-transform:uppercase; letter-spacing:0.08em;">
            Highest Priority Opportunity
        </div>
        <div style="font-size:34px; font-weight:700; margin-top:8px;">
            {top_category}
        </div>
        <div style="font-size:18px; margin-top:8px;">
            Estimated revenue recovery: <b>${top_opportunity:,.0f}</b>
        </div>
        <div style="font-size:15px; margin-top:8px; opacity:0.9;">
            Primary issue: {top_situation}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Recommended Executive Focus")

    focus1, focus2, focus3 = st.columns(3)

    with focus1:
        st.info(
            "**1. Prioritize the largest revenue gaps**  \n\n"
            "Start with categories showing the highest estimated recoverable revenue."
        )

    with focus2:
        st.warning(
            "**2. Fix conversion bottlenecks**  \n\n"
            "Focus seller recommendations on product pages, visibility, and checkout friction."
        )

    with focus3:
        st.success(
            "**3. Scale strong converters**  \n\n"
            "Increase exposure for brands/products that already convert well."
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if category_df is not None and not category_df.empty and "actionable_lost_revenue" in category_df.columns:
            top_cats = (
                category_df[category_df["situation"].isin(valid_situations)]
                .sort_values("actionable_lost_revenue", ascending=False)
                .head(8)
            )

            fig = px.bar(
                top_cats,
                x="actionable_lost_revenue",
                y="cat_level_2",
                orientation="h",
                title="Top Revenue Recovery Categories",
                labels={
                    "actionable_lost_revenue": "Estimated Revenue Recovery ($)",
                    "cat_level_2": ""
                },
                text="actionable_lost_revenue",
            )
            fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside")
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="DM Sans"),
                margin=dict(l=0, r=20, t=50, b=20),
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if category_df is not None and not category_df.empty and "situation" in category_df.columns:
            situation_summary = (
                category_df[category_df["situation"].isin(valid_situations)]
                .groupby("situation")["actionable_product_count"]
                .sum()
                .reset_index()
                .sort_values("actionable_product_count", ascending=False)
            )

            situation_summary["Situation"] = (
                situation_summary["situation"]
                .str.replace("Situation 1: ", "", regex=False)
                .str.replace("Situation 2: ", "", regex=False)
                .str.replace("Situation 3: ", "", regex=False)
            )

            fig = px.bar(
                situation_summary,
                x="Situation",
                y="actionable_product_count",
                title="Products Needing Action by Funnel Issue",
                labels={"actionable_product_count": "Products Needing Action"},
                text="actionable_product_count",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="DM Sans"),
                margin=dict(l=0, r=20, t=50, b=80),
                height=420,
                xaxis_tickangle=-20,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Client Talking Point")
    st.success(
        f"The dashboard identifies **{actionable_products:,} products needing action**, "
        f"with the biggest immediate opportunity in **{top_category}**. "
        "The recommended strategy is to fix underperforming funnel stages first, then scale products and brands that already convert well."
    )

def render_business_value_tab(filtered_products, signal_summary_df, category_df=None):
    kpis = build_signal_kpis(filtered_products)
    st.markdown("## Business Value")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products Analyzed", f"{kpis['total_products']:,}")
    c2.metric("Products Requiring Action", f"{kpis['flagged_products']:,}")
    c3.metric("Total Platform Revenue", f"${kpis['total_revenue']:,.0f}")
    c4.metric("Avg Conversion", f"{kpis['avg_conversion']:.2%}")
    st.info(executive_summary_text(kpis))

    col1, col2 = st.columns(2)

    # Left chart: Product Signal Distribution — horizontal, short labels, no Insufficient Data
    with col1:
        sig_col = "signal_v2" if "signal_v2" in filtered_products.columns else "signal"
        if sig_col in filtered_products.columns:
            EXCLUDE_SIGNALS = ["Insufficient data", "Insufficient Data", "Underperformer"]
            SHORT_SIGNAL_LABELS = {
                "Low Cart Rate — fix product page":          "Cart Barrier",
                "Low Direct Purchase Rate — fix visibility": "Low Visibility",
                "Low Checkout Rate — fix checkout":          "Checkout Friction",
                "Low Overall CR — review traffic quality":   "Traffic Mismatch",
                "High Direct Purchase (Path B)":             "Direct Purchase",
                "Strong Performer":                          "Strong Performer",
                "Normal":                                    "Normal",
            }
            signal_counts = (
                filtered_products[~filtered_products[sig_col].isin(EXCLUDE_SIGNALS)][sig_col]
                .map(SHORT_SIGNAL_LABELS)
                .fillna(filtered_products[sig_col])
                .value_counts()
                .reset_index()
            )
            signal_counts.columns = ["Signal", "Products"]
            # Sort by count descending for cleaner look
            signal_counts = signal_counts.sort_values("Products", ascending=False)
            fig_dist = px.bar(
                signal_counts,
                x="Signal", y="Products",
                title="Product Signal Distribution",
                color_discrete_sequence=["#1d4ed8"],
                text="Products",
            )
            fig_dist.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="DM Sans"),
                margin=dict(l=0, r=0, t=40, b=100),
                xaxis_tickangle=-35,
            )
            fig_dist.update_traces(textposition="outside")
            st.plotly_chart(fig_dist, use_container_width=True)

    # Right chart: Revenue Recovery Opportunities by Situation
    with col2:
        if category_df is not None and not category_df.empty:
            valid_situations = [
                "Situation 1: Cart barrier",
                "Situation 2: Discovery/appeal problem",
                "Situation 3: Checkout friction",
            ]
            situation_labels = {
                "Situation 1: Cart barrier":               "Cart Barrier",
                "Situation 2: Discovery/appeal problem":   "Discovery Gap",
                "Situation 3: Checkout friction":          "Checkout Friction",
            }
            sit_revenue = (
                category_df[category_df["situation"].isin(valid_situations)]
                .groupby("situation")["actionable_lost_revenue"]
                .sum()
                .reset_index()
            )
            sit_revenue["situation_label"] = sit_revenue["situation"].map(situation_labels)
            sit_revenue = sit_revenue.sort_values("actionable_lost_revenue", ascending=False)
            fig_opp = px.bar(
                sit_revenue,
                x="situation_label", y="actionable_lost_revenue",
                title="Revenue Recovery Opportunities by Situation",
                labels={
                    "situation_label": "",
                    "actionable_lost_revenue": "Estimated Revenue Recovery ($)"
                },
                color_discrete_sequence=["#1d4ed8"],
                text="actionable_lost_revenue",
            )
            fig_opp.update_traces(
                texttemplate="%{y:$.2s}",
                textposition="outside"
            )
            fig_opp.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="DM Sans"),
                margin=dict(l=0, r=0, t=40, b=80),
                xaxis_tickangle=-20,
            )
            st.plotly_chart(fig_opp, use_container_width=True)

    st.markdown("### Why this matters")
    st.write("This dashboard identifies where the funnel is underperforming relative to category benchmarks, and surfaces which categories and sellers need action.")


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    st.title("📊 Clicks2Action: A Funnel Intelligence Dashboard 📊")
    st.caption("From Clicks to Conversions: A Spark-Driven Funnel Intelligence Dashboard with LLM Insights")
    
    product_df, events_df, signal_summary_df, brand_df, category_df, signal_v2_df = load_real_data()
    with st.spinner("Loading data..."):
        full_context = build_llm_context(product_df, events_df, signal_summary_df, brand_df, category_df, signal_v2_df)

    with st.sidebar:
        st.header("Dashboard Controls")
        level_1_options = sorted(product_df["cat_level_1"].dropna().unique().tolist()) if "cat_level_1" in product_df.columns else []
        selected_level_1 = st.multiselect("Category", level_1_options, default=[])
        level_2_base = product_df.copy()
        if selected_level_1 and "cat_level_1" in product_df.columns:
            level_2_base = level_2_base[level_2_base["cat_level_1"].isin(selected_level_1)]
        level_2_options = sorted(level_2_base["cat_level_2"].dropna().unique().tolist()) if "cat_level_2" in level_2_base.columns else []
        selected_level_2 = st.multiselect("Subcategory", level_2_options, default=[])
        sig_col = "signal_v2" if "signal_v2" in product_df.columns else "signal"
        signal_options = sorted(product_df[sig_col].dropna().unique().tolist()) if sig_col in product_df.columns else []
        selected_signals = st.multiselect("Opportunity Type", signal_options, default=[])
        priority_options = sorted(product_df["priority_tier"].dropna().unique().tolist()) if "priority_tier" in product_df.columns else []
        selected_priority = st.multiselect("Priority", priority_options, default=[])
        min_price = float(product_df["price"].min()) if "price" in product_df.columns else 0.0
        max_price = float(product_df["price"].max()) if "price" in product_df.columns else 1000.0
        price_range = st.slider("Price Range", min_price, max_price, (min_price, max_price))
        product_search = st.text_input("Search product / brand / category", placeholder="Try samsung, smartphone, 1002099")

    filtered_products = apply_product_filters(product_df, selected_level_1, selected_level_2, selected_signals, selected_priority, price_range, product_search)
    filtered_events = events_df[events_df["product_id"].isin(filtered_products["product_id"])] if {"product_id"}.issubset(events_df.columns) and {"product_id"}.issubset(filtered_products.columns) else events_df.copy()
    render_sidebar_chat(full_context)

    if filtered_products.empty:
        st.warning("No products match the current sidebar filters. Try widening the filters.")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Executive Snapshot",
        "Business Value",
        "Platform Analysis",
        "Seller Dashboard"
    ])

    with tab1:
        st.session_state.active_tab = "Executive Snapshot"
        render_executive_snapshot_tab(filtered_products, category_df, brand_df)
    
    with tab2:
        st.session_state.active_tab = "Business Value"
        render_business_value_tab(
            filtered_products,
            signal_v2_df if not signal_v2_df.empty else signal_summary_df,
            category_df
        )
    
    with tab3:
        st.session_state.active_tab = "Platform Analysis"
        st.session_state.role = "platform"
        platform_view(filtered_products, filtered_events, brand_df, category_df, full_context)
    
    with tab4:
        st.session_state.active_tab = "Seller Dashboard"
        st.session_state.role = "seller"
        seller_view(filtered_products, filtered_events, full_context)


    with st.expander("Technical details", expanded=False):
        st.write("Products shape:", product_df.shape)
        st.write("Filtered products shape:", filtered_products.shape)
        st.write("Events shape:", events_df.shape)
        st.write("Filtered events shape:", filtered_events.shape)
        st.write("Signal summary shape:", signal_summary_df.shape)
        st.write("Signal v2 shape:", signal_v2_df.shape)
        st.write("Brand shape:", brand_df.shape)
        st.write("Category shape:", category_df.shape)
        st.write("Data path:", str(BASE_PATH))


if __name__ == "__main__":
    main()
