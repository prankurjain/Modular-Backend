"""Streamlit UI for semiconductor ingestion and alternative search."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st


DEFAULT_API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")


st.set_page_config(
    page_title="Semiconductor Alternative Finder",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
      :root {
        --glass-bg: rgba(255, 255, 255, 0.08);
        --glass-border: rgba(255, 255, 255, 0.24);
        --soft-text: #dbe7ff;
        --brand-1: #8b5cf6;
        --brand-2: #06b6d4;
      }

      .stApp {
        background:
          radial-gradient(circle at 0% 0%, rgba(139, 92, 246, 0.25), transparent 35%),
          radial-gradient(circle at 100% 0%, rgba(6, 182, 212, 0.25), transparent 35%),
          linear-gradient(135deg, #0b1020 0%, #111b34 42%, #172554 100%);
      }

      .block-container {
        padding-top: 1rem;
      }

      [data-testid="stSidebar"] {
        background: rgba(9, 15, 30, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
      }

      h1, h2, h3, h4, p, label, .stMarkdown, .stCaption {
        color: #f8fafc !important;
      }

      .hero {
        border-radius: 20px;
        padding: 1.35rem;
        margin-bottom: 1rem;
        background: linear-gradient(120deg, rgba(139, 92, 246, 0.35), rgba(6, 182, 212, 0.3));
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 12px 35px rgba(8, 15, 35, 0.45);
      }

      .glass-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.95rem;
        box-shadow: 0 10px 22px rgba(2, 6, 23, 0.35);
        backdrop-filter: blur(8px);
      }

      .product-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.13) 0%, rgba(255,255,255,0.06) 100%);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.9rem;
      }

      .score-pill {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.82rem;
        color: white;
        background: linear-gradient(135deg, var(--brand-1), var(--brand-2));
      }

      .pill {
        display: inline-block;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        margin-right: 0.35rem;
        border: 1px solid rgba(255,255,255,0.25);
        color: var(--soft-text);
      }

      .pros-list li::marker { color: #22c55e; }
      .cons-list li::marker { color: #ef4444; }

      [data-baseweb="tab-list"] {
        gap: 0.7rem;
      }

      [data-baseweb="tab"] {
        background: rgba(255,255,255,0.09);
        border: 1px solid rgba(255,255,255,0.17);
        border-radius: 12px;
        padding: 0.45rem 0.9rem;
      }

      .stButton>button {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.25);
        background: linear-gradient(120deg, rgba(139,92,246,0.6), rgba(6,182,212,0.55));
        color: white;
        font-weight: 600;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>⚡ Semiconductor Product Intelligence Studio</h1>
      <p>Ingest product datasets, discover alternatives, and explore your catalog in a material-style dashboard.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Backend Connection")
    api_base = st.text_input("API Base URL", value=DEFAULT_API_BASE)
    st.caption("Set this to your FastAPI service endpoint.")


def _request(method: str, path: str, **kwargs) -> tuple[bool, Any]:
    url = f"{api_base.rstrip('/')}{path}"
    try:
        resp = requests.request(method, url, timeout=60, **kwargs)
        if resp.status_code >= 400:
            return False, {"status": resp.status_code, "detail": resp.text}
        return True, resp.json()
    except Exception as exc:
        return False, {"detail": str(exc)}


def _pros_cons(base: dict, candidate: dict) -> tuple[list[str], list[str]]:
    pros: list[str] = []
    cons: list[str] = []

    checks = [
        ("vds_max_v", "Higher/Equal Vds", lambda b, c: c >= b),
        ("id_max_a", "Higher/Equal Id", lambda b, c: c >= b),
        ("rds_on_ohm", "Lower/Equal Rds(on)", lambda b, c: c <= b),
        ("gate_charge_nc", "Lower/Equal Gate Charge", lambda b, c: c <= b),
    ]

    for field, label, fn in checks:
        b = base.get(field)
        c = candidate.get(field)
        if b is None or c is None:
            continue
        if fn(b, c):
            pros.append(f"{label}: base={b}, candidate={c}")
        else:
            cons.append(f"{label} not met: base={b}, candidate={c}")

    if candidate.get("package_type") and base.get("package_type"):
        if str(candidate["package_type"]).lower() == str(base["package_type"]).lower():
            pros.append(f"Package match: {candidate['package_type']}")
        else:
            cons.append(f"Package differs: base={base['package_type']}, candidate={candidate['package_type']}")

    return pros, cons


def _render_alt_card(position: int, candidate: dict, pros: list[str], cons: list[str]):
    score = candidate.get("rule_score", candidate.get("similarity_score", "NA"))
    tags = [candidate.get("category"), candidate.get("package_type")]
    tags = [t for t in tags if t]

    tag_html = "".join([f'<span class="pill">{tag}</span>' for tag in tags])
    st.markdown(
        f"""
        <div class="product-card">
          <h4 style="margin-bottom:0.2rem;">#{position} {candidate.get('part_number') or candidate.get('product_name', 'Unknown Product')}</h4>
          <span class="score-pill">Match Score: {score}</span>
          <div style="margin-top:0.55rem;">{tag_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown("**✅ Pros**")
        if pros:
            st.markdown("<ul class='pros-list'>" + "".join([f"<li>{p}</li>" for p in pros]) + "</ul>", unsafe_allow_html=True)
        else:
            st.write("No major advantages from configured checks.")

    with right:
        st.markdown("**⚠️ Cons**")
        if cons:
            st.markdown("<ul class='cons-list'>" + "".join([f"<li>{c}</li>" for c in cons]) + "</ul>", unsafe_allow_html=True)
        else:
            st.write("No major drawbacks from configured checks.")


tab_ingest, tab_find, tab_products = st.tabs([
    "📥 Ingest Data",
    "🔎 Find Alternatives",
    "📦 Product Catalog",
])

with tab_ingest:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Data Ingestion")
    csv_path = st.text_input("CSV Path", value="data/products.csv")
    if st.button("Run /ingest-data", use_container_width=True):
        ok, payload = _request("POST", "/ingest-data", params={"csv_path": csv_path})
        if ok:
            st.success(f"Ingest completed: {payload.get('ingested', 0)} ingested, {payload.get('skipped', 0)} skipped")
            if payload.get("errors"):
                st.warning("Some rows failed:")
                st.json(payload["errors"])
        else:
            st.error(payload)
    st.markdown("</div>", unsafe_allow_html=True)

with tab_find:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Find Alternatives")
    c1, c2 = st.columns([3, 1])
    with c1:
        part_number = st.text_input("Part Number", value="IRFB3207")
    with c2:
        top_k = st.number_input("Top K", min_value=1, max_value=50, value=8)

    if st.button("Search /find-alternative", use_container_width=True):
        ok, payload = _request(
            "POST",
            "/find-alternative",
            json={"part_number": part_number, "top_k": int(top_k)},
        )
        if not ok:
            st.error(payload)
        else:
            base = payload.get("base_product", {})
            alternatives = payload.get("alternatives", [])
            metrics = st.columns(3)
            metrics[0].metric("Alternatives", len(alternatives))
            metrics[1].metric("Search Mode", str(payload.get("search_mode", "N/A")))
            metrics[2].metric("Top K", int(top_k))

            st.markdown("### Base Product")
            st.json(base)

            st.markdown("### Candidate Cards")
            if not alternatives:
                st.info("No alternatives found.")

            for idx, candidate in enumerate(alternatives, start=1):
                pros, cons = _pros_cons(base, candidate)
                _render_alt_card(idx, candidate, pros, cons)
                with st.expander("View raw product data"):
                    st.json(candidate)
    st.markdown("</div>", unsafe_allow_html=True)

with tab_products:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Ingested Product Catalog")
    col1, col2 = st.columns([2, 1])
    with col1:
        category = st.text_input("Category filter (optional)", value="")
    with col2:
        limit = st.number_input("Limit", min_value=1, max_value=5000, value=200)

    if st.button("Load /products", use_container_width=True):
        params = {"limit": int(limit)}
        if category.strip():
            params["category"] = category.strip()
        ok, payload = _request("GET", "/products", params=params)
        if not ok:
            st.error(payload)
        else:
            products = payload.get("products", [])
            st.success(f"Loaded {payload.get('total', 0)} products")
            if products:
                df = pd.DataFrame(products)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No products found.")
    st.markdown("</div>", unsafe_allow_html=True)
