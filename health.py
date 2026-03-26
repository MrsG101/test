import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<style>
.big-title {
font-size:38px;
font-weight:800;
text-align:center;
}
.small-text {
text-align:center;
font-size:16px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">ӨВӨРХАНГАЙ АЙМАГТ БҮРТГЭГДСЭН ОСОЛ ГЭМТЭЛ, ГАДНЫ ШАЛТГААНТ ӨВЧЛӨЛ, НАС БАРАЛТЫН БАЙДАЛД ХИЙСЭН ТАРХВАР ЗҮЙН СУДАЛГАА</div>', unsafe_allow_html=True)

st.markdown('<div class="small-text">Д.Нацагням, М.Ганцэцэг, Я.Жаргал<br>Өвөрхангай аймгийн Эрүүл мэндийн газар</div>', unsafe_allow_html=True)

st.divider()

st.info("Зүүн талын menu-ээс судалгааны хэсгийг сонгоно уу.")
