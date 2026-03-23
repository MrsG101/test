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
    max_file = st.file_uploader("Maxcenter файл (xlsx)", type=["xlsx"])
with col2:
    icon_file = st.file_uploader("iConnect файл (xls / xlsx / html)", type=["xls", "xlsx", "html"])

if max_file and icon_file:
    # ================== MAXCENTER УНШИХ ==================
    max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)

    # Зөвхөн шаардлагатай багануудыг ашиглана
    max_df = max_df[['First Name', 'Last Name', 'Office Name', 'Role', 'Constituent ID']].copy()

    # Нэр зөвхөн First + Last
    def make_full_name(row):
        first = str(row.get('First Name', '')).strip()
        last  = str(row.get('Last Name', '')).strip()
        return f"{first} {last}".strip()

    max_df['full_name'] = max_df.apply(make_full_name, axis=1)
    max_df['norm_name'] = max_df['full_name'].str.lower().str.strip()
    max_df['Office Name'] = max_df['Office Name'].fillna('').astype(str).str.strip()
    max_df['Role'] = max_df['Role'].fillna('').astype(str).str.strip()

    # ================== ICONNECT УНШИХ ==================
    icon_bytes = icon_file.read()
    try:
        icon_df = pd.read_excel(BytesIO(icon_bytes))
    except:
        icon_df = pd.read_html(BytesIO(icon_bytes))[0]

    # Шаардлагатай баганууд
    icon_df = icon_df[['Агентын нэр', 'Оффисын нэр', 'Агент идэвхгүй болсон', 
                       'Одоогийн RE/MAX дэх албан тушаал', 'Гар утас', 'Имэйл']].copy()

    # Цэвэрлэгээ
    icon_df['clean_name'] = icon_df['Агентын нэр'].astype(str).str.replace(r'\s*\(Transferred\)', '', regex=True).str.strip()
    icon_df['norm_name'] = icon_df['clean_name'].str.lower().str.strip()
    icon_df['is_active'] = icon_df['Агент идэвхгүй болсон'].astype(str).str.strip() == 'No'
    icon_df['Оффисын нэр'] = icon_df['Оффисын нэр'].astype(str).str.replace('REMAX', 'RE/MAX ', regex=False).str.strip()

    # ================== ТУЛГАХ ЛОГИК (ЯГ 6 АЛХАМ) ==================
    def get_status(row):
        norm_name = row['norm_name']
        office_max = row['Office Name']
        role = row['Role'].upper()

        # 1. Owner
        if 'OWNER' in role:
            return 'Зөв + Owner', None

        # iConnect-д хайх
        matches = icon_df[icon_df['norm_name'] == norm_name]
        active_matches = matches[matches['is_active']]

        if len(active_matches) == 0:
            return ('Гарсан тул устгах' if len(matches) > 0 else 'Шалгах олдоогүй'), None

        # 2 & 3. Оффис таарсан эсэх
        if office_max in active_matches['Оффисын нэр'].values:
            return 'Зөв + Owner', None
        else:
            suggested = active_matches.iloc[0]['Оффисын нэр']
            return 'Оффис засах', suggested

    status_results = max_df.apply(get_status, axis=1)
    max_df['status'] = [x[0] for x in status_results]
    max_df['suggested_office'] = [x[1] for x in status_results]

    # ================== АНГИЛАХ ==================
    correct     = max_df[max_df['status'] == 'Зөв + Owner'].copy()
    to_update   = max_df[max_df['status'] == 'Оффис засах'].copy()
    to_delete   = max_df[max_df['status'] == 'Гарсан тул устгах'].copy()
    to_check    = max_df[max_df['status'] == 'Шалгах олдоогүй'].copy()

    # 6. iConnect-д идэвхтэй Associate байгаа ч Maxcenter-д байхгүй
    max_names = set(max_df['norm_name'])
    to_create = icon_df[
        (icon_df['is_active']) &
        (icon_df['Одоогийн RE/MAX дэх албан тушаал'].astype(str).str.contains('Associate', case=False, na=False)) &
        (~icon_df['norm_name'].isin(max_names))
    ].copy()

    #
