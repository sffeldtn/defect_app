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
    p0_cols = ["Serious Grammar", "Inappropriate Language", "Serious Inaccuracy",
               "Nonsensical Language", "Serious Concise"]

    p1_annotator_cols = ["Grammar Soft", "Inaccurate Soft", "Concise Soft"]
    p1_auditor_cols = ["Grammar Soft Auditor", "Inaccurate Soft Auditor", "Concise Soft Auditor"]

    was_audited_col = "was_audited"

    total_records = len(df)

    # ------------------------------
    # Calculate P0 defects (only auditor totals)
    # ------------------------------
    p0_counts = {col: df[col].sum() for col in p0_cols}

    # ------------------------------
    # Calculate P1 defects (conditional)
    # ------------------------------
    p1_counts = {}
    for ann_col, aud_col in zip(p1_annotator_cols, p1_auditor_cols):
        p1_counts[ann_col] = ((df[was_audited_col] == True) & (df[aud_col] == True)).sum() + \
                             ((df[was_audited_col] == False) & (df[ann_col] == True)).sum()

    # ------------------------------
    # Summary metrics
    # ------------------------------
    totally_defect_free = 0
    p0_free = 0

    for idx, row in df.iterrows():
        has_p0 = any(row[col] == True for col in p0_cols)
        has_p1 = False
        for ann_col, aud_col in zip(p1_annotator_cols, p1_auditor_cols):
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
    st.write(f"Totally Defect-Free: {totally_defect_free} ({totally_defect_free/total_records:.2%})")
    st.write(f"P0-Free: {p0_free} ({p0_free/total_records:.2%})")
    st.write(f"With P0 Defects: {total_records - p0_free} ({(total_records - p0_free)/total_records:.2%})")

    # ------------------------------
    # Create defect breakdown table
    # ------------------------------
    defect_types = ["P0"] * len(p0_cols) + ["P1"] * len(p1_counts)
    defect_names = p0_cols + p1_annotator_cols
    defect_totals = list(p0_counts.values()) + list(p1_counts.values())
    defect_percent = [f"{count/total_records:.2%}" for count in defect_totals]

    defect_df = pd.DataFrame({
        "Defect Type": defect_types,
        "Defect Name": defect_names,
        "Count": defect_totals,
        "Percentage": defect_percent
    })

    st.subheader("Defect Breakdown")
    st.dataframe(defect_df, use_container_width=True)

    # ------------------------------
    # P0, P1, Grand totals
    # ------------------------------
    p0_total = sum(p0_counts.values())
    p1_total = sum(p1_counts.values())
    grand_total = p0_total + p1_total

    totals_df = pd.DataFrame({
        "Defect Type": ["P0 TOTAL", "P1 TOTAL", "GRAND TOTAL"],
        "Count": [p0_total, p1_total, grand_total]
    })
    st.subheader("Totals")
    st.dataframe(totals_df)

    # ------------------------------
    # Download as Excel
    # ------------------------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
        defect_df.to_excel(writer, index=False, sheet_name="Defect Breakdown")
        totals_df.to_excel(writer, index=False, sheet_name="Totals")
    output.seek(0)

    st.download_button(
        label="Download Full Report",
        data=output,
        file_name="defect_analysis_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
