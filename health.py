import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    df = pd.read_excel("health_data.xlsx")

    df.columns = df.columns.str.strip()

    # date parse
    df["Үзүүлсэн огноо"] = pd.to_datetime(df["Үзүүлсэн огноо"], errors="coerce")

    df["year"] = df["Үзүүлсэн огноо"].dt.year
    df["month"] = df["Үзүүлсэн огноо"].dt.month

    return df

df = load_data()

st.title("🚑 Осол гэмтлийн аналитик дашбоард")

# ================= SIDEBAR FILTER =================
st.sidebar.header("Filter")

year = st.sidebar.multiselect(
    "Он",
    sorted(df["year"].dropna().unique()),
    default=sorted(df["year"].dropna().unique())
)

soum = st.sidebar.multiselect(
    "Сум",
    df["SOUM"].dropna().unique()
)

gender = st.sidebar.multiselect(
    "Хүйс",
    df["Хүйс"].dropna().unique()
)

filtered = df.copy()

if year:
    filtered = filtered[filtered["year"].isin(year)]

if soum:
    filtered = filtered[filtered["SOUM"].isin(soum)]

if gender:
    filtered = filtered[filtered["Хүйс"].isin(gender)]

# ================= KPI =================
col1, col2, col3, col4 = st.columns(4)

total_case = len(filtered)
death_case = len(filtered[filtered["Шилжүүлсэн хэлбэр"]=="Нас барсан"])
alcohol_case = len(filtered[
    filtered["Гэмтэл авах үедээ согтууруулах ундаа хэрэглэсэн эсэх"]=="Тийм"
])
violence_case = filtered["Хүчирхийлэлийн хэлбэр"].notna().sum()

col1.metric("Нийт кейс", total_case)
col2.metric("Нас барсан", death_case)
col3.metric("Согтууруулах холбоотой", alcohol_case)
col4.metric("Хүчирхийллийн кейс", violence_case)

st.divider()

# ================= TIME TREND =================
st.subheader("📈 Осол гэмтэл хугацаагаар")

trend = (
    filtered
    .groupby(["year","month"])
    .size()
    .reset_index(name="count")
)

fig = px.line(
    trend,
    x="month",
    y="count",
    color="year",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ================= AGE GROUP =================
col1, col2 = st.columns(2)

with col1:
    st.subheader("👥 Насны бүлэг")
    age = filtered["Насны бүлгээр"].value_counts().reset_index()
    age.columns = ["Насны бүлэг","count"]

    fig2 = px.bar(age, x="Насны бүлэг", y="count")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.subheader("🚻 Хүйс")
    g = filtered["Хүйс"].value_counts().reset_index()
    g.columns = ["Хүйс","count"]

    fig3 = px.pie(g, names="Хүйс", values="count")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ================= CAUSE =================
st.subheader("⚠️ Осол гэмтлийн шалтгаан")

cause = (
    filtered["Осол гэмтлийн шалтгаан, бүлгээр"]
    .value_counts()
    .head(10)
    .reset_index()
)

cause.columns = ["Шалтгаан","count"]

fig4 = px.bar(
    cause,
    x="count",
    y="Шалтгаан",
    orientation="h"
)

st.plotly_chart(fig4, use_container_width=True)

# ================= LOCATION =================
st.subheader("📍 Сумаар тархалт")

map_df = filtered["SOUM"].value_counts().reset_index()
map_df.columns = ["SOUM","count"]

fig5 = px.bar(
    map_df.head(15),
    x="SOUM",
    y="count"
)

st.plotly_chart(fig5, use_container_width=True)
