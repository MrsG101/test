import streamlit as st
import pandas as pd
import plotly.express as px
from filter import global_filter

st.set_page_config(layout="wide")

# ===== DATA LOAD =====
@st.cache_data
def load():
    df = pd.read_excel("health_data.xlsx")

    df.columns = df.columns.str.strip()

    df["Үзүүлсэн огноо"] = pd.to_datetime(df["Үзүүлсэн огноо"], errors="coerce")
    df["year"] = df["Үзүүлсэн огноо"].dt.year
    df["month"] = df["Үзүүлсэн огноо"].dt.month

    return df

df = load()

# ===== FILTER =====
df = global_filter(df)

# ===== Зөвхөн амиа хорлолт =====
df = df[df["Амиа хорлоход хүргэсэн хэлбэр"].notna()]

st.title("Амиа хорлолтын тархвар зүйн шинжилгээ")

total = len(df)

# ================= KPI =================
col1,col2,col3 = st.columns(3)

col1.metric("Нийт кейс", total)

death = df["Нас барсан эсэх"].eq("Нас барсан").sum()
death_rate = round(death/total*100,1) if total>0 else 0

col2.metric("Нас барсан", death)
col3.metric("Нас баралтын хувь %", death_rate)

st.divider()

# ================= ХЭЛБЭР =================
st.subheader("Амиа хорлоход хүргэсэн хэлбэр")

form = df["Амиа хорлоход хүргэсэн хэлбэр"].value_counts().reset_index()
form.columns = ["Хэлбэр","count"]
form["percent"] = round(form["count"]/total*100,1)

fig1 = px.bar(
    form,
    x="count",
    y="Хэлбэр",
    orientation="h",
    text="percent"
)

fig1.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig1, use_container_width=True)

# ================= АРГА =================
st.subheader("Хэрэглэсэн арга / зүйл")

method = df["Хэрэглэсэн арга/зүйл"].value_counts().reset_index()
method.columns = ["Арга","count"]
method["percent"] = round(method["count"]/total*100,1)

fig2 = px.bar(
    method,
    x="count",
    y="Арга",
    orientation="h",
    text="percent"
)

fig2.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig2, use_container_width=True)

# ================= ХҮЙС =================
st.subheader("Хүйс")

gender = df["Хүйс"].value_counts().reset_index()
gender.columns = ["Хүйс","count"]

fig3 = px.pie(
    gender,
    names="Хүйс",
    values="count"
)

fig3.update_traces(textinfo="percent+label")

st.plotly_chart(fig3, use_container_width=True)

# ================= НАСНЫ БҮЛЭГ =================
st.subheader("Насны бүлгээр")

age = df["Насны бүлгээр"].value_counts().reset_index()
age.columns = ["Нас","count"]
age["percent"] = round(age["count"]/total*100,1)

fig4 = px.bar(
    age,
    x="Нас",
    y="count",
    text="percent"
)

fig4.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig4, use_container_width=True)
