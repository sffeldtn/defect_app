import streamlit as st
import pandas as pd
import numpy as np

st.title("CFAT Defect Analysis Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # --- Step 1: Validate required columns ---
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

    # --- Step 2: Correctly convert `was_audited` to boolean ---
    # Handle common representations (Yes/No, True/False, 1/0)
    if df["was_audited"].dtype == "object":
        df["was_audited"] = df["was_audited"].map({
            "Yes": True, "No": False,
            "True": True, "False": False,
            "1": True, "0": False
        }).fillna(False)  # Handle unexpected values
    else:
        df["was_audited"] = df["was_audited"].astype(bool)

    # --- Step 3: Convert defect columns to boolean ---
    defect_columns = [
        "audit_grammar_mistakes_serious", "audit_inappropriate_language",
        "audit_innacurate_serious", "audit_nonsensical_language",
        "audit_not_concise_serious",
        "audit_grammar_mistakes_soft", "audit_innacurate_soft",
        "audit_not_concise_soft",
        "original_grammar_mistakes_soft", "original_innacurate_soft",
        "original_not_concise_soft"
    ]
    
    for col in defect_columns:
        if df[col].dtype == "object":
            # Handle string representations (e.g., "True"/"False", "Yes"/"No")
            df[col] = df[col].map({
                "True": True, "False": False,
                "Yes": True, "No": False,
                "1": True, "0": False
            }).fillna(False)
        df[col] = df[col].astype(bool)  # Ensure all are boolean

    total_records = len(df)

    # --- Step 4: Compute P0 counts (serious defects) ---
    p0_cols = [
        "audit_grammar_mistakes_serious",
        "audit_inappropriate_language",
        "audit_innacurate_serious",
        "audit_nonsensical_language",
        "audit_not_concise_serious"
    ]
    p0_counts = df[p0_cols].sum()

    # --- Step 5: Compute P1 counts (soft defects) ---
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
    
    p1_counts = pd.Series(index=p1_audit_cols)
    
    for audit_col, orig_col in original_map.items():
        # Use audit result if `was_audited` is True, else use original decision
        effective_values = np.where(
            df["was_audited"],
            df[audit_col],   # Use audit column when audited
            df[orig_col]      # Use original column when not audited
        )
        p1_counts[audit_col] = effective_values.sum()  # Count True values

    # --- Step 6: Summary metrics ---
    p0_free = ((df[p0_cols].sum(axis=1) == 0).sum())
    
    # Build effective P1 DataFrame for "any P1 defect" check
    effective_p1_df = pd.DataFrame()
    for audit_col, orig_col in original_map.items():
        effective_p1_df[audit_col] = np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        ).astype(bool)
    
    p1_any = effective_p1_df.any(axis=1)
    totally_defect_free = ((df[p0_cols].sum(axis=1) == 0) & ~p1_any).sum()

    # --- Step 7: Display metrics with 1 decimal place ---
    st.subheader("Summary Metrics")
    st.metric("Total Records", total_records)
    st.metric("Totally Defect Free", 
              f"{totally_defect_free} ({totally_defect_free/total_records:.1%})")
    st.metric("P0 Free", 
              f"{p0_free} ({p0_free/total_records:.1%})")

    # --- Step 8: Defect breakdown table ---
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
        "Count": list(p0_counts.values) + list(p1_counts.values.astype(int))
    })
    
    # Format percentages with 1 decimal place (e.g., 3.2%)
    breakdown["Percentage"] = breakdown["Count"] / total_records
    breakdown["Percentage"] = breakdown["Percentage"].map("{:.1%}".format)
    
    st.dataframe(breakdown)
