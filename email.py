import streamlit as st
import pandas as pd

st.title("📧 System Email Cleanup Tool")

active = pd.read_excel(active_file, engine="openpyxl")
protected = pd.read_excel(protected_file, engine="openpyxl")
system = pd.read_excel(system_file, engine="openpyxl")

if active_file and protected_file and system_file:

    active = pd.read_excel(active_file)
    protected = pd.read_excel(protected_file)
    system = pd.read_excel(system_file)

    # ===== COLUMN SETTINGS =====
    EMAIL_COL = "Имэйл"
    STATUS_COL = "Агент идэвхгүй болсон"
    LOGIN_COL = "Last Login Date"

    # ===== CLEAN EMAIL =====
    active_emails = active[EMAIL_COL].str.lower().str.strip().dropna().unique()
    protected_emails = protected[EMAIL_COL].str.lower().str.strip().dropna().unique()

    system["email"] = system[EMAIL_COL].str.lower().str.strip()
    system["inactive"] = system[STATUS_COL].str.lower().str.strip()

    # ===== PRIORITY =====
    # No = active = 0
    # Yes = inactive = 1
    system["priority"] = system["inactive"].map({"no":0, "yes":1})

    # login date
    system[LOGIN_COL] = pd.to_datetime(system[LOGIN_COL], errors="coerce")

    # ===== SMART DUPLICATE RESOLVE =====
    system_sorted = system.sort_values(
        by=["email", "priority", LOGIN_COL],
        ascending=[True, True, False]
    )

    system_unique = system_sorted.drop_duplicates("email", keep="first")

    # ===== DELETE CANDIDATE =====
    delete_list = system_unique[
        (system_unique["inactive"] == "yes") &
        ~system_unique["email"].isin(active_emails) &
        ~system_unique["email"].isin(protected_emails)
    ]

    # ===== SUMMARY =====
    total_system = len(system_unique)
    delete_count = len(delete_list)
    keep_count = total_system - delete_count

    st.success(f"✅ Total unique emails: {total_system}")
    st.warning(f"🗑️ Delete candidates: {delete_count}")
    st.info(f"✅ Keep emails: {keep_count}")

    st.subheader("Delete Candidate Preview")
    st.dataframe(delete_list)

    st.download_button(
        "⬇️ Download Delete List",
        delete_list.to_csv(index=False),
        "DELETE_EMAIL_LIST.csv",
        "text/csv"
    )
