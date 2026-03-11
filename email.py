import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📧 Active Email Cleanup Tool")

active_file = st.file_uploader("1️⃣ Active Email List", type=["xlsx"])
protected_file = st.file_uploader("2️⃣ Protected Email List", type=["xlsx"])
system_file = st.file_uploader("3️⃣ System Users File", type=["xlsx"])


def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip()
    return df


if active_file and protected_file and system_file:

    active = pd.read_excel(active_file, engine="openpyxl")
    protected = pd.read_excel(protected_file, engine="openpyxl")
    system = pd.read_excel(system_file, engine="openpyxl")

    active = clean_columns(active)
    protected = clean_columns(protected)
    system = clean_columns(system)

    # ===== COLUMN SETTINGS =====
    active_email_col = "email"
    protected_email_col = "email"
    system_email_col = "Имэйл"

    status_col = "Агент идэвхгүй болсон"
    login_col = "Last Login Date"

    # ===== EMAIL CLEAN =====
    active["email_clean"] = (
        active[active_email_col]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    protected_emails = (
        protected[protected_email_col]
        .astype(str)
        .str.lower()
        .str.strip()
        .dropna()
        .unique()
    )

    system["email"] = (
        system[system_email_col]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    system["inactive"] = (
        system[status_col]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    system["priority"] = system["inactive"].map({"no": 0, "yes": 1}).fillna(1)

    system[login_col] = pd.to_datetime(system[login_col], errors="coerce")

    system_sorted = system.sort_values(
        by=["email", "priority", login_col],
        ascending=[True, True, False]
    )

    system_unique = system_sorted.drop_duplicates("email", keep="first")

    system_active_emails = system_unique[
        system_unique["inactive"] == "no"
    ]["email"].dropna().unique()

    system_all_emails = system_unique["email"].dropna().unique()

    # ===== CANDIDATE =====
    candidate = active[
        ~active["email_clean"].isin(protected_emails)
        & ~active["email_clean"].isin(system_active_emails)
    ].copy()

    # ===== SPLIT =====
    investigation_list = candidate[
        ~candidate["email_clean"].isin(system_all_emails)
    ].copy()

    delete_list = candidate[
        candidate["email_clean"].isin(system_all_emails)
    ].copy()

    # ===== SUMMARY =====
    st.success(f"✅ Active total: {len(active)}")
    st.warning(f"🗑️ To Delete: {len(delete_list)}")
    st.info(f"🔎 Need Investigation: {len(investigation_list)}")

    st.subheader("Delete Preview")
    st.dataframe(delete_list)

    st.subheader("Investigation Preview")
    st.dataframe(investigation_list)

    # ===== EXCEL EXPORT =====
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        delete_list.to_excel(writer, sheet_name="To_Delete", index=False)
        investigation_list.to_excel(writer, sheet_name="Need_Investigation", index=False)

    st.download_button(
        "⬇️ Download Result Excel",
        output.getvalue(),
        "EMAIL_CLEANUP_RESULT.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
