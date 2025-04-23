"""
Name:  Jason Juarez
Section: CS230-6
Data: Top 2000 Global Companies

Description:
This program allows users to explore the top 2000 global companies to evaluate which regions have the best potential for growth.
It uses a user adjusted growth score using profit margin, asset leverage, and market undervaluation. Users can adjust weights for each metric by adjusting sliders.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pydeck as pdk

df = pd.read_csv("Top2000CompaniesGlobally.csv")
df.dropna(inplace=True)

df = df[  # only uses company data with positive figures because it will affect calculations
    (df['Sales ($billion)'] > 0) &
    (df['Profits ($billion)'] > 0) &
    (df['Market Value ($billion)'] > 0) &
    (df['Assets ($billion)'] > 0)
]

# [DA9] new metrics for calculations
df['Profit Margin'] = df['Profits ($billion)'] / df['Sales ($billion)']
df['Asset Leverage'] = df['Assets ($billion)'] / df['Market Value ($billion)']
df['Undervaluation'] = (df['Profits ($billion)'] + df['Sales ($billion)']) / df['Market Value ($billion)']

# [ST4]
st.sidebar.title("Customize Growth Score")
st.title("Regional Growth Potential Explorer")
st.markdown("Use the sliders to configure the weight of your assumptions for company growth. Explore regions and companies based on their potential for financial growth.")

# [ST1] sliders for assumption weights
w1 = st.sidebar.slider("Weight: Profit Margin", 0.0, 1.0, 0.4)
w2 = st.sidebar.slider("Weight: Asset Leverage", 0.0, 1.0, 0.3)
w3 = st.sidebar.slider("Weight: Undervaluation", 0.0, 1.0, 0.3)
total = w1 + w2 + w3
w1, w2, w3 = w1 / total, w2 / total, w3 / total

# [PY1] calculating growth scores of companies using adjusted weights
@st.cache_data
def compute_growth_score(df, w1=0.4, w2=0.3, w3=0.3):
    df = df.copy()
    df['Growth Score'] = (
        w1 * df['Profit Margin'] +
        w2 * df['Asset Leverage'] +
        w3 * df['Undervaluation']
    )
    return df[['Company', 'Country', 'Continent', 'Growth Score', 'Latitude', 'Longitude']]

# finding average growth scores to use for growth scores of continents
@st.cache_data
def get_grouped_scores(df):
    grouped = df.groupby('Continent').agg(
        Avg_Score=('Growth Score', 'mean'),
        Company_Count=('Company', 'count')
    ).reset_index()
    return grouped, grouped.sort_values(by='Avg_Score', ascending=False)

# [PY3]
try:
    scored_df = compute_growth_score(df, w1, w2, w3)
    grouped_df, sorted_grouped_df = get_grouped_scores(scored_df)
except Exception as e:
    st.error(f"Error computing growth score: {e}")

# [ST2] dropdown for bar chart
region_option = st.selectbox("Select Region View", ["Continent", "Country"])

# [PY1] [CHART1] bar chart option of countries or continents
if region_option == "Continent":
    grouped_df = scored_df.groupby('Continent').agg(
        Avg_Score=('Growth Score', 'mean'),
        Company_Count=('Company', 'count')
    ).reset_index()
    sorted_grouped_df = grouped_df.sort_values(by='Avg_Score', ascending=False)


    fig, ax = plt.subplots()
    colors = plt.cm.Blues(np.linspace(0.4, 1, len(sorted_grouped_df)))
    ax.barh(sorted_grouped_df['Continent'], sorted_grouped_df['Avg_Score'], color=colors)
    ax.set_title("Average Growth Score by Continent")
    ax.set_xlabel("Growth Score")
    ax.set_ylabel("Continent")
    st.pyplot(fig)

elif region_option == "Country":
    grouped_df = scored_df.groupby('Country').agg(
        Avg_Score=('Growth Score', 'mean'),
        Company_Count=('Company', 'count')
    ).reset_index()
    sorted_grouped_df = grouped_df.sort_values(by='Avg_Score', ascending=False)

    # only top 10 countries because of crowded visual
    top_10_countries = sorted_grouped_df.head(10)

    fig, ax = plt.subplots()
    colors = plt.cm.Blues(np.linspace(0.4, 1, len(top_10_countries)))
    ax.barh(top_10_countries['Country'], top_10_countries['Avg_Score'], color=colors)
    ax.set_title("Top 10 Countries by Average Growth Score")
    ax.set_xlabel("Growth Score")
    ax.set_ylabel("Country")
    st.pyplot(fig)

# [DA3] chart of companies by greatest growth score
st.subheader("Top Companies by Growth Score")
# [ST3] slider for how many companies to show
top_n = st.slider("Number of top companies to view:", 5, 50, 10)
scored_df = scored_df.dropna(subset=['Growth Score'])
top_companies = scored_df.sort_values(by='Growth Score', ascending=False).head(top_n)
st.dataframe(top_companies)

# [MAP] map of global companies
st.subheader("Company Locations by Growth Score")
layer = pdk.Layer(
    'ScatterplotLayer',
    data=scored_df,
    get_position='[Longitude, Latitude]',
    get_color='[200, 30, 0, 160]',
    get_radius=10000,
    pickable=True
)
view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=1.5,
    pitch=0
)
map = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{Company}\nScore: {Growth Score}"})
st.pydeck_chart(map)

# [PY4] list of companies with growth score greater than 20
high_score_companies = [row['Company'] for _, row in scored_df.iterrows() if row['Growth Score'] > 20]

# [PY5] shows a count of how many companies per continent
continent_counts = {cont: len(scored_df[scored_df['Continent'] == cont]) for cont in scored_df['Continent'].unique()}
st.sidebar.write("Company Count per Continent:", continent_counts)

st.markdown("**Note:** Not financial advice.")
