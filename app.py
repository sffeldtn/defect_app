import streamlit as st
import pandas as pd
import numpy as np

st.title("CFAT Defect Analysis Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

if uploaded_file:
    # Load data
    df = pd.read_excel(uploaded_file)
    
    # Validate required columns
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
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}")
        st.stop()

    df["was_audited"] = df["was_audited"].astype(bool)
    total_records = len(df)

    # P0 defect columns (serious defects)
    p0_cols = [
        "audit_grammar_mistakes_serious",
        "audit_inappropriate_language",
        "audit_innacurate_serious",
        "audit_nonsensical_language",
        "audit_not_concise_serious"
    ]

    # P1 defect mapping (soft defects)
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

    # Calculate P0 counts
    p0_counts = df[p0_cols].eq(True).sum()

    # Calculate P1 counts (use audit if audited, else original)
    p1_counts = pd.Series(index=p1_audit_cols)
    
    for audit_col, orig_col in original_map.items():
        # Use np.where to select between audit/original values
        effective_values = np.where(
            df["was_audited"],
            df[audit_col],  # Use audit result if audited
            df[orig_col]    # Fall back to original if not audited
        )
        
        # COUNT TRUES DIRECTLY (NO .eq(True) NEEDED)
        p1_counts[audit_col] = effective_values.sum()  # <--- FIXED HERE

    # Summary metrics
    p0_free = (df[p0_cols].eq(True).sum(axis=1) == 0).sum()
    
    # Build effective P1 DataFrame for "any P1 defect" check
    effective_p1_df = pd.DataFrame()
    for audit_col, orig_col in original_map.items():
        effective_p1_df[audit_col] = np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        ).astype(bool)  # Ensure boolean type
    
    p1_any = effective_p1_df.any(axis=1)
    totally_defect_free = ((df[p0_cols].eq(True).sum(axis=1) == 0) & ~p1_any).sum()

    # Display metrics with WHOLE-NUMBER percentages
    st.subheader("Summary Metrics")
    st.metric("Total Records", total_records)
    st.metric("Totally Defect Free", f"{totally_defect_free} ({totally_defect_free/total_records:.0%})")
    st.metric("P0 Free",           f"{p0_free} ({p0_free/total_records:.0%})")

    # Defect breakdown table
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
        "Count": list(p0_counts.values) + list(p1_counts.values.astype(int))  # Ensure integers
    })
    
    # Format percentages as whole numbers (e.g., 3% instead of 0.3%)
    breakdown["Percentage"] = breakdown["Count"] / total_records
    breakdown["Percentage"] = breakdown["Percentage"].map("{:.0%}".format)
    
    st.dataframe(breakdown)
