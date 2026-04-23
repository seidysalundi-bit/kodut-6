import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

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

GEOJSON_FILE = "zip://maakonnad.zip"


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


def get_data_for_year(df, year):
    return df[df["Aasta"].astype(str) == str(year)]


def plot_map(df, year):
    fig, ax = plt.subplots(figsize=(12, 8))

    df.plot(
        column="Loomulik iive",
        ax=ax,
        legend=True,
        cmap="viridis",
        legend_kwds={"label": "Loomulik iive"}
    )

    ax.set_title(f"Loomulik iive maakonniti aastal {year}")
    ax.axis("off")
    return fig


st.title("Loomulik iive Eesti maakondades")
st.write("Rakendus visualiseerib Statistikaameti andmete põhjal loomulikku iivet maakonniti.")

merged_data = prepare_data()

aastad = sorted(merged_data["Aasta"].astype(str).unique())

st.sidebar.title("Seaded")
selected_year = st.sidebar.selectbox(
    "Vali aasta",
    aastad,
    index=len(aastad) - 1
)

year_data = get_data_for_year(merged_data, selected_year)
fig = plot_map(year_data, selected_year)

st.pyplot(fig)
