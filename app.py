import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "zip://maakonnad.zip"

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2014",
          "2015",
          "2016",
          "2017",
          "2018",
          "2019",
          "2020",
          "2021",
          "2022",
          "2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39",
          "44",
          "49",
          "51",
          "57",
          "59",
          "65",
          "67",
          "70",
          "74",
          "78",
          "82",
          "84",
          "86",
          "37"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": [
          "2",
          "3"
        ]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""


@st.cache_data
def import_data():
    headers = {"Content-Type": "application/json"}
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)

    if response.status_code == 200:
        text = response.content.decode("utf-8-sig")
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"Andmete laadimine ebaõnnestus. Staatuskood: {response.status_code}")
        st.stop()


@st.cache_data
def import_geojson():
    gdf = gpd.read_file(GEOJSON_FILE)
    return gdf


def prepare_data():
    df = import_data()
    gdf = import_geojson()

    merged_data = gdf.merge(df, left_on="MNIMI", right_on="Maakond")
    merged_data["Loomulik iive"] = (
        merged_data["Mehed Loomulik iive"] + merged_data["Naised Loomulik iive"]
    )

    return merged_data


def get_data_for_filters(df, year, selected_counties):
    filtered = df[df["Aasta"].astype(str) == str(year)].copy()

    if selected_counties:
        filtered = filtered[filtered["Maakond"].isin(selected_counties)]

    return filtered


def plot_map(df, year, indicator, cmap):
    fig, ax = plt.subplots(figsize=(12, 8))

    if df.empty:
        ax.text(0.5, 0.5, "Valitud filtritega andmeid ei leitud", ha="center", va="center", fontsize=14)
        ax.axis("off")
        return fig

    df.plot(
        column=indicator,
        ax=ax,
        legend=True,
        cmap=cmap,
        legend_kwds={"label": indicator}
    )

    ax.set_title(f"{indicator} maakonniti aastal {year}")
    ax.axis("off")
    return fig


st.set_page_config(page_title="Loomulik iive Eesti maakondades", layout="wide")

st.title("Loomulik iive Eesti maakondades")
st.write("Rakendus visualiseerib Statistikaameti andmete põhjal maakondade näitajaid.")

merged_data = prepare_data()

aastad = sorted(merged_data["Aasta"].astype(str).unique())
maakonnad = sorted(merged_data["Maakond"].dropna().unique())

st.sidebar.title("Seaded")

selected_year = st.sidebar.selectbox(
    "Vali aasta",
    aastad,
    index=len(aastad) - 1
)

indicator = st.sidebar.selectbox(
    "Vali näitaja",
    ["Loomulik iive", "Mehed Loomulik iive", "Naised Loomulik iive"]
)

selected_counties = st.sidebar.multiselect(
    "Vali maakonnad",
    maakonnad,
    default=maakonnad
)

cmap = st.sidebar.selectbox(
    "Vali värviskaala",
    ["viridis", "plasma", "coolwarm", "Blues", "Greens", "OrRd"],
    index=0
)

year_data = get_data_for_filters(merged_data, selected_year, selected_counties)

col1, col2, col3 = st.columns(3)

if not year_data.empty:
    max_row = year_data.loc[year_data[indicator].idxmax()]
    min_row = year_data.loc[year_data[indicator].idxmin()]
    mean_value = year_data[indicator].mean()

    col1.metric("Suurim väärtus", f"{max_row[indicator]:.0f}", max_row["Maakond"])
    col2.metric("Väikseim väärtus", f"{min_row[indicator]:.0f}", min_row["Maakond"])
    col3.metric("Keskmine", f"{mean_value:.1f}")
else:
    col1.metric("Suurim väärtus", "-")
    col2.metric("Väikseim väärtus", "-")
    col3.metric("Keskmine", "-")

fig = plot_map(year_data, selected_year, indicator, cmap)
st.pyplot(fig)

st.subheader("Andmed tabelina")
if not year_data.empty:
    st.dataframe(
        year_data[["Maakond", "Aasta", "Loomulik iive", "Mehed Loomulik iive", "Naised Loomulik iive"]]
        .sort_values(by=indicator, ascending=False)
        .reset_index(drop=True)
    )
else:
    st.info("Valitud filtritega andmeid ei leitud.")
