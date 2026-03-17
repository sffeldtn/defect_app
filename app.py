import streamlit as st
import pandas as pd
import numpy as np


st.title("CFAT Defect Analysis Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

if uploaded_file:
    # ---- Load data ----
    df = pd.read_excel(uploaded_file)

    # Make sure the required columns are present
    required_cols = [
        "was_audited",
        "audit_grammar_mistakes_serious", "audit_inappropriate_language",
        "audit_innacurate_serious", "audit_nonsensical_language",
        "audit_not_concise_serious",
        "audit_grammar_mistakes_soft", "audit_innacurate_soft",
        "audit_not_concise_soft",
        "grammar_mistakes_soft", "innacurate_soft", "not_concise_soft"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required column(s): {', '.join(missing)}")
        st.stop()

    # Ensure the audit flag is treated as a boolean
    df["was_audited"] = df["was_audited"].astype(bool)

    total_records = len(df)

    # ---- P0 defect columns (unchanged) ----
    p0_cols = [
        "audit_grammar_mistakes_serious",
        "audit_inappropriate_language",
        "audit_innacurate_serious",
        "audit_nonsensical_language",
        "audit_not_concise_serious"
    ]

    # ---- P1 defect columns (audit version) ----
    p1_audit_cols = [
        "audit_grammar_mistakes_soft",
        "audit_innacurate_soft",
        "audit_not_concise_soft"
    ]

    # Mapping from audit column → original‑decision column
    original_map = {
        "audit_grammar_mistakes_soft": "grammar_mistakes_soft",
        "audit_innacurate_soft":      "innacurate_soft",
        "audit_not_concise_soft":     "not_concise_soft"
    }

    # ---- Compute P0 counts (same as before) ----
    p0_counts = df[p0_cols].eq(True).sum()

    # ---- Compute P1 counts – use audit if was_audited=True, otherwise original ----
    p1_counts = pd.Series(index=p1_audit_cols)
    for audit_col, orig_col in original_map.items():
        # Select the appropriate boolean value for each row
        effective = np.where(
            df["was_audited"],          # condition
            df[audit_col],              # value if True (audit result)
            df[orig_col]                # value if False (original decision)
        )
        p1_counts[audit_col] = effective.eq(True).sum()

    # ---- Summary metrics ----
    # P0‑free rows (no serious defects)
    p0_free = (df[p0_cols].eq(True).sum(axis=1) == 0).sum()

    # Build a DataFrame of effective P1 values to decide if *any* soft defect exists
    effective_p1_df = pd.DataFrame()
    for audit_col, orig_col in original_map.items():
        effective_p1_df[audit_col] = np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        )
    p1_any = effective_p1_df.eq(True).any(axis=1)

    # Totally defect‑free = no P0 defects **and** no P1 defects
    totally_defect_free = ((df[p0_cols].eq(True).sum(axis=1) == 0) & ~p1_any).sum()

    st.subheader("Summary Metrics")
    st.metric("Total Records", total_records)
    st.metric("Totally Defect Free", f"{totally_defect_free} ({totally_defect_free/total_records:.0%})")
    st.metric("P0 Free",           f"{p0_free} ({p0_free/total_records:.0%})")

    # ---- Defect breakdown table ----
    st.subheader("Defect Breakdown")
    breakdown = pd.DataFrame({
        "Defect": [
            "Serious Grammar",
            "Inappropriate Language",
            "Serious Inaccuracy",
            "Nonsensical Language",
            "Serious Concise",
            "Grammar Soft",
            "Inaccurate Soft",
            "Concise Soft"
        ],
        "Count": list(p0_counts.values) + list(p1_counts.values)
    })

    # Compute percentages and format as “X%” (no decimal percentages)
    breakdown["Percentage"] = breakdown["Count"] / total_records
    breakdown["Percentage"] = breakdown["Percentage"].map("{:.0%}".format)

    st.dataframe(breakdown)
