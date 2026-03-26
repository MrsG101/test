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

# ===== GLOBAL FILTER =====
df = global_filter(df)

st.title("Осол гэмтлийн ерөнхий тархвар зүйн шинж")

total = len(df)

# ===== KPI =====
col1,col2,col3,col4 = st.columns(4)

col1.metric("Нийт тохиолдол", total)

death = df["Нас барсан эсэх"].eq("Нас барсан").sum()
death_rate = round(death/total*100,1) if total>0 else 0

col2.metric("Нас барсан", death)
col3.metric("Нас баралтын хувь %", death_rate)

alcohol = df["Гэмтэл авах үедээ согтууруулах ундаа хэрэглэсэн эсэх"].eq("Тийм").sum()
alcohol_rate = round(alcohol/total*100,1) if total>0 else 0

col4.metric("Согтууруулах холбоотой %", alcohol_rate)

st.divider()

# ==========================================================
# НАСНЫ БҮЛЭГ
# ==========================================================
st.subheader("Насны бүлгээр")

age = df["Насны бүлгээр"].value_counts().reset_index()
age.columns = ["Насны бүлэг","count"]
age["percent"] = round(age["count"]/total*100,1)

fig_age = px.bar(
    age,
    x="Насны бүлэг",
    y="count",
    text="percent"
)

fig_age.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig_age, use_container_width=True)

# ==========================================================
# ХҮЙС
# ==========================================================
st.subheader("Хүйс")

gender = df["Хүйс"].value_counts().reset_index()
gender.columns = ["Хүйс","count"]

fig_gender = px.pie(
    gender,
    names="Хүйс",
    values="count"
)

fig_gender.update_traces(textinfo="percent+label")

st.plotly_chart(fig_gender, use_container_width=True)

# ==========================================================
# СУМ (GRAPH HEAT STYLE)
# ==========================================================
st.subheader("Сумаар тархалт")

soum = df["SOUM"].value_counts().head(15).reset_index()
soum.columns = ["Сум","count"]
soum["percent"] = round(soum["count"]/total*100,1)

fig_soum = px.bar(
    soum,
    x="count",
    y="Сум",
    orientation="h",
    text="percent",
    color="count",
    color_continuous_scale="Reds"
)

fig_soum.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig_soum, use_container_width=True)

# ==========================================================
# АЖИЛ МЭРГЭЖИЛ
# ==========================================================
st.subheader("Албан тушаал / ажил мэргэжил")

job = df["Албан тушаал"].value_counts().head(10).reset_index()
job.columns = ["Ажил","count"]
job["percent"] = round(job["count"]/total*100,1)

fig_job = px.bar(
    job,
    x="count",
    y="Ажил",
    orientation="h",
    text="percent"
)

fig_job.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig_job, use_container_width=True)

# ==========================================================
# ОСОЛ БОЛСОН БАЙРШИЛ
# ==========================================================
st.subheader("Осол болсон байршил")

place = df["Осол гарах үеийн байршил"].value_counts().reset_index()
place.columns = ["Байршил","count"]
place["percent"] = round(place["count"]/total*100,1)

fig_place = px.bar(
    place,
    x="count",
    y="Байршил",
    orientation="h",
    text="percent"
)

fig_place.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig_place, use_container_width=True)

# ==========================================================
# SEASONALITY
# ==========================================================
st.subheader("Сараар тархалт")

season = df.groupby("month").size().reset_index(name="count")

fig_season = px.line(
    season,
    x="month",
    y="count",
    markers=True
)

st.plotly_chart(fig_season, use_container_width=True)
