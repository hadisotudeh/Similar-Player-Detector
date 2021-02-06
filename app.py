# coding=utf-8
# import libraries
import requests
import base64
import subprocess
import pandas as pd
import streamlit as st
from annoy import AnnoyIndex
import os
import math
import warnings
from unidecode import unidecode

warnings.simplefilter("ignore")

# variables
all_name = "All"
photo_profile_dir = "profile_photo/"

for file in os.listdir():
    if file.endswith(".png"):
        os.remove(file)

# load data

st.set_page_config(
    page_title="Similar Player Detector",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache(allow_output_mutation=True)
def load_data():
    df = pd.read_csv("data/sofifa2020.csv")
    df["name"] = df["name"].apply(lambda name: unidecode(name))
    # df["positions_list"] = df["positions"].apply(lambda x: x.split(","))
    df["contract"] = df["contract"].apply(
        lambda x: int(x) if not math.isnan(x) else 2020
    )
    # df["contract"] = df["contract"].astype(int)
    df["player_hashtags"] = (
        df["player_traits"].apply(
            lambda x: ", ".join([c.replace("(AI)", "").strip() for c in eval(x)])
        )
        + ", "
        + df["player_hashtags"].apply(
            lambda x: ", ".join([c.replace("#", "").strip() for c in eval(x)])
        )
    )

    df["player_hashtags"] = df["player_hashtags"].apply(lambda row: row.rstrip(", "))
    return df


df = load_data()
league_list = list(df["league"].unique())
player_list = list(df["name"].unique())

default_leagues = [
    "Spain Primera Division",
    "Italian Serie A",
    "French Ligue 1",
    "English Premier League",
    "German 1. Bundesliga",
    "Holland Eredivisie",
    "Portuguese Liga ZON SAGRES",
    "Campeonato Brasileiro Série A",
    "Argentina Primera División",
    "Belgian Jupiler Pro League",
    "English League Championship",
]

default_positions = ["ST", "CF", "LF", "RF", "LS", "RS", "RW", "LW"]

positions_list = [
    "LW",
    "LS",
    "ST",
    "RW",
    "RS",
    "LF",
    "CF",
    "RF",
    "CAM",
    "LM",
    "CM",
    "RM",
    "CDM",
    "LWB",
    "LB",
    "CB",
    "RB",
    "RWB",
    "GK",
]

show_columns = [
    "photo_url",
    "name",
    "teams",
    "league",
    "age",
    "positions",
    "Overall Rating",
    "Potential",
    "contract",
    "Value",
    "player_hashtags",
]

default_columns_to_compare = [
    "Potential",
    "Finishing",
    "HeadingAccuracy",
    "Volleys",
    "Dribbling",
    "Curve",
    "BallControl",
    "Acceleration",
    "SprintSpeed",
    "Agility",
    "Reactions",
    "Balance",
    "ShotPower",
    "Jumping",
    "Stamina",
    "Strength",
    "LongShots",
    "Aggression",
    "Positioning",
    "Vision",
    "Composure",
]

possible_columns_to_compare = [
    "Overall Rating",
    "Potential",
    "Crossing",
    "Finishing",
    "HeadingAccuracy",
    "ShortPassing",
    "Volleys",
    "Dribbling",
    "Curve",
    "FKAccuracy",
    "LongPassing",
    "BallControl",
    "Acceleration",
    "SprintSpeed",
    "Agility",
    "Reactions",
    "Balance",
    "ShotPower",
    "Jumping",
    "Stamina",
    "Strength",
    "LongShots",
    "Aggression",
    "Interceptions",
    "Positioning",
    "Vision",
    "Penalties",
    "Composure",
    "DefensiveAwareness",
    "StandingTackle",
    "SlidingTackle",
    "GKDiving",
    "GKHandling",
    "GKKicking",
    "GKPositioning",
    "GKReflexes",
]

################################################################
# css style
hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Annoy (Approximate Nearest Neighbors Oh Yeah) is a C++ library with Python bindings to search for points in space that are close to a given query point. It also creates large read-only file-based data structures that are mmapped into memory so that many processes may share the same data.
# https://github.com/spotify/annoy

##################################################################
# sidebar filters
st.sidebar.title(":pick: Filters")

st.sidebar.title("Target:")

target_player_name = st.sidebar.selectbox("Player:", [""] + player_list)

target_player_name = target_player_name.strip()

st.sidebar.title("Similar Player Conditions:")

leagues = st.sidebar.multiselect(
    "League:", [all_name] + league_list, default=default_leagues
)

positions = st.sidebar.multiselect(
    "Position:", positions_list, default=default_positions
)

age = st.sidebar.slider("Age:", min_value=15, max_value=50, value=27)

transfer_fee = 1000000 * float(
    st.sidebar.text_input("Maximum Transfer Fee (€M):", "100")
)
wage = 1000 * float(st.sidebar.text_input("Maximum Wage (€K):", "200"))

columns_to_compare = st.sidebar.multiselect(
    "KPIs:", possible_columns_to_compare, default=default_columns_to_compare
)

top_K = st.sidebar.slider("K Top Similar Players", min_value=0, max_value=20, value=10)

is_scan = st.sidebar.button("Detect")

st.sidebar.image(
    "agent.jpg",
    caption="https://www.wikihow.com/Become-a-Football-Agent",
    use_column_width=True,
)
st.sidebar.header("Contact Info")
st.sidebar.info("hadisotudeh1992[at]gmail.com")

##############################################################################
# if detect button is clicked, then show the main components of the dashboard


def filter_positions(row, positions):
    for p in positions:
        if p in eval(row["positions"]):
            return True
    return False


def upload_local_photo(file):
    file_ = open(file, "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()
    return data_url


def download_photo_url(url):
    photo_name = "_".join(url.split("/")[-3:])

    r = requests.get(url, allow_redirects=True)
    open(photo_name, "wb").write(r.content)

    return photo_name


def create_table(data, width=100, class_="", image_height=95, image_width=95):
    if len(class_) > 0:
        table = f'<table class="{class_}" style="text-align: center; width:{width}%">'
    else:
        table = f'<table style="text-align: center; width:{width}%">'

    # create header row
    header_html = "<tr>"
    for col in data.columns:
        if col == "photo_url":
            header_html = header_html + "<th>Photo</th>"
        elif col == "Value":
            header_html = header_html + "<th>Value (€M)</th>"
        elif col == "player_hashtags":
            header_html = header_html + "<th>Description</th>"
        else:
            header_html = header_html + f"<th>{col.capitalize()}</th>"
    header_html = header_html + "<tr>"

    all_rows_html = ""
    for row_index in range(len(data)):
        row_html = "<tr>"
        row = data.iloc[row_index]
        for col in data.columns:
            if col == "photo_url":
                local_photo = download_photo_url(row[col])
                data_url = upload_local_photo(local_photo)
                row_html = (
                    row_html
                    + f'<td><img src="data:image/gif;base64,{data_url}" height="{image_height} width="{image_width}"></img></td>'
                )
            elif row[col] == None:
                row_html = row_html + "<td></td>"
            elif col == "positions":
                row_html = row_html + f'<td>{", ".join(eval(row[col]))}</td>'
            else:
                row_html = row_html + f"<td>{row[col]}</td>"
        row_html = row_html + "</tr>"
        all_rows_html = all_rows_html + row_html

    table = table + header_html + all_rows_html + "</table>"
    st.markdown(table, unsafe_allow_html=True)


# @st.cache(allow_output_mutation=True)
def scan(target_player, leagues, positions, transfer_fee, wage, age):
    df = load_data()

    target_player_KPIs = target_player[columns_to_compare].to_numpy()[0]

    df = df.loc[df["name"] != target_player_name]
    df = df[df["age"] <= age]
    if all_name not in leagues:
        df = df[df["league"].isin(leagues)]
    df = df[(df["Value"] <= transfer_fee) & (df["Wage"] <= wage)]

    df["filter_positions"] = df.apply(
        lambda row: filter_positions(row, positions), axis=1
    )
    search_space = df.loc[df["filter_positions"] == True]
    search_space.reset_index(drop=True, inplace=True)

    # search_space["label"] = pd.Series(list(clf.fit_predict(X)))
    # search_space["score"] = pd.Series(list(clf.score_samples(X)))
    # search_space.sort_values(by=["score"], inplace=True)

    # calculate ANNOY
    annoy = AnnoyIndex(len(columns_to_compare), "euclidean")
    search_space_array = search_space[columns_to_compare].to_numpy()

    for i in range(search_space_array.shape[0]):
        annoy.add_item(i, search_space_array[i, :])
    annoy.build(n_trees=1000)

    indices = annoy.get_nns_by_vector(target_player_KPIs, top_K)
    return pd.concat([search_space.iloc[index : index + 1, :] for index in indices])


@st.cache(allow_output_mutation=True)
def calc_target_player(target_player_name):
    target_player = df.loc[df["name"] == target_player_name]
    return target_player


if is_scan:
    target_player = calc_target_player(target_player_name)
    target_player_age = target_player["age"].iloc[0]
    target_player_teams = target_player["teams"].iloc[0]
    url = target_player["photo_url"].iloc[0]
    local_photo = download_photo_url(url)
    data_url = upload_local_photo(local_photo)
    st.title("Target Player:")
    st.markdown(
        f"![](data:image/gif;base64,{data_url}) **{target_player_name}** - **{target_player_teams}**"
    )
    result = scan(target_player, leagues, positions, transfer_fee, wage, age)
    st.markdown(f"**Top _{top_K}_ most similar players are**:")
    result["Value"] = result["Value"].apply(lambda v: str(v / 1000000))
    create_table(result[show_columns])
else:
    st.title(":male-detective: Similar Player Detector")
    st.subheader(
        "This app makes use of [EA SPORTS™ FIFA 2020](https://sofifa.com) KPIs to search for similar players to a given one."
    )
    st.subheader(
        "It first applies filters such as league, age, and market value on players. Then, each remaining player is considered as a vector of their KPIs and afterwards [Annoy (Approximate Nearest Neighbors Oh Yeah)](https://github.com/spotify/annoy) is used to search for players (points) in space that are close to a given query."
    )
    st.image("annoy.jpg", caption="https://github.com/spotify/annoy")
