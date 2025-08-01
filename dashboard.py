import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Function to scrape BoxRec data
def scrape_boxrec(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract boxer info
        boxer_info = {}
        info_table = soup.find("table", class_="personTable")
        if info_table:
            rows = info_table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) == 2:
                    key = cols[0].text.strip().lower()
                    value = cols[1].text.strip()
                    boxer_info[key] = value
        
        # Extract fight history
        fights = []
        fight_table = soup.find("table", class_="dataTable")
        if fight_table:
            rows = fight_table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 7:
                    fight = {
                        "date": cols[0].text.strip(),
                        "opponent": cols[1].text.strip(),
                        "opponent_record": cols[2].text.strip(),
                        "result": cols[3].text.strip(),
                        "type": cols[4].text.strip(),
                        "rounds": cols[5].text.strip(),
                        "location": cols[6].text.strip()
                    }
                    fights.append(fight)
        
        return boxer_info, fights
    except Exception as e:
        st.error(f"Error scraping BoxRec: {e}")
        return None, None

# Fallback: Use provided document data
def load_document_data():
    data = [
        {"date": "May 48", "opponent": "Jose Martinez Pascual", "opponent_record": "5 12 1", "result": "L"},
        {"date": "Jul 47", "opponent": "Rafael Ferro", "opponent_record": "7 2 1", "result": "L"},
        {"date": "Jan 47", "opponent": "Jose Martinez Pascual", "opponent_record": "4 6 1", "result": "W"},
        # Add all other bouts from the document here (abridged for brevity)
        {"date": "Apr 30", "opponent": "Modesto Munoz", "opponent_record": "1 6 4", "result": "W"}
    ]
    boxer_info = {
        "name": "Miguel Tarre",
        "division": "light",
        "status": "inactive",
        "bouts": "62",
        "rounds": "461",
        "kos": "23.08%",
        "career": "1930-1948",
        "debut": "1930-04-09",
        "nationality": "Spain",
        "residence": "Barcelona, Cataluña, Spain",
        "stance": "orthodox"
    }
    return boxer_info, data

# Process data into DataFrame
def process_data(boxer_info, fights):
    df = pd.DataFrame(fights)
    df["date"] = pd.to_datetime(df["date"], format="%b %y", errors="coerce")
    df["year"] = df["date"].dt.year
    df["result"] = df["result"].map({"W": "Win", "L": "Loss", "D": "Draw"})
    return boxer_info, df

# Streamlit Dashboard
def main():
    st.set_page_config(page_title="Miguel Tarre Boxing Dashboard", layout="wide")
    st.title("Miguel Tarre: Boxing Legend Dashboard")

    # Load data (try scraping, fallback to document)
    url = "https://boxrec.com/en/box-pro/125969"
    boxer_info, fights = scrape_boxrec(url)
    if not fights:
        st.warning("Using provided document data due to scraping issues.")
        boxer_info, fights = load_document_data()

    boxer_info, df = process_data(boxer_info, fights)

    # Sidebar with boxer info
    with st.sidebar:
        st.header("Boxer Profile")
        st.image("https://via.placeholder.com/150", caption="Miguel Tarre")  # Replace with actual image if available
        st.write(f"**Name**: {boxer_info['name']}")
        st.write(f"**Nationality**: {boxer_info['nationality']}")
        st.write(f"**Residence**: {boxer_info['residence']}")
        st.write(f"**Division**: {boxer_info['division']}")
        st.write(f"**Stance**: {boxer_info['stance']}")
        st.write(f"**Career**: {boxer_info['career']}")
        st.write(f"**Total Bouts**: {boxer_info['bouts']}")
        st.write(f"**Rounds**: {boxer_info['rounds']}")
        st.write(f"**KO %**: {boxer_info['kos']}")

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fight Outcomes")
        outcome_counts = df["result"].value_counts()
        fig_pie = px.pie(
            names=outcome_counts.index,
            values=outcome_counts.values,
            title="Win/Loss/Draw Distribution",
            color_discrete_sequence=["#00CC96", "#EF553B", "#636EFA"]
        )
        st.plotly_chart(fig_pie)

    with col2:
        st.subheader("Fights Over Time")
        yearly_fights = df.groupby("year").size().reset_index(name="fights")
        fig_line = px.line(
            yearly_fights,
            x="year",
            y="fights",
            title="Number of Fights per Year",
            markers=True
        )
        st.plotly_chart(fig_line)

    st.subheader("Fight History")
    st.dataframe(
        df[["date", "opponent", "opponent_record", "result"]].sort_values("date", ascending=False),
        use_container_width=True
    )

    st.subheader("Career Highlights")
    wins = df[df["result"] == "Win"].shape[0]
    losses = df[df["result"] == "Loss"].shape[0]
    draws = df[df["result"] == "Draw"].shape[0]
    st.metric("Total Wins", wins)
    st.metric("Total Losses", losses)
    st.metric("Total Draws", draws)

if __name__ == "__main__":
    main()
