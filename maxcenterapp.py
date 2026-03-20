<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Maxcenter vs iConnect Агент Тулгах Tool (Streamlit код)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }
        pre { background: #2d2d2d; color: #fff; padding: 20px; border-radius: 8px; overflow-x: auto; }
        h1 { color: #1e88e5; }
    </style>
</head>
<body>
<h1>✅ Maxcenter ба iConnect Агент Тулгах Tool</h1>
<p>Доорх кодыг <strong>maxcenterapp.py</strong> гэж хадгалаад <code>streamlit run maxcenterapp.py</code> гэж ажиллуулна уу.</p>
<p>Файлуудыг оруулахад:</p>
<ul>
    <li>Maxcenter (xlsx) – "Roster" sheet</li>
    <li>iConnect (xls эсвэл html table) – автоматаар уншина</li>
</ul>
<p>Логикийг яг таны зааснаар хийсэн:</p>
<ul>
    <li>iConnect-д "REMAX" → "RE/MAX " болгоно</li>
    <li>Нэр (First + Middle + Last) + Office тулгана (exact + lower case)</li>
    <li>Owner-уудыг хэзээ ч устгахгүй</li>
    <li>"Агент идэвхгүй болсон" = "No" → идэвхтэй</li>
    <li>(Transferred) нэрийг цэвэрлэнэ</li>
    <li>Үр дүнг 1 Excel файлд 5 sheet-ээр татна</li>
</ul>

<pre><code>
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
    max_file = st.file_uploader("Maxcenter файл (maxcenter (2).xlsx)", type=["xlsx"], key="max")
with col2:
    icon_file = st.file_uploader("iConnect файл (iconnect.xls)", type=["xls", "xlsx", "html"], key="icon")

if max_file and icon_file:
    # ---------- Maxcenter унших (header=2) ----------
    max_df = pd.read_excel(max_file, sheet_name="Roster", header=2)
    
    # Нэр цэвэрлэх
    def make_full_name(row):
        parts = [str(row["First Name"]).strip() if pd.notna(row["First Name"]) else "",
                 str(row["Middle Name"]).strip() if pd.notna(row["Middle Name"]) else "",
                 str(row["Last Name"]).strip() if pd.notna(row["Last Name"]) else ""]
        return " ".join([p for p in parts if p]).strip()
    
    max_df["full_name"] = max_df.apply(make_full_name, axis=1)
    max_df["norm_name"] = max_df["full_name"].str.lower().str.strip()
    max_df["Office Name"] = max_df["Office Name"].fillna("").astype(str).str.strip()
    
    # ---------- iConnect унших (HTML эсвэл Excel) ----------
    icon_bytes = icon_file.read()
    try:
        icon_df = pd.read_excel(BytesIO(icon_bytes))
    except:
        icon_df = pd.read_html(BytesIO(icon_bytes))[0]
    
    # Заавал байх баганууд
    icon_df["clean_name"] = icon_df["Агентын нэр"].astype(str).str.replace(r"\s*\(Transferred\)", "", regex=True).str.strip()
    icon_df["norm_name"] = icon_df["clean_name"].str.lower().str.strip()
    icon_df["is_active"] = icon_df["Агент идэвхгүй болсон"].astype(str).str.strip() == "No"
    icon_df["office_clean"] = icon_df["Оффисын нэр"].astype(str).str.replace("REMAX", "RE/MAX ", regex=False).str.strip()
    
    # ================== ТУЛГАХ ФУНКЦ ==================
    def get_status(row, icon_df):
        norm_name = row["norm_name"]
        office_max = row["Office Name"]
        role = str(row.get("Role", "")).strip().upper()
        
        if role == "OWNER":
            return "Owner - Хэвээр үлдээх", None
        
        matches = icon_df[icon_df["norm_name"] == norm_name]
        active_matches = matches[matches["is_active"]]
        
        if len(matches) == 0:
            return "Шалгах олдоогүй", None
        if len(active_matches) == 0:
            return "Гарсан тул устгах", None
        
        # Оффис таарсан эсэх
        matching_office = active_matches[active_matches["office_clean"].str.strip() == office_max]
        if len(matching_office) > 0:
            return "Зөв бүртгэлтэй", None
        else:
            suggested = active_matches.iloc[0]["office_clean"]
            return "Шилжсэн оффис засах", suggested
    
    # Apply
    status_results = max_df.apply(lambda row: get_status(row, icon_df), axis=1)
    max_df["status"] = [x[0] for x in status_results]
    max_df["suggested_office"] = [x[1] for x in status_results]
    
    # ================== ҮР ДҮНГЭЭР АНГИЛАХ ==================
    to_delete = max_df[max_df["status"] == "Гарсан тул устгах"].copy()
    to_check = max_df[max_df["status"] == "Шалгах олдоогүй"].copy()
    to_update = max_df[max_df["status"] == "Шилжсэн оффис засах"].copy()
    correct = max_df[max_df["status"] == "Зөв бүртгэлтэй"].copy()
    owners = max_df[max_df["status"].str.contains("Owner", na=False)].copy()
    
    # iConnect-д байгаа ч Maxcenter-д байхгүй (идэвхтэй)
    max_names = set(max_df["norm_name"])
    to_create = icon_df[(icon_df["is_active"]) & (~icon_df["norm_name"].isin(max_names))].copy()
    
    # ================== ХАРУУЛАХ ==================
    st.success(f"Тулгалт дууслаа! Maxcenter: {len(max_df)} агент | iConnect идэвхтэй: {len(icon_df[icon_df['is_active']])}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚫 Устгах", "🔍 Шалгах олдоогүй", "✏️ Оффис засах", "➕ Maxcenter үүсгэх", "✅ Зөв + Owner"])
    
    with tab1:
        st.subheader(f"Устгах ({len(to_delete)})")
        st.dataframe(to_delete[["Constituent ID", "full_name", "Office Name", "Role"]])
    
    with tab2:
        st.subheader(f"Шалгах олдоогүй ({len(to_check)})")
        st.dataframe(to_check[["Constituent ID", "full_name", "Office Name"]])
    
    with tab3:
        st.subheader(f"Шилжсэн оффис засах ({len(to_update)})")
        st.dataframe(to_update[["Constituent ID", "full_name", "Office Name", "suggested_office"]])
    
    with tab4:
        st.subheader(f"Maxcenter-д үүсгэх ({len(to_create)})")
        st.dataframe(to_create[["Агент ID", "Агентын нэр", "Оффисын нэр", "Гар утас", "Имэйл"]])
    
    with tab5:
        st.subheader(f"Зөв + Owner ({len(correct) + len(owners)})")
        st.dataframe(pd.concat([correct, owners])[["full_name", "Office Name", "Role", "status"]])
    
    # ================== DOWNLOAD ==================
    def create_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            max_df.to_excel(writer, sheet_name="БҮХ Maxcenter + Status", index=False)
            to_delete.to_excel(writer, sheet_name="Устгах", index=False)
            to_check.to_excel(writer, sheet_name="Шалгах олдоогүй", index=False)
            to_update.to_excel(writer, sheet_name="Оффис засах", index=False)
            to_create.to_excel(writer, sheet_name="Maxcenter үүсгэх", index=False)
            owners.to_excel(writer, sheet_name="Owners", index=False)
        output.seek(0)
        return output.getvalue()
    
    st.download_button(
        label="📥 БҮХ ҮР ДҮНГ Excel-ээр татах",
        data=create_excel(),
        file_name="agent_tulgalt_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Хоёр файлыг оруулна уу.")
</code></pre>

<p><strong>Яаж ашиглах вэ?</strong></p>
<ol>
    <li>Кодыг <code>app.py</code> гэж хадгал</li>
    <li><code>pip install streamlit pandas openpyxl</code></li>
    <li><code>streamlit run app.py</code></li>
    <li>Хоёр файлаа оруулаад татах</li>
</ol>

<p>Хэрвээ нэр таарахгүй байвал (алдаа ихтэй гэж та хэлсэн) – хүсвэл fuzzy matching (difflib) нэмж өгч болно. Одоогоор яг таны заасан логиктой.</p>
</body>
</html>
