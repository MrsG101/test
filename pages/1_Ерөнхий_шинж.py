import streamlit as st
import pandas as pd

# ==== DATA LOAD ====
df = pd.read_excel("health_data.xlsx")

df["Үзүүлсэн огноо"] = pd.to_datetime(df["Үзүүлсэн огноо"], errors="coerce")
df["year"] = df["Үзүүлсэн огноо"].dt.year
df["month"] = df["Үзүүлсэн огноо"].dt.month


# ==== FILTER FUNCTION COPY ====
def global_filter(df):

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


# ==== CALL FILTER ====
df = global_filter(df)

st.title("Ерөнхий шинж чанар")

st.write("Filtered rows:", len(df))
