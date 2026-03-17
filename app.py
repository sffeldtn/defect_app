import streamlit as st
import pandas as pd
import numpy as np

st.title("CFAT Defect Analysis Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # --- Validate required columns ---
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

    # --- Prepare data ---
    # Convert `was_audited` to boolean (handle Yes/No, True/False, 1/0)
    if df["was_audited"].dtype == "object":
        df["was_audited"] = df["was_audited"].map({
            "Yes": True, "No": False,
            "True": True, "False": False,
            "1": True, "0": False
        }).fillna(False)
    else:
        df["was_audited"] = df["was_audited"].astype(bool)
    
    # Convert all defect columns to boolean
    defect_cols = [
        "audit_grammar_mistakes_serious", "audit_inappropriate_language",
        "audit_innacurate_serious", "audit_nonsensical_language",
        "audit_not_concise_serious",
        "audit_grammar_mistakes_soft", "audit_innacurate_soft",
        "audit_not_concise_soft",
        "original_grammar_mistakes_soft", "original_innacurate_soft",
        "original_not_concise_soft"
    ]
    
    for col in defect_cols:
        if df[col].dtype == "object":
            df[col] = df[col].map({
                'True': True, 'False': False,
                'Yes': True, 'No': False,
                '1': True, '0': False
            }).fillna(False)
        df[col] = df[col].astype(bool)

    total_records = len(df)

    # --------------------------------------------------------------
    # 1. SERIOUS DEFECTS (P0) - AUDIT ONLY
    # --------------------------------------------------------------
    p0_cols = [
        "audit_grammar_mistakes_serious",
        "audit_inappropriate_language",
        "audit_innacurate_serious",
        "audit_nonsensical_language",
        "audit_not_concise_serious"
    ]
    
    # Count TRUE in audit columns (P0 defects)
    p0_counts = df[p0_cols].sum().astype(int)
    
    # --------------------------------------------------------------
    # 2. SOFT DEFECTS (P1) - COMBINE AUDIT/ORIGINAL
    # --------------------------------------------------------------
    p1_audit_cols = [
        "audit_grammar_mistakes_soft",
        "audit_innacurate_soft",
        "audit_not_concise_soft"
    ]
    
    original_cols = [
        "original_grammar_mistakes_soft",
        "original_innacurate_soft",
        "original_not_concise_soft"
    ]
    
    p1_counts = pd.Series(index=p1_audit_cols, dtype=int)
    
    for audit_col, orig_col in zip(p1_audit_cols, original_cols):
        # Use audit if audited, else original
        effective = np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        ).astype(bool)
        p1_counts[audit_col] = effective.sum().astype(int)

    # --------------------------------------------------------------
    # 3. TOTALLY DEFECT FREE - NO P0 AND NO P1 DEFECTS
    # --------------------------------------------------------------
    # P0 defects: any audit_P0 column is True
    has_p0_defect = df[p0_cols].any(axis=1)
    
    # P1 defects: any combined P1 column is True
    has_p1_defect = pd.Series(False, index=df.index)
    for audit_col, orig_col in zip(p1_audit_cols, original_cols):
        has_p1_defect |= np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        ).astype(bool)
    
    totally_defect_free = ((~has_p0_defect) & (~has_p1_defect)).sum().astype(int)

    # --------------------------------------------------------------
    # 4. P0 FREE - NO SERIOUS DEFECTS (AUDIT ONLY)
    # --------------------------------------------------------------
    p0_free = (~df[p0_cols].any(axis=1)).sum().astype(int)

    # --------------------------------------------------------------
    # DISPLAY METRICS (1 DECIMAL PLACE)
    # --------------------------------------------------------------
    st.subheader("Summary Metrics")
    st.metric("Total Records", total_records)
    st.metric("Totally Defect Free", 
              f"{totally_defect_free} ({totally_defect_free / total_records:.1%})")
    st.metric("P0 Free", 
              f"{p0_free} ({p0_free / total_records:.1%})")

    # --------------------------------------------------------------
    # DEFECT BREAKDOWN TABLE
    # --------------------------------------------------------------
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
    
    breakdown["Percentage"] = breakdown["Count"] / total_records
    breakdown["Percentage"] = breakdown["Percentage"].map("{:.1%}".format)
    
    st.dataframe(breakdown)
