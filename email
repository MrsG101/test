import streamlit as st
import pandas as pd

st.title("📧 Email Delete List Generator")

active_file = st.file_uploader("1️⃣ Active Email List", type=["xlsx"])
protected_file = st.file_uploader("2️⃣ Protected Email List", type=["xlsx"])
system_file = st.file_uploader("3️⃣ System Users File", type=["xlsx"])

if active_file and protected_file and system_file:

    active = pd.read_excel(active_file)
    protected = pd.read_excel(protected_file)
    system = pd.read_excel(system_file)

    # email column name тохируул
    active_emails = active["email"].str.lower().dropna().unique()
    protected_emails = protected["email"].str.lower().dropna().unique()

    system["email"] = system["email"].str.lower()

    # delete candidate
    delete_list = system[
        ~system["email"].isin(active_emails)
        & ~system["email"].isin(protected_emails)
    ]

    delete_list = delete_list.drop_duplicates("email")

    st.success(f"✅ Delete email count: {len(delete_list)}")

    st.dataframe(delete_list)

    st.download_button(
        "⬇️ Download Delete List",
        delete_list.to_csv(index=False),
        "delete_list.csv",
        "text/csv"
    )
