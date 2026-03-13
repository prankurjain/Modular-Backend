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
      .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #0ea5e9 100%);
      }
      .block-container {
        padding-top: 1.2rem;
      }
      .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
      }
      .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 0.5rem 1rem;
      }
      h1, h2, h3, p, label {
        color: white !important;
      }
      .card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚡ Semiconductor Alternative Finder")
st.caption("Ingest data, search alternatives, and inspect catalog from a single UI.")


with st.sidebar:
    st.header("⚙️ Backend")
    api_base = st.text_input("API Base URL", value=DEFAULT_API_BASE)


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


tab_ingest, tab_find, tab_products = st.tabs([
    "📥 Ingest Data",
    "🔎 Find Alternatives",
    "📦 Ingested Products",
])


with tab_ingest:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Ingest From CSV")
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

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Ingest Demo JSON")
    demo_path = st.text_input("Demo JSON Path", value="data/demo_products.json")
    if st.button("Run /ingest-demo-data", use_container_width=True):
        ok, payload = _request("POST", "/ingest-demo-data", params={"path": demo_path})
        if ok:
            st.success(f"Demo ingest completed: {payload.get('ingested', 0)} ingested, {payload.get('skipped', 0)} skipped")
            if payload.get("errors"):
                st.warning("Some rows failed:")
                st.json(payload["errors"])
        else:
            st.error(payload)
    st.markdown("</div>", unsafe_allow_html=True)


with tab_find:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Find Alternative Products")
    c1, c2 = st.columns([3, 1])
    with c1:
        part_number = st.text_input("Part Number", value="IRFB3207")
    with c2:
        top_k = st.number_input("Top K", min_value=1, max_value=50, value=10)

    if st.button("Run /find-alternative", use_container_width=True):
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
            st.success(
                f"Found {len(alternatives)} alternatives. Mode: {payload.get('search_mode')} | Sources: {payload.get('sources', {})}"
            )
            st.write("### Base Product")
            st.json(base)

            st.write("### Alternatives with Pros & Cons")
            if not alternatives:
                st.info("No alternatives found.")
            for idx, candidate in enumerate(alternatives, start=1):
                pros, cons = _pros_cons(base, candidate)
                with st.expander(
                    f"#{idx} {candidate.get('part_number') or candidate.get('product_name')} "
                    f"(score={candidate.get('rule_score', candidate.get('similarity_score', 'NA'))})",
                    expanded=(idx == 1),
                ):
                    cols = st.columns(2)
                    with cols[0]:
                        st.markdown("**✅ Pros**")
                        if pros:
                            for p in pros:
                                st.write(f"- {p}")
                        else:
                            st.write("- No clear pros from configured checks")
                    with cols[1]:
                        st.markdown("**⚠️ Cons**")
                        if cons:
                            for c in cons:
                                st.write(f"- {c}")
                        else:
                            st.write("- No major cons from configured checks")
                    st.json(candidate)
    st.markdown("</div>", unsafe_allow_html=True)


with tab_products:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("All Ingested Products")
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
                st.dataframe(pd.DataFrame(products), use_container_width=True)
            else:
                st.info("No products found.")
    st.markdown("</div>", unsafe_allow_html=True)
