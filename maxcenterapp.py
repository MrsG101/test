import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Агент Тулгах Tool", layout="wide")
st.title("Maxcenter болон iсonnect хэрэглэгчийн мэдээллийг тулгах tool")
st.markdown("iconnect болон maxcenter-ийн хэрэглэгчийн тайланд суурилан зөрүүтэй хэрэглэгчдийг гаргана.")

# Файл оруулах
col1, col2 = st.columns(2)
with col1:
    max_file = st.file_uploader("Maxcenter файл оруулах (xlsx)", type=["xlsx"])
with col2:
    icon_file = st.file_uploader("iconnect файл оруулах (xls / xlsx)", type=["xls", "xlsx"])

if max_file and icon_file:
    # ────────────────────────────── MAXCENTER ──────────────────────────────
    max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)

    # Баганын нэрийг цэвэрлэх
    max_df.columns = [str(c).strip().replace('\n', '').replace('\r', '').replace('  ', ' ') for c in max_df.columns]

    # Шаардлагатай баганууд шалгах
    required = ['First Name', 'Last Name', 'Office Name', 'Role', 'Constituent ID']
    missing = [c for c in required if c not in max_df.columns]
    if missing:
        st.error(f"Maxcenter-д дараах баганууд олдсонгүй: {missing}\n\nУншигдсан баганууд:\n" + "\n".join(max_df.columns))
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

    # Шаардлагатай баганууд шалгах
    icon_required = ['Агентын нэр', 'Оффисын нэр', 'Агент идэвхгүй болсон', 'Одоогийн REMAX дэх албан тушаал']
    icon_missing = [c for c in icon_required if c not in icon_df.columns]
    if icon_missing:
        st.error(f"iConnect-д дараах баганууд олдсонгүй: {icon_missing}\n\nУншигдсан баганууд:\n" + "\n".join(icon_df.columns))
        st.stop()

    icon_df['clean_name'] = icon_df['Агентын нэр'].astype(str).str.replace(r'\s*\(Transferred\)', '', regex=True).str.strip()
    icon_df['norm_name'] = icon_df['clean_name'].str.lower().str.strip()
    icon_df['is_active'] = icon_df['Агент идэвхгүй болсон'].astype(str).str.strip() == 'No'
    icon_df['Оффисын нэр'] = icon_df['Оффисын нэр'].astype(str).str.replace('REMAX', 'RE/MAX', regex=False).str.strip()

    # ────────────────────────────── ТУЛГАХ ──────────────────────────────
    def classify(row):
        name_norm = row['norm_name']
        office_max = row['Office Name']
        role = row['Role'].upper()

        if 'OWNER' in role:
            return 'Зөв + Owner', None

        matches = icon_df[icon_df['norm_name'] == name_norm]
        active_matches = matches[matches['is_active']]

        if active_matches.empty:
            if not matches.empty:
                return 'Гарсан тул устгах', None
            else:
                return 'Шалгах олдоогүй', None

        active_offices = active_matches['Оффисын нэр'].str.strip()

        if office_max in active_offices.values:
            return 'Зөв + Owner', None
        else:
            suggested = active_matches.iloc[0]['Оффисын нэр'].strip()
            return 'Оффис засах', suggested

    max_df[['status', 'suggested_office']] = max_df.apply(classify, axis=1, result_type='expand')

    # Ангилал
    correct     = max_df[max_df['status'] == 'Зөв + Owner']
    to_update   = max_df[max_df['status'] == 'Оффис засах']
    to_delete   = max_df[max_df['status'] == 'Гарсан тул устгах']
    to_check    = max_df[max_df['status'] == 'Шалгах олдоогүй']

    max_names_set = set(max_df['norm_name'])
    to_create = icon_df[
        (icon_df['is_active']) &
        (icon_df['Одоогийн REMAX дэх албан тушаал'].astype(str).str.contains('Associate', case=False, na=False)) &
        (~icon_df['norm_name'].isin(max_names_set))
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

    with tabs[0]:
        st.dataframe(correct[['Constituent ID', 'full_name', 'Office Name', 'Role', 'status']].reset_index(drop=True))
    with tabs[1]:
        st.dataframe(to_update[['Constituent ID', 'full_name', 'Office Name', 'suggested_office', 'status']].reset_index(drop=True))
    with tabs[2]:
        st.dataframe(to_delete[['Constituent ID', 'full_name', 'Office Name', 'status']].reset_index(drop=True))
    with tabs[3]:
        st.dataframe(to_check[['Constituent ID', 'full_name', 'Office Name', 'status']].reset_index(drop=True))
    with tabs[4]:
        st.dataframe(to_create[['Агентын нэр', 'Оффисын нэр', 'Гар утас', 'Имэйл']].reset_index(drop=True))

    # Excel татах
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

    st.download_button(
        label="📥 Бүх үр дүнг excel-ээр татах",
        data=to_excel(),
        file_name="agent_tulgalt_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("хоёр файлаа оруулна уу.")
