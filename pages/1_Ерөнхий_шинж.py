import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(layout="wide")

@st.cache_data
def load():
    df = pd.read_excel("health_data.xlsx")

    df.columns = df.columns.str.strip()

    df["Үзүүлсэн огноо"] = pd.to_datetime(df["Үзүүлсэн огноо"], errors="coerce")
    df["year"] = df["Үзүүлсэн огноо"].dt.year
    df["month"] = df["Үзүүлсэн огноо"].dt.month

    return df

df = load()

# ===== GLOBAL FILTER =====
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

df = global_filter(df)

st.title("Ерөнхий тархвар зүйн шинж")

# ===== KPI =====
col1,col2,col3 = st.columns(3)

total = len(df)
death = df["Нас барсан эсэх"].eq("Нас барсан").sum()
death_rate = round(death/total*100,2) if total>0 else 0

col1.metric("Нийт тохиолдол", total)
col2.metric("Нас барсан", death)
col3.metric("Нас баралтын хувь %", death_rate)

st.divider()

# ===== Seasonality =====
st.subheader("Seasonality")

season = df.groupby("month").size().reset_index(name="count")

fig = px.line(season, x="month", y="count", markers=True)
st.plotly_chart(fig, use_container_width=True)

# ===== Cause =====
st.subheader("Осол гэмтлийн шалтгаан")

cause = df["Осол гэмтлийн шалтгаан, бүлгээр"].value_counts().head(10).reset_index()
cause.columns = ["Шалтгаан","count"]

fig2 = px.bar(cause, x="count", y="Шалтгаан", orientation="h")
st.plotly_chart(fig2, use_container_width=True)

# ===== SOUM MAP =====
st.subheader("Сумаар тархалт")

with open("mongolia_soum.geojson","r",encoding="utf-8") as f:
    geo = json.load(f)

map_df = df.groupby("SOUM").size().reset_index(name="count")

fig3 = px.choropleth_mapbox(
    map_df,
    geojson=geo,
    locations="SOUM",
    featureidkey="properties.soum_code",
    color="count",
    color_continuous_scale="Reds",
    mapbox_style="carto-positron",
    zoom=5.3,
    center={"lat":46.5,"lon":103}
)

fig3.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

st.plotly_chart(fig3, use_container_width=True)
