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

# ===== Зөвхөн зам тээврийн осол =====
df = df[df["Та ослын үед замын хөдөлгөөнд яаж оролцож байсан бэ"].notna()]

st.title("Зам тээврийн ослын тархвар зүйн шинжилгээ")

total = len(df)

# ================= KPI =================
col1,col2,col3,col4 = st.columns(4)

col1.metric("Нийт кейс", total)

death = df["Нас барсан эсэх"].eq("Нас барсан").sum()
death_rate = round(death/total*100,1) if total>0 else 0

col2.metric("Нас барсан", death)
col3.metric("Нас баралтын хувь %", death_rate)

helmet = df["Хамгаалалтын малгай"].eq("Тийм").sum()
helmet_rate = round(helmet/total*100,1) if total>0 else 0

col4.metric("Хамгаалалт хэрэглэсэн %", helmet_rate)

st.divider()

# ================= ТЭЭВРИЙН ХЭРЭГСЭЛ =================
st.subheader("Тээврийн хэрэгслийн төрөл")

vehicle = df["Осол гарах үед та ямар тээврийн хэрэгслээр явж байсан бэ"].value_counts().reset_index()
vehicle.columns = ["Тээврийн хэрэгсэл","count"]
vehicle["percent"] = round(vehicle["count"]/total*100,1)

fig1 = px.bar(
    vehicle,
    x="count",
    y="Тээврийн хэрэгсэл",
    orientation="h",
    text="percent"
)

fig1.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig1, use_container_width=True)

# ================= ОРОЛЦОО =================
st.subheader("Замын хөдөлгөөнд оролцсон байдал")

role = df["Та ослын үед замын хөдөлгөөнд яаж оролцож байсан бэ"].value_counts().reset_index()
role.columns = ["Оролцоо","count"]
role["percent"] = round(role["count"]/total*100,1)

fig2 = px.bar(
    role,
    x="count",
    y="Оролцоо",
    orientation="h",
    text="percent"
)

fig2.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig2, use_container_width=True)

# ================= МӨРГӨЛДСӨН ЗҮЙЛ =================
st.subheader("Мөргөлдсөн зүйл")

impact = df["Та ослын үед ямар зүйлтэй мөргөлдсөн бэ"].value_counts().reset_index()
impact.columns = ["Мөргөлдсөн зүйл","count"]
impact["percent"] = round(impact["count"]/total*100,1)

fig3 = px.bar(
    impact,
    x="count",
    y="Мөргөлдсөн зүйл",
    orientation="h",
    text="percent"
)

fig3.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig3, use_container_width=True)

# ================= ХАМГААЛАЛТ =================
st.subheader("Хамгаалалт хэрэглэсэн эсэх")

protect = df["Осол гарах үед та хамгаалалт хэрэглэсэн бэ"].value_counts().reset_index()
protect.columns = ["Хамгаалалт","count"]

fig4 = px.pie(
    protect,
    names="Хамгаалалт",
    values="count"
)

fig4.update_traces(textinfo="percent+label")

st.plotly_chart(fig4, use_container_width=True)

# ================= НАСНЫ БҮЛЭГ =================
st.subheader("Насны бүлгээр")

age = df["Насны бүлгээр"].value_counts().reset_index()
age.columns = ["Нас","count"]
age["percent"] = round(age["count"]/total*100,1)

fig5 = px.bar(
    age,
    x="Нас",
    y="count",
    text="percent"
)

fig5.update_traces(texttemplate="%{text}%", textposition="outside")

st.plotly_chart(fig5, use_container_width=True)
