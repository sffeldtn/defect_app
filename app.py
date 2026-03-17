import streamlit as st
import pandas as pd
import numpy as np

st.title("CFAT Defect Analysis Tool")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xlsm"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # ----------------------------------------------------
    # VALIDATE COLUMNS (MATCH YOUR VBA COLUMN LETTERS)
    # ----------------------------------------------------
    # Map VBA column letters to actual column names in your data
    column_mapping = {
        # P0 audit columns (M, U, Y, AG, AK)
        "audit_grammar_mistakes_serious": "M",  # e.g., column M = audit_grammar_mistakes_serious
        "audit_inappropriate_language": "U",
        "audit_innacurate_serious": "Y",
        "audit_nonsensical_language": "AG",
        "audit_not_concise_serious": "AK",
        
        # P1 annotator columns (P, AB, AN)
        "original_grammar_mistakes_soft": "P",
        "original_innacurate_soft": "AB",
        "original_not_concise_soft": "AN",
        
        # P1 audit columns (Q, AC, AO)
        "audit_grammar_mistakes_soft": "Q",
        "audit_innacurate_soft": "AC",
        "audit_not_concise_soft": "AO",
        
        # was_audited flag (AZ)
        "was_audited": "AZ"
    }
    
    # Check if mapped columns exist
    required_columns = list(column_mapping.keys())
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {', '.join(missing)}. Ensure your Excel uses the exact column names.")
        st.stop()
    
    # ----------------------------------------------------
    # PREPARE DATA (EXACTLY LIKE VBA)
    # ----------------------------------------------------
    # Convert was_audited to boolean (handle Yes/No, True/False, 1/0)
    df["was_audited"] = df["was_audited"].astype(str).str.upper().map({
        "TRUE": True, "FALSE": False,
        "YES": True, "NO": False,
        "1": True, "0": False
    }).fillna(False)
    
    # Convert all defect columns to boolean (VBA uses "TRUE"/"FALSE" strings)
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
        df[col] = df[col].astype(str).str.upper().map({
            "TRUE": True, "FALSE": False,
            "YES": True, "NO": False,
            "1": True, "0": False
        }).fillna(False)
    
    total_records = len(df)
    
    # ----------------------------------------------------
    # 1. P0 DEFECTS (SERIOUS) - AUDIT ONLY (DIRECT COUNT)
    # ----------------------------------------------------
    p0_cols = [
        "audit_grammar_mistakes_serious",
        "audit_inappropriate_language",
        "audit_innacurate_serious",
        "audit_nonsensical_language",
        "audit_not_concise_serious"
    ]
    
    p0_counts = df[p0_cols].sum().astype(int)
    
    # ----------------------------------------------------
    # 2. P1 DEFECTS (SOFT) - COMBINED LOGIC
    # ----------------------------------------------------
    p1_defect_types = {
        "Grammar Soft": ("audit_grammar_mistakes_soft", "original_grammar_mistakes_soft"),
        "Inaccurate Soft": ("audit_innacurate_soft", "original_innacurate_soft"),
        "Concise Soft": ("audit_not_concise_soft", "original_not_concise_soft")
    }
    
    p1_counts = {}
    
    for defect_name, (audit_col, orig_col) in p1_defect_types.items():
        # Replicate VBA logic: use audit if was_audited=True, else original
        effective = np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        )
        p1_counts[defect_name] = effective.sum().astype(int)
    
    # ----------------------------------------------------
    # 3. TOTALLY DEFECT FREE - NO P0 AND NO P1 DEFECTS
    # ----------------------------------------------------
    # P0 defects: any audit_P0 column is True
    has_p0 = df[p0_cols].any(axis=1)
    
    # P1 defects: any combined P1 column is True
    has_p1 = pd.Series(False, index=df.index)
    for _, (audit_col, orig_col) in p1_defect_types.items():
        has_p1 |= np.where(
            df["was_audited"],
            df[audit_col],
            df[orig_col]
        )
    
    totally_defect_free = ((~has_p0) & (~has_p1)).sum().astype(int)
    
    # ----------------------------------------------------
    # 4. P0 FREE - NO SERIOUS DEFECTS (AUDIT ONLY)
    # ----------------------------------------------------
    p0_free = (~has_p0).sum().astype(int)
    
    # ----------------------------------------------------
    # DISPLAY METRICS (EXACTLY LIKE VBA OUTPUT)
    # ----------------------------------------------------
    st.subheader("Summary Metrics")
    st.metric("Total Records", total_records)
    st.metric("Totally Defect Free", 
              f"{totally_defect_free} ({totally_defect_free / total_records:.1%})")
    st.metric("P0 Free", 
              f"{p0_free} ({p0_free / total_records:.1%})")
    
    # ----------------------------------------------------
    # DEFECT BREAKDOWN TABLE (MATCHING VBA FORMAT)
    # ----------------------------------------------------
    st.subheader("Defect Breakdown")
    
    breakdown_data = []
    # P0 defects (audit-only)
    for col, count in p0_counts.items():
        breakdown_data.append({
            "Defect": col.replace("audit_", "").replace("_", " ").title(),
            "Category": "P0",
            "Count": count,
            "Percentage": count / total_records
        })
    
    # P1 defects (combined)
    for defect_name, count in p1_counts.items():
        breakdown_data.append({
            "Defect": defect_name,
            "Category": "P1",
            "Count": count,
            "Percentage": count / total_records
        })
    
    breakdown_df = pd.DataFrame(breakdown_data)
    breakdown_df["Percentage"] = breakdown_df["Percentage"].map("{:.1%}".format)
    
    st.dataframe(breakdown_df[["Defect", "Category", "Count", "Percentage"]])
