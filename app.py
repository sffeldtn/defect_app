import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Defect Analysis App", layout="wide")
st.title("Defect Analysis Automation")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xlsm"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ------------------------------
    # Define defect columns
    # ------------------------------
    # P0 - serious defects (auditor only)
    p0_cols = [
        "audit_grammar_mistakes_serious",
        "audit_innacurate_serious",
        "audit_inappropriate_language",
        "audit_nonsensical_language",
        "audit_not_concise_serious"
    ]

    # P1 - soft defects
    p1_auditor_cols = [
        "audit_grammar_mistakes_soft",
        "audit_innacurate_soft",
        "audit_not_concise_soft"
    ]
    p1_annotator_cols = [
        "original_grammar_mistakes_soft",
        "original_innacurate_soft",
        "original_not_concise_soft"
    ]

    was_audited_col = "was_audited"
    total_records = len(df)

    # ------------------------------
    # Check columns exist
    # ------------------------------
    existing_p0_cols = [col for col in p0_cols if col in df.columns]
    missing_p0_cols = [col for col in p0_cols if col not in df.columns]
    if missing_p0_cols:
        st.warning(f"The following P0 columns are missing and will be skipped: {missing_p0_cols}")

    existing_p1_auditor_cols = [col for col in p1_auditor_cols if col in df.columns]
    existing_p1_annotator_cols = [col for col in p1_annotator_cols if col in df.columns]
    missing_p1_cols = list(set(p1_auditor_cols + p1_annotator_cols) - set(existing_p1_auditor_cols + existing_p1_annotator_cols))
    if missing_p1_cols:
        st.warning(f"The following P1 columns are missing and will be skipped: {missing_p1_cols}")

    if not existing_p0_cols and not existing_p1_annotator_cols:
        st.error("No valid defect columns were found in your uploaded file.")
        st.stop()

    # ------------------------------
    # Calculate P0 defects (only auditor totals)
    # ------------------------------
    p0_counts = {col: df[col].sum() for col in existing_p0_cols}

    # ------------------------------
    # Calculate P1 defects (audited + original)
    # ------------------------------
    p1_counts = {}
    for ann_col, aud_col in zip(existing_p1_annotator_cols, existing_p1_auditor_cols):
        audited_true_count = ((df[was_audited_col] == True) & (df[aud_col] == True)).sum()
        not_audited_count = ((df[was_audited_col] == False) & (df[ann_col] == True)).sum()
        p1_counts[ann_col] = audited_true_count + not_audited_count

    # ------------------------------
    # Summary metrics
    # ------------------------------
    totally_defect_free = 0
    p0_free = 0

    for idx, row in df.iterrows():
        has_p0 = any(row[col] == True for col in existing_p0_cols)
        has_p1 = False
        for ann_col, aud_col in zip(existing_p1_annotator_cols, existing_p1_auditor_cols):
            if row[was_audited_col]:
                has_p1 |= row[aud_col] == True
            else:
                has_p1 |= row[ann_col] == True
        if not has_p0 and not has_p1:
            totally_defect_free += 1
        if not has_p0:
            p0_free += 1

    # ------------------------------
    # Display summary metrics
    # ------------------------------
    st.subheader("Summary Metrics")
    st.write(f"Total records: {total_records}")
    st.write(f"Totally Defect-Free: {totally_defect_free} ({totally_defect_free/total_records*100:.1f}%)")
    st.write(f"P0-Free: {p0_free} ({p0_free/total_records*100:.1f}%)")
    st.write(f"With P0 Defects: {total_records - p0_free} ({(total_records - p0_free)/total_records*100:.1f}%)")

    # ------------------------------
    # Create defect breakdown table
    # ------------------------------
    defect_types = ["P0"] * len(existing_p0_cols) + ["P1"] * len(p1_counts)
    defect_names = existing_p0_cols + existing_p1_annotator_cols
    defect_totals = list(p0_counts.values()) + list(p1_counts.values())
    defect_percent = [f"{count/total_records*100:.1f}%" for count in defect_totals]

    defect_df = pd.DataFrame({
        "Defect Type": defect_types,
        "Defect Name": defect_names,
        "Count": defect_totals,
        "Percentage": defect_percent
    })

    st.subheader("Defect Breakdown")
    st.dataframe(defect_df, use_container_width=True)

    # ------------------------------
    # Download as Excel
    # ------------------------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
        defect_df.to_excel(writer, index=False, sheet_name="Defect Breakdown")
    output.seek(0)

    st.download_button(
        label="Download Full Report",
        data=output,
        file_name="defect_analysis_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
