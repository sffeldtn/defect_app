import streamlit as st
import pandas as pd
import numpy as np

st.title("CFAT Defect Analysis Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

if uploaded_file:
    # ---- Load data ----
    df = pd.read_excel(uploaded_file)
    
    # Verify required columns exist
    required_cols = [
        "was_audited",
        "audit_grammar_mistakes_serious", "audit_inappropriate_language",
        "audit_innacurate_serious", "audit_nonsensical_language",
        "audit_not_concise_serious",
        "audit_grammar_mistakes_soft", "audit_innacurate_soft",
        "audit_not_concise_soft",
        "original_grammar_mistakes_soft", "original_innacurate_soft",
        "original_not_concise_soft"
    ]
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required column(s): {', '.join(missing)}")
        st.stop()

    # Ensure correct data types
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

    # ---- P1 defect columns mapping ----
    # Map audit columns to their original counterparts
    p1_audit_cols = [
        "audit_grammar_mistakes_soft",
        "audit_innacurate_soft",
        "audit_not_concise_soft"
    ]
    
    original_map = {
        "audit_grammar_mistakes_soft": "original_grammar_mistakes_soft",
        "audit_innacurate_soft":      "original_innacurate_soft",
        "audit_not_concise_soft":     "original_not_concise_soft"
    }

    # ---- Compute P0 counts ----
    p0_counts = df[p0_cols].eq(True).sum()

    # ---- Compute P1 counts (audit OR original based on was_audited) ----
    p1_counts = pd.Series(index=p1_audit_cols)
    
    for audit_col, orig_col in original_map.items():
        # Use audit result if audited, otherwise use original decision
        effective_values = np.where(
            df["was_audited"], 
            df[audit_col],      # audited rows: use audit column
            df[orig_col]        # unaudited rows: use original column
        )
        p1_counts[audit_col] = effective_values.eq(True).sum()

    # ---- Summary metrics ----
    p0_free = (df[p0_cols].eq(True).sum(axis=1) == 0).sum()
    
    # Create effective P1 DataFrame for "any P1 defect" calculation
    effective_p1_df = pd.DataFrame()
    for audit_col, orig_col in original_map.items():
        effective_p1_df[audit_col] = np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        )
    
    p1_any = effective_p1_df.eq(True).any(axis=1)
    totally_defect_free = ((df[p0_cols].eq(True).sum(axis=1) == 0) & ~p1_any).sum()

    # Display metrics with WHOLE NUMBER percentages (3% instead of 0.3%)
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
    
    # Format percentages as WHOLE NUMBERS (3% instead of 0.3%)
    breakdown["Percentage"] = breakdown["Count"] / total_records
    breakdown["Percentage"] = breakdown["Percentage"].map("{:.0%}".format)
    
    st.dataframe(breakdown)
