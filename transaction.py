import streamlit as st
import pandas as pd
import re
from io import BytesIO
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Гүйлгээний алдаа шалгах", layout="wide", page_icon="🔍")
st.title("🔍 Гүйлгээний алдаа шалгах")
st.caption("TRR XML Report файл upload хийж алдаатай гүйлгээг шалгана")

# ── helpers ───────────────────────────────────────────────────────────────────
def parse_num(v):
    v = str(v).replace(" ₮", "").replace("₮", "").replace(",", "").strip()
    try:
        return float(v)
    except:
        return 0.0

def mls_base(v):
    m = re.match(r"^(\d+)", str(v))
    return m.group(1) if m else str(v)

def load_file(file_bytes):
    try:
        soup = BeautifulSoup(file_bytes.decode("utf-8-sig"), "html.parser")
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
            data = []
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if cells:
                    data.append(cells)
            if data:
                return pd.DataFrame(data, columns=headers)
    except Exception:
        pass
    buf = BytesIO(file_bytes)
    try:
        return pd.read_excel(buf, dtype=str)
    except Exception:
        buf.seek(0)
        return pd.read_excel(buf, engine="openpyxl", dtype=str)

def check_errors(df):
    # 1. ₮ replace
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(" ₮", "", regex=False).str.replace("₮", "", regex=False)

    # 2. Шимтгэлийн хувь
    df["_comm"] = df["Total Commission"].apply(parse_num)
    df["_sold"]  = df["Зарагдсан үнэ"].apply(parse_num)
    df["Шимтгэлийн хувь"] = df.apply(
        lambda r: round(r["_comm"] / r["_sold"] * 100, 2) if r["_sold"] > 0 else 0.0,
        axis=1,
    )

    # ── Алдаа 1: TRR ID давхардал ────────────────────────────────────────────
    df["Алдаа_TRR"] = df.duplicated("TRR ID", keep=False).map({True: "Давхардсан", False: ""})

    # ── Алдаа 2: Агент өөр дээрээ хаасан ─────────────────────────────────────
    # Нэг Бүртгэлийн дугаар (зураастай бүтнээр) дээр ижил AgentID 2+ удаа орвол алдаа
    agent_cnt = df.groupby(["Бүртгэлийн дугаар", "AgentID"]).size().reset_index(name="_n")
    self_close_pairs = set(
        zip(
            agent_cnt[agent_cnt["_n"] >= 2]["Бүртгэлийн дугаар"],
            agent_cnt[agent_cnt["_n"] >= 2]["AgentID"],
        )
    )
    df["Алдаа_Агент"] = df.apply(
        lambda r: "Агент өөр дээрээ хаасан"
        if (r["Бүртгэлийн дугаар"], r["AgentID"]) in self_close_pairs
        else "",
        axis=1,
    )

    # ── Алдаа 3: Шимтгэл зөрсөн ─────────────────────────────────────────────
    VALID = {
        ("Түрээс",   "Listing and Selling TRR"): {20.0, 50.0, 90.0},
        ("Түрээс",   "Listing TRR"):             {10.0, 25.0, 45.0},
        ("Худалдах", "Listing and Selling TRR"): {3.0,  5.0},
        ("Худалдах", "Listing TRR"):             {1.5,  2.5},
    }

    def shimtgel_err(row):
        key = (row["Шилжүүлэгийн төрөл"], row["TRR Type"])
        if key not in VALID:
            return ""
        pct = round(float(row["Шимтгэлийн хувь"]), 1)
        return "Шимтгэл зөрсөн" if pct not in VALID[key] else ""

    df["Алдаа_Шимтгэл"] = df.apply(shimtgel_err, axis=1)

    # ── Нийт алдаа ───────────────────────────────────────────────────────────
    df["Алдаа"] = df.apply(
        lambda r: " | ".join(
            p for p in [r["Алдаа_TRR"], r["Алдаа_Агент"], r["Алдаа_Шимтгэл"]] if p
        ),
        axis=1,
    )

    df.drop(columns=["_comm", "_sold"], inplace=True)
    return df


def to_excel(df_err):
    wb = Workbook()
    thin = Side(style="thin", color="D0D0D0")
    bdr  = Border(left=thin, right=thin, top=thin, bottom=thin)

    def make_sheet(df, title, tab_color, first=False):
        ws = wb.active if first else wb.create_sheet(title)
        ws.title = title
        ws.tab_color = tab_color
        ws.freeze_panes = "A2"
        ws.sheet_view.showGridLines = False

        hdr_fill = PatternFill("solid", fgColor="1E3A5F")
        err_fill = PatternFill("solid", fgColor="7B1010")

        for ci, col in enumerate(df.columns, 1):
            c = ws.cell(row=1, column=ci, value=col)
            c.font      = Font(name="Arial", bold=True, size=10, color="FFFFFF")
            c.fill      = err_fill if col == "Алдаа" else hdr_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border    = bdr
        ws.row_dimensions[1].height = 22
        ws.auto_filter.ref = ws.dimensions

        err_row_fill = PatternFill("solid", fgColor="FFF0F0")
        even_fill    = PatternFill("solid", fgColor="F5F8FF")
        odd_fill     = PatternFill("solid", fgColor="FFFFFF")
        red_font     = Font(name="Arial", size=9, color="CC0000", bold=True)
        norm_font    = Font(name="Arial", size=9)

        for ri, (_, row) in enumerate(df.iterrows(), 2):
            has_err = bool(row.get("Алдаа", ""))
            bg = err_row_fill if has_err else (even_fill if ri % 2 == 0 else odd_fill)
            for ci, val in enumerate(row, 1):
                col_name = df.columns[ci - 1]
                c = ws.cell(row=ri, column=ci, value=val)
                c.font      = red_font if (col_name == "Алдаа" and has_err) else norm_font
                c.fill      = bg
                c.alignment = Alignment(vertical="center")
                c.border    = bdr
                if col_name == "Шимтгэлийн хувь":
                    try:
                        c.value         = float(val) / 100
                        c.number_format = "0.00%"
                    except Exception:
                        pass
            ws.row_dimensions[ri].height = 15

        col_w = {
            "TRR ID": 12, "TRR Type": 24, "Үл хөдлөх хөрөнгийн хаяг": 32,
            "Шилжүүлэгийн төрөл": 16, "Orig. List Date": 14,
            "Анхны жагсаалтын үнэ": 18, "Зарагдсан өдөр": 14,
            "Зарагдсан үнэ": 16, "Payment Amount": 16, "Payment Date": 14,
            "Payments Received": 16, "Оффисын нэр": 22, "AgentID": 14,
            "Агент": 26, "Бүртгэлийн дугаар": 20, "Дүүрэг": 12,
            "Total Commission": 16, "# of Agents": 10, "Total Received": 16,
            "Total Outstanding": 16, "Last Submission Date": 18, "Buyers": 24,
            "Банк": 20, "Currency": 10, "Market Segment": 14, "First Payment": 12,
            "Шимтгэлийн хувь": 14, "Алдаа_TRR": 16,
            "Алдаа_Агент": 26, "Алдаа_Шимтгэл": 18, "Алдаа": 32,
        }
        for ci, col in enumerate(df.columns, 1):
            ws.column_dimensions[get_column_letter(ci)].width = col_w.get(col, 14)

    make_sheet(df_err, "Алдаатай гүйлгээ", "CC0000", first=True)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ── UI ────────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "📂 XLS / XLSX файл сонгоно уу",
    type=["xls", "xlsx"],
    help="TRR XML Report файл",
)

if uploaded:
    file_bytes = uploaded.read()

    with st.spinner("Файл уншиж байна..."):
        try:
            df_raw = load_file(file_bytes)
        except Exception as e:
            st.error(f"Файл уншихад алдаа гарлаа: {e}")
            st.stop()

    st.success(f"✅ {len(df_raw):,} мөр уншлаа — {len(df_raw.columns)} багана")

    with st.spinner("Алдаа шалгаж байна..."):
        df = check_errors(df_raw.copy())

    df_err = df[df["Алдаа"] != ""].reset_index(drop=True)

    n_total  = len(df)
    n_err    = len(df_err)
    n_dup    = (df["Алдаа_TRR"]     != "").sum()
    n_agent  = (df["Алдаа_Агент"]   != "").sum()
    n_shimtg = (df["Алдаа_Шимтгэл"] != "").sum()

    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Нийт гүйлгээ",        f"{n_total:,}")
    c2.metric("🔴 Нийт алдаа",        f"{n_err:,}",
              delta=f"{n_err / n_total * 100:.1f}%", delta_color="inverse")
    c3.metric("🔁 Давхардсан TRR",    f"{n_dup:,}")
    c4.metric("👤 Агент өөрт хаасан", f"{n_agent:,}")
    c5.metric("💰 Шимтгэл зөрсөн",   f"{n_shimtg:,}")
    st.markdown("---")

    show_cols = [
        "TRR ID", "TRR Type", "Шилжүүлэгийн төрөл",
        "Үл хөдлөх хөрөнгийн хаяг", "Зарагдсан үнэ",
        "Total Commission", "Шимтгэлийн хувь",
        "AgentID", "Агент", "Бүртгэлийн дугаар",
        "Алдаа_TRR", "Алдаа_Агент", "Алдаа_Шимтгэл", "Алдаа",
    ]
    show_cols = [c for c in show_cols if c in df.columns]

    if n_err == 0:
        st.success("✅ Алдаатай гүйлгээ олдсонгүй!")
    else:
        def highlight_err(val):
            return "background-color:#ffe0e0;color:#cc0000;font-weight:bold" if val else ""

        styled = df_err[show_cols].style.map(highlight_err, subset=["Алдаа"])
        st.dataframe(styled, use_container_width=True, height=500)

    st.markdown("---")
    with st.spinner("Excel файл бэлтгэж байна..."):
        excel_buf = to_excel(df_err)

    st.download_button(
        label=f"📥 Excel татах  —  {n_err:,} алдаатай гүйлгээ",
        data=excel_buf,
        file_name="trr_aldaa_shalgah.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
    st.caption("Excel файлд алдаатай гүйлгээнүүд байна")

else:
    st.info("👆 XLS / XLSX файл upload хийнэ үү")
    with st.expander("ℹ️ Шалгадаг алдаануудын тайлбар"):
        st.markdown("""
| Алдааны төрөл | Тайлбар |
|---|---|
| **Давхардсан** | TRR ID давхардсан байна |
| **Агент өөр дээрээ хаасан** | Нэг MLS ID дээр ижил AgentID **Listing TRR болон Selling TRR хоёуланд** бүртгэгдсэн |
| **Шимтгэл зөрсөн** | Шимтгэлийн хувь зөвшөөрөгдсөн утгаас зөрсөн |

**Зөвшөөрөгдсөн шимтгэлийн хувь:**

| Шилжүүлэгийн төрөл | TRR Type | Зөв хувь |
|---|---|---|
| Түрээс | Listing and Selling TRR | 20%, 50%, 90% |
| Түрээс | Listing TRR | 10%, 25%, 45% |
| Худалдах | Listing and Selling TRR | 3%, 5% |
| Худалдах | Listing TRR | 1.5%, 2.5% |
""")
