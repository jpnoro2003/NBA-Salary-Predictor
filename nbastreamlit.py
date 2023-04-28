# Import useful libraries
import streamlit as st
import pickle
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np

# Fetch player search results from BasketballReference
def search_results(Name):
    
    formatted_url = "https://www.basketball-reference.com/search/search.fcgi?search=" + Name.replace(" ","%20")
    page = requests.get(formatted_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('div', class_="search-item-name")
    results_list = {"Name": [], "Link": []}
    
    # Redirects straight to player page
    if len(results) == 0 and len(soup.find_all('div', id="info")) > 0:
        print(1)
        name = soup.find('div', id="info").find_all('span')[0].text.strip()
        print(name)
        link = soup.find('div', id="bottom_nav_container").find_all('a')[0]
        results_list = {"Name": [name], "Link": ["https://www.basketball-reference.com" + link['href']]}
    else: # Search Page
        print(2)
        for result in results:
            link = result.find('a')
            if link['href'][:8] == "/players":
                results_list['Name'].append(link.text)
                results_list['Link'].append("https://www.basketball-reference.com" + link['href'])
    return results_list


# Get player's data from bball-ref page
def get_player_data(link, year):
    
    # Read tables from page
    player_data = pd.read_html(link, flavor="html5lib")
    
    # Select data (if there are more than 6 tables, then the player has playoff experience - have to select different tables)
    if len(player_data) >= 6:
        base_data = player_data[0]
        adv_data = player_data[5]
    else:
        base_data = player_data[0]
        adv_data = player_data[3]
    
    # Select Relevant year
    base_data = base_data[base_data['Season'] == year][:1]
    adv_data = adv_data[adv_data['Season'] == year][:1]
    
    #print(adv_data)
    #print(adv_data.columns)
    
    # Filter and merge tables, return final result
    adv_data = adv_data.drop(["Pos", "Age", "Tm", "G", "MP", "Unnamed: 19", "Unnamed: 24"], axis=1)
    final_data = pd.merge(base_data, adv_data, on='Season').fillna(0)[target_list]
    return final_data

if __name__ == "__main__":

    # Table formatting CSS
    hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """

    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

    # Title
    st.title('NBA Salary Prediction based on the 2021-22 Regular Season')

    # Header Image
    st.image('https://a.espncdn.com/photo/2021/0922/nba-rank_5-1_16x9.jpg', caption='Source: ESPN')

    # Introductory Blurb
    st.write("""

    This tool predicts an NBA Player's Salary (in USD) relative to the 2021-22 NBA season using their regular season
    statistics according to Basketball-Reference.com. Note that this model was trained on 2021-22 data, and while you
    can use the model to predict salaries from other seasons, the results may be erratic.

    """)

    # Load model from pickle file
    model = pickle.load(open("nbasalary_randomforrest1.sav", 'rb'))
    target_list = ['Age', 'G', 'GS', 'MP', 
        'FG', 'FGA', '3P', '3PA', '2P', '2PA', 
        'FT', 'FTA', 'DRB', 'TRB', 'AST', 'STL', 
        'BLK', 'TOV', 'PF', 'PTS', 'PER', 
        'AST%', 'USG%', 'OWS', 'DWS', 'WS',
        'OBPM', 'BPM', 'VORP'
    ] # Statistics used

    # Search bar for player
    search = st.text_input('Player Name', 'Brandon Ingram')

    # Results from player Search
    results_list = search_results(search)

    # Show list of players fetched from search
    player_options = st.selectbox('Player Results', results_list["Name"])

    # Input field for year
    # year = st.text_input("Enter Season (Ex: 2021-22, 1999-00): ", '2021-22')
    seasons = list(pd.read_html(results_list['Link'][results_list["Name"].index(player_options)], flavor="html5lib")[0]['Season'])
    year = st.selectbox('Select Season:', seasons[:seasons.index('Career')])

    try:
        # Data from basketball reference for the specified player and year
        bballref_data = get_player_data(results_list['Link'][results_list["Name"].index(player_options)], year)

        # Set up columns
        col1, col2 = st.columns([1,8])
        # Display Player Image
        try:
            col1.image(BeautifulSoup(requests.get(results_list['Link'][results_list["Name"].index(player_options)]).content, 'html.parser')
            .find_all('div', class_="media-item")[0].find('img')['src'])
        except:
            col1.write("no image")
        # Display Player Stats
        rounded = np.round(bballref_data, decimals= 2) # DataFrame to display
        col2.table(rounded)

        # Display prediction
        try:
            col2.write("The player's predicted salary in the 2021-22 NBA season is: " + str(round(model.predict(bballref_data).item())))
        except:
            col2.write("Please enter a valid year.")
    except:
        st.write("Error")

