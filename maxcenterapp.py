# maxcenterapp.py

import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Агент Тулгах Tool", layout="wide")
st.title("🔍 Maxcenter vs iConnect Агент Тулгах Tool")
st.markdown("**iConnect** нь үнэн зөв, шинэчлэгдсэн систем. Maxcenter-ийг түүнтэй тулгаж засвар/устгах/үүсгэх жагсаалт гаргана.")

# ================== ФАЙЛ ОРУУЛАХ ==================
col1, col2 = st.columns(2)

with col1:
    max_file = st.file_uploader(
        "Maxcenter файл оруулна уу",
        type=["xlsx"],
        accept_multiple_files=False,
        key="maxcenter_uploader"
    )

with col2:
    icon_file = st.file_uploader(
        "iConnect файл оруулна уу (xls, xlsx, html)",
        type=["xls", "xlsx", "html"],
        accept_multiple_files=False,
        key="iconnect_uploader"
    )

if max_file is not None and icon_file is not None:
    # ---------- Maxcenter унших ----------
        try:
        max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)
    except Exception as e:
        st.error(f"Maxcenter файлыг уншихад алдаа гарлаа: {e}")
        st.stop()

    # ────────────── DEBUG ──────────────
    st.write("### Maxcenter-ийн баганууд (уншсаны дараа):")
    st.write(list(max_df.columns))
    st.dataframe(max_df.head(3))   # эхний 3 мөрийг харуулна
    # ───────────────────────────────────
    # Нэр цэвэрлэх – ЗӨВХӨН First Name + Last Name
    def make_full_name(row):
        parts = []
        first = row.get("First Name", "")
        last = row.get("Last Name", "")
        
        if pd.notna(first) and str(first).strip():
            parts.append(str(first).strip())
        if pd.notna(last) and str(last).strip():
            parts.append(str(last).strip())
        
        return " ".join(parts).strip()

    max_df["full_name"] = max_df.apply(make_full_name, axis=1)
    max_df["norm_name"] = max_df["full_name"].str.lower().str.strip()
    max_df["Office Name"] = max_df["Office Name"].fillna("").astype(str).str.strip()

    # ---------- iConnect унших ----------
    icon_bytes = icon_file.read()
    icon_bytes_io = BytesIO(icon_bytes)

    try:
        icon_df = pd.read_excel(icon_bytes_io)
    except:
        try:
            # html5lib parser ашиглаж lxml шаардлагагүй болгох
            icon_df = pd.read_html(icon_bytes_io, flavor='html5lib')[0]
        except Exception as e:
            st.error(f"iConnect файлыг уншихад алдаа гарлаа: {e}\n(lxml эсвэл html5lib суулгаарай: pip install lxml эсвэл pip install html5lib)")
            st.stop()

    # iConnect цэвэрлэгээ
    if "Агентын нэр" in icon_df.columns:
        icon_df["clean_name"] = icon_df["Агентын нэр"].astype(str)\
            .str.replace(r"\s*\(Transferred\)", "", regex=True)\
            .str.strip()
        icon_df["norm_name"] = icon_df["clean_name"].str.lower().str.strip()

    if "Агент идэвхгүй болсон" in icon_df.columns:
        icon_df["is_active"] = icon_df["Агент идэвхгүй болсон"].astype(str).str.strip() == "No"

    if "Оффисын нэр" in icon_df.columns:
        icon_df["office_clean"] = icon_df["Оффисын нэр"].astype(str)\
            .str.replace("REMAX", "RE/MAX ", regex=False)\
            .str.strip()

    # ================== ТУЛГАХ ЛОГИК ==================
    def get_status(row, icon_df):
        norm_name = row["norm_name"]
        office_max = row["Office Name"]
        role = str(row.get("Role", "")).strip().upper()

        if "OWNER" in role:
            return "Owner - Хэвээр үлдээх", None

        matches = icon_df[icon_df["norm_name"] == norm_name]
        active_matches = matches[matches["is_active"]] if "is_active" in matches.columns else pd.DataFrame()

        if len(matches) == 0:
            return "Шалгах олдоогүй", None

        if len(active_matches) == 0:
            return "Гарсан тул устгах", None

        if "office_clean" in active_matches.columns:
            matching_office = active_matches[active_matches["office_clean"] == office_max]
            if not matching_office.empty:
                return "Зөв бүртгэлтэй", None
            else:
                suggested = active_matches.iloc[0]["office_clean"]
                return "Шилжсэн оффис засах", suggested
        else:
            return "Зөв бүртгэлтэй (оффис мэдээлэл байхгүй)", None

    status_results = max_df.apply(lambda r: get_status(r, icon_df), axis=1)
    max_df["status"] = [x[0] for x in status_results]
    max_df["suggested_office"] = [x[1] for x in status_results]

    # Ангилах (өмнөхтэй адил)
    to_delete   = max_df[max_df["status"] == "Гарсан тул устгах"].copy()
    to_check    = max_df[max_df["status"] == "Шалгах олдоогүй"].copy()
    to_update   = max_df[max_df["status"] == "Шилжсэн оффис засах"].copy()
    correct     = max_df[max_df["status"] == "Зөв бүртгэлтэй"].copy()
    owners      = max_df[max_df["status"].str.contains("Owner", na=False)].copy()

    max_norm_set = set(max_df["norm_name"].dropna())
    to_create = icon_df[
        (icon_df.get("is_active", False)) &
        (~icon_df["norm_name"].isin(max_norm_set))
    ].copy()

    # ================== ХАРУУЛАХ ==================
    st.success(f"Тулгалт дууслаа! Maxcenter: {len(max_df)} | iConnect идэвхтэй: {len(icon_df[icon_df.get('is_active', False)])}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚫 Устгах",
        "🔍 Шалгах олдоогүй",
        "✏️ Оффис засах",
        "➕ Maxcenter үүсгэх",
        "✅ Зөв + Owner"
    ])

    with tab1:
        st.subheader(f"Устгах ({len(to_delete)})")
        if not to_delete.empty:
            st.dataframe(to_delete[["Constituent ID", "full_name", "Office Name", "Role", "status"]])

    with tab2:
        st.subheader(f"Шалгах олдоогүй ({len(to_check)})")
        if not to_check.empty:
            st.dataframe(to_check[["Constituent ID", "full_name", "Office Name", "status"]])

    with tab3:
        st.subheader(f"Шилжсэн оффис засах ({len(to_update)})")
        if not to_update.empty:
            st.dataframe(to_update[["Constituent ID", "full_name", "Office Name", "suggested_office", "status"]])

    with tab4:
        st.subheader(f"Maxcenter-д үүсгэх ({len(to_create)})")
        cols_to_show = ["Агент ID", "Агентын нэр", "Оффисын нэр", "Гар утас", "Имэйл"]
        available_cols = [c for c in cols_to_show if c in to_create.columns]
        if not to_create.empty and available_cols:
            st.dataframe(to_create[available_cols])

    with tab5:
        st.subheader(f"Зөв бүртгэлтэй + Owner ({len(correct) + len(owners)})")
        combined = pd.concat([correct, owners], ignore_index=True)
        if not combined.empty:
            st.dataframe(combined[["full_name", "Office Name", "Role", "status"]])

    # ================== Excel татах ==================
    def to_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            max_df.to_excel(writer, sheet_name="Бүх Maxcenter + Status", index=False)
            to_delete.to_excel(writer, sheet_name="Устгах", index=False)
            to_check.to_excel(writer, sheet_name="Шалгах олдоогүй", index=False)
            to_update.to_excel(writer, sheet_name="Оффис засах", index=False)
            to_create.to_excel(writer, sheet_name="Maxcenter үүсгэх", index=False)
            owners.to_excel(writer, sheet_name="Owners", index=False)
        output.seek(0)
        return output.getvalue()

    st.download_button(
        label="📥 Бүх үр дүнг Excel-ээр татах",
        data=to_excel(),
        file_name="agent_tulgalt_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Maxcenter болон iConnect хоёр файлыг оруулна уу.")
