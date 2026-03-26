import streamlit as st

st.set_page_config(layout="wide")

st.title("ӨВӨРХАНГАЙ АЙМАГТ БҮРТГЭГДСЭН ОСОЛ ГЭМТЭЛ, ГАДНЫ ШАЛТГААНТ ӨВЧЛӨЛ, НАС БАРАЛТЫН БАЙДАЛД ХИЙСЭН ТАРХВАР ЗҮЙН СУДАЛГАА")

st.caption("""
Д.Нацагням, М.Ганцэцэг, Я.Жаргал  
Өвөрхангай аймгийн Эрүүл мэндийн газар
""")

st.info("Зүүн талын menu-ээс судалгааны хуудсыг сонгоно уу.")
def global_filter(df, st):
    st.sidebar.header("GLOBAL FILTER")

    death = st.sidebar.multiselect(
        "Нас барсан эсэх",
        df["Нас барсан эсэх"].dropna().unique()
    )

    year = st.sidebar.multiselect(
        "Он",
        sorted(df["year"].dropna().unique())
    )

    month = st.sidebar.multiselect(
        "Сар",
        sorted(df["month"].dropna().unique())
    )

    soum = st.sidebar.multiselect(
        "SOUM",
        df["SOUM"].dropna().unique()
    )

    if death:
        df = df[df["Нас барсан эсэх"].isin(death)]

    if year:
        df = df[df["year"].isin(year)]

    if month:
        df = df[df["month"].isin(month)]

    if soum:
        df = df[df["SOUM"].isin(soum)]

    return df
