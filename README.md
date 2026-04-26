# 🛍️ From Clicks to Actions: Spark-Powered Funnel Analysis with LLM-Driven Recommendations

> **This project repository is created in partial fulfillment of the requirements for the Big Data Analytics course offered by the Master of Science in Business Analytics program at the Carlson School of Management, University of Minnesota.**

---

**Team**: Team 4

**Members**: Shang Chi Hsu, Xiang Li, Ashwini Manokar, Isabel O'Grady, Meenakshi Narendra

---

## 📌 Project Overview

This project builds an **E-Commerce Funnel Intelligence System** that identifies conversion gaps, quantifies lost revenue, and surfaces actionable recommendations across products, brands, and categories — all grounded in large-scale clickstream data from a real multi-category e-commerce platform.

The system combines big data processing (Apache Spark / Databricks), behavioral signal engineering, and an LLM-powered analyst interface to help platform operators and sellers make data-driven decisions about where and how to improve conversion performance.

---

## 🎯 Executive Summary

Online retailers lose significant revenue not from lack of traffic, but from invisible friction in the purchase funnel. A shopper who views a product but never adds it to cart, or adds to cart but never checks out, represents both a missed conversion and a diagnosable pattern.

Using over two months of behavioral clickstream data (October–November 2019) from a large e-commerce marketplace, this project engineered a full-stack funnel intelligence pipeline that:

- **Processes millions of events** at scale using Apache Spark on Databricks, sampling sessions to balance speed and statistical fidelity
- **Defines and audits 15+ funnel metrics** at the session, user, product, brand, and category level, with explicit reliability classifications for sampled vs. full-data contexts
- **Classifies products into behavioral signals** using a situation-aware framework — the same metric (e.g. low View→Cart rate) is diagnosed differently depending on whether users in that category typically buy through the cart or directly
- **Estimates lost revenue** per product, brand, and category to rank opportunities by business impact
- **Deploys an interactive Streamlit dashboard** with an embedded LLM analyst (powered by Azure OpenAI) that answers natural-language questions across all data tables in real time

The result is a reproducible, scalable intelligence layer that transforms raw clickstream logs into prioritized, revenue-linked action queues for platform operators and sellers.

---

## 🗂️ Project Files

| File | Description |
|---|---|
| `funnel_analysis.ipynb` | PySpark notebook (Databricks) — full pipeline from raw data to dashboard CSV outputs, with metric definitions and design rationale |
| `TrendsMarketDashboard_v5.py` | Streamlit dashboard with role-based views (Platform Operator & Seller), funnel drilldowns, product action queue, and embedded Azure OpenAI chat analyst |
| `DATA_DICTIONARY.md` | Full column-level documentation for all three dashboard output files |
| `flier.pdf` | One-page project poster summarising the problem, architecture, and key results |

---

## 📊 Dataset

**eCommerce behavior data from a multi-category store** — October & November 2019
([Kaggle](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store?select=2019-Oct.csv))

~28M events across ~9M sessions covering view, cart, and purchase actions.

---

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| Data Processing | Apache Spark, PySpark, Databricks |
| Analysis | Python, pandas, NumPy |
| Visualization | Plotly, Streamlit, Matplotlib, Seaborn |
| LLM / AI | Azure OpenAI |
| Environment | Databricks (notebook), Streamlit (dashboard) |

---

## ⚙️ Setup & Usage

### Requirements

- Python 3.9+
- Azure OpenAI resource *(for AI chat; dashboard works without it)*
- Databricks workspace *(only for re-running `funnel_analysis.ipynb`)*

### Running the Dashboard

**1. Install dependencies**

```bash
pip install streamlit plotly pandas openai
```

**2. Download the data**

Download the pre-processed CSV files from Google Drive and place them in a `data/` folder inside the project directory:

📁 [Download dashboard data (Google Drive)](https://drive.google.com/drive/folders/1ZeW9jHcoaIxO9ER95jfT7aQLZYBZmsYX?usp=sharing)

Your folder structure should look like this:
```
Team4_BigData/
└── data/
    ├── dashboard_products_v2.csv
    ├── dashboard_category_v2.csv
    ├── dashboard_brand_v2.csv
    ├── dashboard_events.csv
    └── dashboard_signal_summary_v2.csv
```

**3. Set environment variables** *(optional — only needed for AI chat feature)*

```bash
# macOS / Linux
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your_api_key_here"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"

# Windows
set AZURE_OPENAI_API_KEY=your_api_key_here
# (repeat pattern for other variables)
```

**4. Launch**

```bash
streamlit run TrendsMarketDashboard_v5.py
```

Open `http://localhost:8501` in your browser.

### Re-running the Analysis Notebook (Optional)

1. Upload `funnel_analysis.ipynb` to a Databricks workspace with a PySpark cluster.
2. Confirm raw data is at `dbfs:/Volumes/msbabigdata/spark/trend_market/` (or update the path in §0).
3. Run all cells — the notebook outputs the three CSV files used by the dashboard.

---

## 🧠 Key Features

- 🔍 Funnel drop-off tracking across view → cart → purchase
- 🗂️ Situation-aware signal classification — same metric, different diagnosis depending on category purchase behaviour
- 🏷️ Product signal labels (e.g. Cart Barrier, Checkout Friction, Discovery Problem) with lost revenue estimates
- 📊 Interactive Streamlit dashboard with role-based views for operators and sellers
- 🤖 Embedded AI chat analyst powered by Azure OpenAI

---

## 📖 References & Credits

- Dataset: [eCommerce behavior data from multi-category store](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store) by Михаил Кечинов (Kaggle)
- Dashboard framework: [Streamlit](https://streamlit.io/)
- LLM integration: [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- Big data processing: [Apache Spark](https://spark.apache.org/) via [Databricks](https://www.databricks.com/)
