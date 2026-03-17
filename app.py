df = pd.read_excel(uploaded_file)



total_records = len(df)



# P0 columns

p0_cols = [

    "audit_grammar_mistakes_serious",

    "audit_inappropriate_language",

    "audit_innacurate_serious",

    "audit_nonsensical_language",

    "audit_not_concise_serious"

]



# P1 columns

p1_cols = [

    "audit_grammar_mistakes_soft",

    "audit_innacurate_soft",

    "audit_not_concise_soft"

]



p0_counts = df[p0_cols].eq(True).sum()

p1_counts = df[p1_cols].eq(True).sum()



p0_total = p0_counts.sum()



p0_free = (df[p0_cols].eq(True).sum(axis=1) == 0).sum()



p1_any = df[p1_cols].eq(True).sum(axis=1) > 0



totally_defect_free = ((df[p0_cols].eq(True).sum(axis=1) == 0) &

                       (df[p1_cols].eq(True).sum(axis=1) == 0)).sum()



st.subheader("Summary Metrics")



st.metric("Total Records", total_records)

st.metric("Totally Defect Free", f"{totally_defect_free} ({totally_defect_free/total_records:.2%})")

st.metric("P0 Free", f"{p0_free} ({p0_free/total_records:.2%})")



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



st.dataframe(breakdown)
