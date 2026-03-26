import streamlit as st
import pandas as pd
import plotly.express as px

df = pd.read_excel("health_data.xlsx")
df = global_filter(df, st)

df = df[df["Та ослын үед замын хөдөлгөөнд яаж оролцож байсан бэ"].notna()]

st.title("Зам тээврийн ослын анализ")

role = df["Та ослын үед замын хөдөлгөөнд яаж оролцож байсан бэ"].value_counts().reset_index()
role.columns=["Оролцоо","count"]

fig = px.bar(role,x="Оролцоо",y="count")
st.plotly_chart(fig,use_container_width=True)
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
