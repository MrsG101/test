# maxcenterapp.py
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Агент Тулгах Tool", layout="wide")
st.title("🔍 Maxcenter vs iConnect Агент Тулгах Tool")
st.markdown("**iConnect** нь үнэн зөв, шинэчлэгдсэн систем. Maxcenter-ийг яг таны заасан дарааллаар тулгана.")

# ================== ФАЙЛ ОРУУЛАХ ==================
col1, col2 = st.columns(2)
with col1:
    max_file = st.file_uploader("Maxcenter файл (xlsx)", type=["xlsx"], key="max")
with col2:
    icon_file = st.file_uploader("iConnect файл (xls / xlsx / html)", type=["xls","xlsx","html"], key="icon")

if max_file and icon_file:
    # ================== MAXCENTER УНШИХ ==================
    max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)

    # Багануудыг цэвэрлэх
    max_df.columns = max_df.columns.str.strip().str.replace(r'\n', '', regex=True).str.replace(r'\s+', ' ', regex=True)

    # Стандарт нэр өгөх
    col_map = {}
    for c in max_df.columns:
        lower = c.lower()
        if 'office' in lower and 'name' in lower: col_map[c] = 'office_name'
        elif 'first' in lower and 'name' in lower: col_map[c] = 'first_name'
        elif 'last' in lower and 'name' in lower: col_map[c] = 'last_name'
        elif 'role' in lower: col_map[c] = 'role'
        elif 'constituent' in lower and 'id' in lower: col_map[c] = 'constituent_id'

    max_df = max_df.rename(columns=col_map)

    # Нэр зөвхөн First + Last
    def make_full_name(row):
        first = str(row.get("first_name", "")).strip()
        last = str(row.get("last_name", "")).strip()
        return f"{first} {last}".strip()

    max_df["full_name"] = max_df.apply(make_full_name, axis=1)
    max_df["norm_name"] = max_df["full_name"].str.lower().str.strip()
    max_df["office_name"] = max_df["office_name"].fillna("").astype(str).str.strip()
    max_df["role"] = max_df["role"].fillna("").astype(str).str.strip()

    # ================== ICONNECT УНШИХ ==================
    icon_bytes = icon_file.read()
    try:
        icon_df = pd.read_excel(BytesIO(icon_bytes))
    except:
        icon_df = pd.read_html(BytesIO(icon_bytes))[0]

    # iConnect цэвэрлэгээ
    icon_df["clean_name"] = icon_df["Агентын нэр"].astype(str).str.replace(r"\s*\(Transferred\)", "", regex=True).str.strip()
    icon_df["norm_name"] = icon_df["clean_name"].str.lower().str.strip()
    icon_df["is_active"] = icon_df["Агент идэвхгүй болсон"].astype(str).str.strip() == "No"
    icon_df["office_clean"] = icon_df["Оффисын нэр"].astype(str).str.replace("REMAX", "RE/MAX ", regex=False).str.strip()

    # ================== ТУЛГАХ (ЯГ ТАНИЙ ЗААСАН ДАРААЛЛААР) ==================
    def get_status(row):
        norm_name = row["norm_name"]
        office_max = row["office_name"]
        role = row["role"].upper()

        # 1. Owner
        if "OWNER" in role:
            return "Зөв + Owner", None

        # iConnect-д хайх
        matches = icon_df[icon_df["norm_name"] == norm_name]
        active_matches = matches[matches["is_active"]]

        if len(active_matches) == 0:
            return ("Гарсан тул устгах" if len(matches) > 0 else "Шалгах олдоогүй"), None

        # 3. Оффис зөрсөн эсэх
        if office_max in active_matches["office_clean"].values:
            return "Зөв + Owner", None
        else:
            suggested = active_matches.iloc[0]["office_clean"]
            return "Оффис засах", suggested

    status_results = max_df.apply(lambda r: get_status(r), axis=1)
    max_df["status"] = [x[0] for x in status_results]
    max_df["suggested_office"] = [x[1] for x in status_results]

    # ================== АНГИЛАЛ ==================
    correct = max_df[max_df["status"] == "Зөв + Owner"].copy()
    to_update = max_df[max_df["status"] == "Оффис засах"].copy()
    to_delete = max_df[max_df["status"] == "Гарсан тул устгах"].copy()
    to_check = max_df[max_df["status"] == "Шалгах олдоогүй"].copy()

    # 6. Iconnect-д байгаа ч Maxcenter-д байхгүй (Шинээр нээх)
    max_names = set(max_df["norm_name"])
    to_create = icon_df[
        (icon_df["is_active"]) &
        (icon_df["Одоогийн REMAX дэх албан тушаал"].astype(str).str.contains("Associate", na=False)) &
        (~icon_df["norm_name"].isin(max_names))
    ].copy()

    # ================== ХАРУУЛАХ ==================
    st.success(f"""
    **Тулгалт дууслаа!**  
    Зөв + Owner: **{len(correct)}**  
    Оффис засах: **{len(to_update)}**  
    Гарсан тул устгах: **{len(to_delete)}**  
    Шалгах олдоогүй: **{len(to_check)}**  
    Шинээр нээх: **{len(to_create)}**
    """)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Зөв + Owner", "✏️ Оффис засах", "🗑️ Гарсан тул устгах",
        "🔍 Шалгах олдоогүй", "➕ Шинээр нээх"
    ])

    with tab1: st.dataframe(correct[["full_name", "office_name", "role", "status"]])
    with tab2: st.dataframe(to_update[["full_name", "office_name", "suggested_office", "status"]])
    with tab3: st.dataframe(to_delete[["full_name", "office_name", "status"]])
    with tab4: st.dataframe(to_check[["full_name", "office_name", "status"]])
    with tab5: 
        cols = ["Агентын нэр", "Оффисын нэр", "Гар утас", "Имэйл"]
        st.dataframe(to_create[[c for c in cols if c in to_create.columns]])

    # ================== EXCEL ТАТАХ ==================
    def to_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            max_df.to_excel(writer, sheet_name="Бүх Maxcenter + Status", index=False)
            correct.to_excel(writer, sheet_name="Зөв + Owner", index=False)
            to_update.to_excel(writer, sheet_name="Оффис засах", index=False)
            to_delete.to_excel(writer, sheet_name="Гарсан тул устгах", index=False)
            to_check.to_excel(writer, sheet_name="Шалгах олдоогүй", index=False)
            to_create.to_excel(writer, sheet_name="Шинээр нээх", index=False)
        output.seek(0)
        return output.getvalue()

    st.download_button("📥 Бүх үр дүнг Excel-ээр татах", 
                       data=to_excel(), 
                       file_name="agent_tulgalt_result.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("Хоёр файлыг оруулна уу.")
