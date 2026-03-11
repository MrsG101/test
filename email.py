import streamlit as st
import pandas as pd

st.title("📧 System Email Cleanup Tool")

active_file = st.file_uploader("1️⃣ Active Email List", type=["xlsx"])
protected_file = st.file_uploader("2️⃣ Protected Email List", type=["xlsx"])
system_file = st.file_uploader("3️⃣ System Users File", type=["xlsx"])


# ===== HELPER FUNCTIONS =====

def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip()
    return df

def find_email_col(df):
    for c in df.columns:
        if "mail" in c.lower():
            return c
    return None

def find_status_col(df):
    for c in df.columns:
        if "идэвх" in c.lower() or "inactive" in c.lower():
            return c
    return None

def find_login_col(df):
    for c in df.columns:
        if "login" in c.lower():
            return c
    return None


# ===== MAIN LOGIC =====

if active_file and protected_file and system_file:

    active = pd.read_excel(active_file, engine="openpyxl")
    protected = pd.read_excel(protected_file, engine="openpyxl")
    system = pd.read_excel(system_file, engine="openpyxl")

    # clean column names
    active = clean_columns(active)
    protected = clean_columns(protected)
    system = clean_columns(system)

    st.write("Active Columns 👉", list(active.columns))
    st.write("Protected Columns 👉", list(protected.columns))
    st.write("System Columns 👉", list(system.columns))

    # auto detect columns
    active_email_col = find_email_col(active)
    protected_email_col = find_email_col(protected)
    system_email_col = "Имэйл"
    status_col = find_status_col(system)
    login_col = find_login_col(system)

    if system_email_col is None:
        st.error("❌ System file дээр email column олдсонгүй")
        st.stop()

    # ===== EMAIL CLEAN =====
    active_emails = (
        active[active_email_col]
        .astype(str)
        .str.lower()
        .str.strip()
        .dropna()
        .unique()
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

    # ===== STATUS PRIORITY =====
    if status_col:
        system["inactive"] = (
            system[status_col]
            .astype(str)
            .str.lower()
            .str.strip()
        )

        system["priority"] = system["inactive"].map(
            {"no": 0, "yes": 1}
        ).fillna(1)
    else:
        system["inactive"] = "yes"
        system["priority"] = 1

    # ===== LOGIN PRIORITY =====
    if login_col:
        system[login_col] = pd.to_datetime(system[login_col], errors="coerce")
        system_sorted = system.sort_values(
            by=["email", "priority", login_col],
            ascending=[True, True, False]
        )
    else:
        system_sorted = system.sort_values(
            by=["email", "priority"],
            ascending=[True, True]
        )

    # ===== DUPLICATE RESOLVE =====
    system_unique = system_sorted.drop_duplicates("email", keep="first")

    # ===== DELETE LIST =====
    delete_list = system_unique[
        (system_unique["inactive"] == "yes") &
        ~system_unique["email"].isin(active_emails) &
        ~system_unique["email"].isin(protected_emails)
    ]

    # ===== SUMMARY =====
    st.success(f"✅ Unique emails: {len(system_unique)}")
    st.warning(f"🗑️ Delete candidates: {len(delete_list)}")

    st.subheader("Delete Candidate Preview")
    st.dataframe(delete_list)

    st.download_button(
        "⬇️ Download Delete List",
        delete_list.to_csv(index=False),
        "DELETE_EMAIL_LIST.csv",
        "text/csv"
    )
