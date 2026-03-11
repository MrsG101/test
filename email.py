import streamlit as st
import pandas as pd

st.title("📧 Datacom - Active Email Cleanup Tool")

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

    # ===== CLEAN COLUMN NAMES =====
    active = clean_columns(active)
    protected = clean_columns(protected)
    system = clean_columns(system)

    # ===== COLUMN SETTINGS (STABLE) =====
    active_email_col = "email"
    protected_email_col = "email"
    system_email_col = "Имэйл"

    status_col = "Агент идэвхгүй болсон"
    login_col = "Last Login Date"

    # ===== CLEAN EMAIL =====
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

    # ===== PRIORITY =====
    system["priority"] = system["inactive"].map({"no": 0, "yes": 1}).fillna(1)

    # ===== LOGIN DATE =====
    system[login_col] = pd.to_datetime(system[login_col], errors="coerce")

    # ===== DUPLICATE RESOLVE =====
    system_sorted = system.sort_values(
        by=["email", "priority", login_col],
        ascending=[True, True, False]
    )

    system_unique = system_sorted.drop_duplicates("email", keep="first")

    # ===== SYSTEM ACTIVE EMAILS =====
    system_active_emails = system_unique[
        system_unique["inactive"] == "no"
    ]["email"].dropna().unique()

    # ===== DELETE LIST =====
    delete_list = active[
        ~active["email_clean"].isin(protected_emails)
        & ~active["email_clean"].isin(system_active_emails)
    ]

    # ===== SUMMARY =====
    st.success(f"✅ Active total: {len(active)}")
    st.warning(f"🗑️ Delete candidates: {len(delete_list)}")

    st.subheader("Delete Candidate Preview")
    st.dataframe(delete_list)

    st.download_button(
        "⬇️ Download Delete List",
        delete_list.to_csv(index=False),
        "DELETE_EMAIL_LIST.csv",
        "text/csv"
    )
