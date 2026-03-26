import json
import plotly.express as px

st.subheader("🇲🇳 Сумаар осол гэмтлийн тархалт")

with open("mongolia_soum.geojson","r",encoding="utf-8") as f:
    geo = json.load(f)

map_df = (
    df.groupby("SOUM")
    .size()
    .reset_index(name="count")
)

fig = px.choropleth_mapbox(
    map_df,
    geojson=geo,
    locations="SOUM",
    featureidkey="properties.soum_code",
    color="count",
    color_continuous_scale="Reds",
    mapbox_style="carto-positron",
    zoom=5.2,
    center={"lat":46.5,"lon":103}
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

st.plotly_chart(fig,use_container_width=True)
