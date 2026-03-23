import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Агент Тулгах Tool", layout="wide")
st.title("Maxcenter vs iConnect Агент Тулгах Tool")
st.markdown("**iConnect** нь үндсэн эх сурвалж. Maxcenter-ийг тулгаж засвар/устгах/нээх жагсаалт гаргана.")

# Файл оруулах
col1, col2 = st.columns(2)
with col1:
    max_file = st.file_uploader("Maxcenter файл (xlsx)", type=["xlsx"])
with col2:
    icon_file = st.file_uploader("iConnect файл (xls / xlsx / html)", type=["xls", "xlsx", "html"])

if max_file and icon_file:
    # ────────────────────────────── MAXCENTER ──────────────────────────────
    max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)

    max_df.columns = [str(c).strip().replace('\n', '').replace('\r', '').replace('  ', ' ') for c in max_df.columns]

    # Шаардлагатай багана байгаа эсэх шалгах
    required_max = ['First Name', 'Last Name', 'Office Name', 'Role']
    missing_max = [c for c in required_max if c not in max_df.columns]
    if missing_max:
        st.error(f"Maxcenter-д дараах баганууд олдсонгүй: {missing_max}\n\nУншигдсан баганууд:\n" + "\n".join(max_df.columns))
        st.stop()

    max_df['full_name'] = (
        max_df['First Name'].astype(str).str.strip() + ' ' +
        max_df['Last Name'].astype(str).str.strip()
    ).str.strip()

    max_df['norm_name'] = max_df['full_name'].str.lower().str.strip()
    max_df['Office Name'] = max_df['Office Name'].fillna('').astype(str).str.strip()
    max_df['Role'] = max_df['Role'].fillna('').astype(str).str.strip()

    # ────────────────────────────── ICONNECT ──────────────────────────────
    icon_bytes = icon_file.read()
    try:
        icon_df = pd.read_excel(BytesIO(icon_bytes))
    except:
        icon_df = pd.read_html(BytesIO(icon_bytes))[0]

    icon_df.columns = [str(c).strip().replace('\n', '').replace('\r', '').replace('  ', ' ') for c in icon_df.columns]

    # iConnect-ийн баганын нэрүүдийг шалгах & debug харуулах
    st.subheader("iConnect-д уншигдсан баганууд (цэвэрлэсний дараа)")
    st.code("\n".join(icon_df.columns.tolist()), language="text")

    required_icon = {
        'Агентын нэр': None,
        'Оффисын нэр': None,
        'Агент идэвхгүй болсон': None,
        'Одоогийн RE/MAX дэх албан тушаал': None
    }

    for key in required_icon:
        found = [c for c in icon_df.columns if key in c]
        if found:
            required_icon[key] = found[0]
        else:
            st.warning(f"iConnect-д '{key}' төстэй багана олдсонгүй")

    if not required_icon['Одоогийн REMAX дэх албан тушаал']:
        st.error("Алдаа: iConnect файлд 'Одоогийн RE/MAX дэх албан тушаал' багана байхгүй. Дээрх жагсаалтаас харна уу.")
        st.stop()

    # Стандарт нэр өгөх
    icon_df = icon_df.rename(columns={
        required_icon['Агентын нэр']: 'Агентын нэр',
        required_icon['Оффисын нэр']: 'Оффисын нэр',
        required_icon['Агент идэвхгүй болсон']: 'Агент идэвхгүй болсон',
        required_icon['Одоогийн REMAX дэх албан тушаал']: 'Position'
    })

    icon_df['clean_name'] = icon_df['Агентын нэр'].astype(str).str.replace(r'\s*\(Transferred\)', '', regex=True).str.strip()
    icon_df['norm_name'] = icon_df['clean_name'].str.lower().str.strip()
    icon_df['is_active'] = icon_df['Агент идэвхгүй болсон'].astype(str).str.strip() == 'No'
    icon_df['Оффисын нэр'] = icon_df['Оффисын нэр'].astype(str).str.replace('REMAX', 'RE/MAX ', regex=False).str.strip()

    # ────────────────────────────── ТУЛГАХ ──────────────────────────────
    def classify(row):
        name_norm = row['norm_name']
        office = row['Office Name']
        role = row['Role'].upper()

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

    max_df[['status', 'suggested_office']] = max_df.apply(classify, axis=1, result_type='expand')

    correct     = max_df[max_df['status'] == 'Зөв + Owner']
    to_update   = max_df[max_df['status'] == 'Оффис засах']
    to_delete   = max_df[max_df['status'] == 'Гарсан тул устгах']
    to_check    = max_df[max_df['status'] == 'Шалгах олдоогүй']

    max_names_set = set(max_df['norm_name'])
    to_create = icon_df[
        icon_df['is_active'] &
        icon_df['Position'].astype(str).str.contains('Associate', case=False, na=False) &
        ~icon_df['norm_name'].isin(max_names_set)
    ]

    # Тоо харуулах
    st.success(f"""
    Зөв + Owner: **{len(correct)}**  
    Оффис засах: **{len(to_update)}**  
    Гарсан тул устгах: **{len(to_delete)}**  
    Шалгах олдоогүй: **{len(to_check)}**  
    Шинээр нээх: **{len(to_create)}**
    """)

    tabs = st.tabs(["Зөв + Owner", "Оффис засах", "Гарсан тул устгах", "Шалгах", "Шинээр нээх"])

    with tabs[0]: st.dataframe(correct[['Constituent ID', 'full_name', 'Office Name', 'Role']].reset_index(drop=True))
    with tabs[1]: st.dataframe(to_update[['Constituent ID', 'full_name', 'Office Name', 'suggested_office']].reset_index(drop=True))
    with tabs[2]: st.dataframe(to_delete[['Constituent ID', 'full_name', 'Office Name']].reset_index(drop=True))
    with tabs[3]: st.dataframe(to_check[['Constituent ID', 'full_name', 'Office Name']].reset_index(drop=True))
    with tabs[4]: st.dataframe(to_create[['Агентын нэр', 'Оффисын нэр', 'Гар утас', 'Имэйл']].reset_index(drop=True))

    # Excel татах (өмнөхтэй адил)
    def to_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            max_df.to_excel(writer, 'Бүх Maxcenter + Status', index=False)
            correct.to_excel(writer, 'Зөв + Owner', index=False)
            to_update.to_excel(writer, 'Оффис засах', index=False)
            to_delete.to_excel(writer, 'Гарсан тул устгах', index=False)
            to_check.to_excel(writer, 'Шалгах олдоогүй', index=False)
            to_create.to_excel(writer, 'Шинээр нээх', index=False)
        output.seek(0)
        return output.getvalue()

    st.download_button("📥 Бүх үр дүнг татах", to_excel(), "agent_tulgalt_result.xlsx")

else:
    st.info("Хоёр файлыг оруулна уу.")
