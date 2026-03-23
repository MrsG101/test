import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Агент Тулгах Tool", layout="wide")
st.title("🔍 Maxcenter vs iConnect Агент Тулгах Tool")

col1, col2 = st.columns(2)
with col1:
    max_file = st.file_uploader("Maxcenter файл (xlsx)", type=["xlsx"])
with col2:
    icon_file = st.file_uploader("iConnect файл (xls/xlsx/html)", type=["xls", "xlsx", "html"])

if max_file and icon_file:
    # ────────────────────────────── MAXCENTER ──────────────────────────────
    try:
        max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)
    except:
        try:
            max_df = pd.read_excel(max_file, sheet_name="Roster", header=3)  # зарим файлд header=3 байж болно
        except Exception as e:
            st.error(f"Maxcenter файлыг унших боломжгүй: {e}")
            st.stop()

    # Баганын нэрийг цэвэрлэх (зай, \n арилгах)
    max_df.columns = [str(c).strip().replace('\n', '').replace('\r', '') for c in max_df.columns]

    # Debug: ямар баганууд уншигдсаныг харуулах
    st.subheader("Maxcenter-д уншигдсан баганууд (цэвэрлэсний дараа)")
    st.write(list(max_df.columns))

    # Автоматаар шаардлагатай багануудыг олох & rename
    col_rename = {}
    for col in max_df.columns:
        c_lower = col.lower()
        if 'first' in c_lower and 'name' in c_lower:
            col_rename[col] = 'First Name'
        elif 'last' in c_lower and 'name' in c_lower:
            col_rename[col] = 'Last Name'
        elif 'office' in c_lower and 'name' in c_lower:
            col_rename[col] = 'Office Name'
        elif 'role' in c_lower:
            col_rename[col] = 'Role'
        elif 'constituent' in c_lower and 'id' in c_lower:
            col_rename[col] = 'Constituent ID'

    max_df.rename(columns=col_rename, inplace=True)

    # Шаардлагатай баганууд байгаа эсэх шалгах
    required = ['First Name', 'Last Name', 'Office Name', 'Role']
    missing = [c for c in required if c not in max_df.columns]
    if missing:
        st.error(f"Дараах баганууд олдсонгүй: {missing}\n\nУншигдсан баганууд:\n" + "\n".join(max_df.columns))
        st.dataframe(max_df.head(3))
        st.stop()

    # Нэр үүсгэх (First + Last)
    max_df['full_name'] = (
        max_df['First Name'].astype(str).str.strip() + ' ' +
        max_df['Last Name'].astype(str).str.strip()
    ).str.strip()
    max_df['norm_name'] = max_df['full_name'].str.lower().str.strip()

    max_df['Office Name'] = max_df['Office Name'].fillna('').astype(str).str.strip()
    max_df['Role'] = max_df['Role'].fillna('').astype(str).str.upper().str.strip()

    # ────────────────────────────── ICONNECT ──────────────────────────────
    icon_bytes = icon_file.read()
    try:
        icon_df = pd.read_excel(BytesIO(icon_bytes))
    except:
        icon_df = pd.read_html(BytesIO(icon_bytes))[0]

    icon_df['clean_name'] = icon_df['Агентын нэр'].astype(str).str.replace(r'\s*\(Transferred\)', '', regex=True).str.strip()
    icon_df['norm_name'] = icon_df['clean_name'].str.lower().str.strip()
    icon_df['is_active'] = icon_df['Агент идэвхгүй болсон'].astype(str).str.strip() == 'No'
    icon_df['Оффисын нэр'] = icon_df['Оффисын нэр'].astype(str).str.replace('REMAX', 'RE/MAX ', regex=False).str.strip()

    # ────────────────────────────── ТУЛГАХ ──────────────────────────────
    def classify_agent(row):
        name_norm = row['norm_name']
        office = row['Office Name']
        role = row['Role']

        if 'OWNER' in role:
            return 'Зөв + Owner', None

        matches = icon_df[icon_df['norm_name'] == name_norm]
        active = matches[matches['is_active']]

        if active.empty:
            return ('Гарсан тул устгах' if not matches.empty else 'Шалгах олдоогүй'), None

        if office in active['Оффисын нэр'].values:
            return 'Зөв + Owner', None
        else:
            return 'Оффис засах', active.iloc[0]['Оффисын нэр']

    max_df[['status', 'suggested_office']] = max_df.apply(classify_agent, axis=1, result_type='expand')

    # Ангилал
    correct = max_df[max_df['status'] == 'Зөв + Owner']
    update_office = max_df[max_df['status'] == 'Оффис засах']
    to_remove = max_df[max_df['status'] == 'Гарсан тул устгах']
    to_check = max_df[max_df['status'] == 'Шалгах олдоогүй']

    # Шинээр нээх
    max_names_set = set(max_df['norm_name'])
    to_create = icon_df[
        icon_df['is_active'] &
        icon_df['Одоогийн RE/MAX дэх албан тушаал'].astype(str).str.contains('Associate', case=False) &
        ~icon_df['norm_name'].isin(max_names_set)
    ]

    # Харуулах
    st.success(f"Зөв + Owner: {len(correct)} | Оффис засах: {len(update_office)} | "
               f"Устгах: {len(to_remove)} | Шалгах: {len(to_check)} | Шинээр нээх: {len(to_create)}")

    tabs = st.tabs(["Зөв + Owner", "Оффис засах", "Устгах", "Шалгах", "Шинээр нээх"])

    with tabs[0]: st.dataframe(correct[['Constituent ID', 'full_name', 'Office Name', 'Role']])
    with tabs[1]: st.dataframe(update_office[['Constituent ID', 'full_name', 'Office Name', 'suggested_office']])
    with tabs[2]: st.dataframe(to_remove[['Constituent ID', 'full_name', 'Office Name']])
    with tabs[3]: st.dataframe(to_check[['Constituent ID', 'full_name', 'Office Name']])
    with tabs[4]: st.dataframe(to_create[['Агентын нэр', 'Оффисын нэр', 'Гар утас', 'Имэйл']])

    # Excel татах функц (өмнөхтэй адилхан)
    # ... (өмнөх кодын to_excel хэсгийг хуулж оруулаарай)

else:
    st.info("Хоёр файлыг оруулна уу.")
