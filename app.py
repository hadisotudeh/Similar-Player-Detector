# coding=utf-8
# import libraries
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

# read df


@st.cache(allow_output_mutation=True)
def load_data():
    df = pd.read_csv("sofifa2020.csv")
    df['name'] = df['name'].apply(lambda name: unidecode(name))
    df["positions_list"] = df["positions"].apply(lambda x: x.split(","))
    df["contract"] = df["contract"].apply(
        lambda x: str(x).split(",")[-1].strip())
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
]

positions_list = [
    "LW",
    "LS",
    "ST",
    "RW",
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

show_columns = ['name', 'photo_url', 'teams', 'league', 'contract', 'positions', 'age', 'height', 'weight',
                'Overall Rating', 'Potential', 'Value', 'Wage', 'Release Clause', 'player_traits']

columns_to_compare = [
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
    "GKReflexes"
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
st.sidebar.title(":male-detective: Similar Player Detector")

st.sidebar.title(":pick: Filters")

st.sidebar.title("Target:")

target_player_name = st.sidebar.selectbox(
    "Player:", [""] + player_list
)

target_player_name = target_player_name.strip()

st.sidebar.title("Similar Player Conditions:")

leagues = st.sidebar.multiselect(
    "League:", [all_name] + league_list, default=default_leagues
)

age = st.sidebar.slider("Age:", min_value=15, max_value=50, value=30)

transfer_fee = 1000000 * float(
    st.sidebar.text_input("Maximum Transfer Fee (€M):", "7.5")
)
wage = 1000 * float(st.sidebar.text_input("Maximum Wage (€K):", "50"))

top_K = st.sidebar.slider(
    "K Top Similar Players", min_value=0, max_value=20, value=5
)

is_scan = st.sidebar.button("Detect")

st.sidebar.header("About")
st.sidebar.info(
    "Similar Player Detecor finds the most similar players to the one you search (developed by Hadi Sotudeh <hadisotudeh1992@gmail.com>)."
)

##############################################################################
# if detect button is clicked, then show the main components of the dashboard


def filter_positions(row, positions):
    for p in positions:
        if p in row["positions_list"]:
            return True
    return False


@st.cache(allow_output_mutation=True)
def scan(leagues, transfer_fee, wage, age):
    df = load_data()

    target_player = df.loc[df['name'] == target_player_name]
    positions = target_player['positions'].iloc[0].split(",")

    target_player_KPIs = target_player[columns_to_compare].to_numpy()[0]

    df = df.loc[df['name'] != target_player_name]
    df = df[df["age"] <= age]
    if all_name not in leagues:
        df = df[df["league"].isin(leagues)]
    df = df[(df["Value"] <= transfer_fee) & (df["Wage"] <= wage)]

    df["filter_positions"] = df.apply(
        lambda row: filter_positions(row, positions), axis=1)
    search_space = df.loc[df["filter_positions"] == True]

    # calculate ANNOY
    annoy = AnnoyIndex(len(columns_to_compare), 'euclidean')
    search_space_array = search_space[columns_to_compare].to_numpy()

    for i in range(search_space_array.shape[0]):
        annoy.add_item(i, search_space_array[i, :])
    annoy.build(n_trees=10)

    indices = annoy.get_nns_by_vector(target_player_KPIs, top_K)
    subset = search_space.iloc[indices, :]
    return subset


if is_scan:
    result = scan(leagues, transfer_fee, wage, age)
    st.write(result[show_columns])
