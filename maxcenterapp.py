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
    # ────────────────────────────── MAXCENTER УНШИХ ──────────────────────────────
    max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)

    # Баганын нэрийг цэвэрлэх (зай, шинэ мөр арилгах)
    max_df.columns = [str(c).strip().replace('\n', '').replace('\r', '').replace('  ', ' ') for c in max_df.columns]

    # Шаардлагатай багануудыг шалгах
    expected_cols = ['First Name', 'Last Name', 'Office Name', 'Role', 'Constituent ID']
    found_cols = [c for c in expected_cols if c in max_df.columns]

    if len(found_cols) < 4:
        st.error("Maxcenter-д дараах багануудын зарим нь олдсонгүй:\n" + 
                 "\n".join(expected_cols) + 
                 "\n\nУншигдсан баганууд:\n" + "\n".join(max_df.columns.tolist()))
        st.stop()

    # Нэр үүсгэх (First + Last)
    max_df['full_name'] = (
        max_df['First Name'].astype(str).str.strip() + ' ' +
        max_df['Last Name'].astype(str).str.strip()
    ).str.strip()

    max_df['norm_name'] = max_df['full_name'].str.lower().str.strip()
    max_df['Office Name'] = max_df['Office Name'].fillna('').astype(str).str.strip()
    max_df['Role'] = max_df['Role'].fillna('').astype(str).str.strip()

    # ────────────────────────────── ICONNECT УНШИХ ──────────────────────────────
    icon_bytes = icon_file.read()
    try:
        icon_df = pd.read_excel(BytesIO(icon_bytes))
    except:
        icon_df = pd.read_html(BytesIO(icon_bytes))[0]

    # Шаардлагатай баганууд
    icon_cols = ['Агентын нэр', 'Оффисын нэр', 'Агент идэвхгүй болсон', 
                 'Одоогийн RE/MAX дэх албан тушаал', 'Гар утас', 'Имэйл']
    
    icon_df = icon_df[[c for c in icon_cols if c in icon_df.columns]].copy()

    icon_df['clean_name'] = icon_df['Агентын нэр'].astype(str).str.replace(r'\s*\(Transferred\)', '', regex=True).str.strip()
    icon_df['norm_name'] = icon_df['clean_name'].str.lower().str.strip()
    icon_df['is_active'] = icon_df['Агент идэвхгүй болсон'].astype(str).str.strip() == 'No'
    icon_df['Оффисын нэр'] = icon_df['Оффисын нэр'].astype(str).str.replace('REMAX', 'RE/MAX ', regex=False).str.strip()

    # ────────────────────────────── ТУЛГАХ (6 алхам дарааллаар) ──────────────────────────────
    def classify(row):
        name_norm = row['norm_name']
        office = row['Office Name']
        role = row['Role'].upper()

        # 1. Owner
        if 'OWNER' in role:
            return 'Зөв + Owner', None

        # Хайлт
        matches = icon_df[icon_df['norm_name'] == name_norm]
        active_matches = matches[matches['is_active']]

        # 4 & 5. Идэвхтэй байхгүй / огт олдохгүй
        if active_matches.empty:
            if not matches.empty:
                return 'Гарсан тул устгах', None
            else:
                return 'Шалгах олдоогүй', None

        # 2 & 3. Оффис таарсан / зөрсөн
        if office in active_matches['Оффисын нэр'].values:
            return 'Зөв + Owner', None
        else:
            suggested = active_matches.iloc[0]['Оффисын нэр']
            return 'Оффис засах', suggested

    max_df[['status', 'suggested_office']] = max_df.apply(classify, axis=1, result_type='expand')

    # Ангилал
    correct     = max_df[max_df['status'] == 'Зөв + Owner']
    to_update   = max_df[max_df['status'] == 'Оффис засах']
    to_delete   = max_df[max_df['status'] == 'Гарсан тул устгах']
    to_check    = max_df[max_df['status'] == 'Шалгах олдоогүй']

    # 6. Шинээр нээх (iConnect-д идэвхтэй Associate байгаа ч Max-д байхгүй)
    max_names = set(max_df['norm_name'])
    to_create = icon_df[
        (icon_df['is_active']) &
        (icon_df['Одоогийн RE/MAX дэх албан тушаал'].astype(str).str.contains('Associate', case=False, na=False)) &
        (~icon_df['norm_name'].isin(max_names))
    ]

    # Тоо харуулах
    st.success(f"""
    Зөв + Owner: **{len(correct)}**  
    Оффис засах: **{len(to_update)}**  
    Гарсан тул устгах: **{len(to_delete)}**  
    Шалгах олдоогүй: **{len(to_check)}**  
    Шинээр нээх: **{len(to_create)}**
    """)

    # Tab-ууд
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Зөв + Owner", "Оффис засах", "Гарсан тул устгах", 
        "Шалгах олдоогүй", "Шинээр нээх"
    ])

    with tab1:
        st.dataframe(correct[['Constituent ID', 'full_name', 'Office Name', 'Role', 'status']].reset_index(drop=True))
    with tab2:
        st.dataframe(to_update[['Constituent ID', 'full_name', 'Office Name', 'suggested_office', 'status']].reset_index(drop=True))
    with tab3:
        st.dataframe(to_delete[['Constituent ID', 'full_name', 'Office Name', 'status']].reset_index(drop=True))
    with tab4:
        st.dataframe(to_check[['Constituent ID', 'full_name', 'Office Name', 'status']].reset_index(drop=True))
    with tab5:
        show_cols = ['Агентын нэр', 'Оффисын нэр', 'Гар утас', 'Имэйл']
        avail_cols = [c for c in show_cols if c in to_create.columns]
        st.dataframe(to_create[avail_cols].reset_index(drop=True))

    # Excel татах
    def create_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            max_df.to_excel(writer, sheet_name='Бүх Maxcenter + Status', index=False)
            correct.to_excel(writer, sheet_name='Зөв + Owner', index=False)
            to_update.to_excel(writer, sheet_name='Оффис засах', index=False)
            to_delete.to_excel(writer, sheet_name='Гарсан тул устгах', index=False)
            to_check.to_excel(writer, sheet_name='Шалгах олдоогүй', index=False)
            to_create.to_excel(writer, sheet_name='Шинээр нээх', index=False)
        output.seek(0)
        return output.getvalue()

    st.download_button(
        label="📥 Бүх үр дүнг Excel-ээр татах",
        data=create_excel(),
        file_name="agent_tulgalt_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Хоёр файлыг оруулна уу.")
