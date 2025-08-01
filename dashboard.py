import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import plotly.express as px
import time
from datetime import datetime

# Function to scrape BoxRec data using Selenium
def scrape_boxrec(url):
    try:
        # Configure Selenium with headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load page
        driver.get(url)
        time.sleep(3)  # Wait for JavaScript to render
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

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

# Fallback: Complete document data
def load_document_data():
    data = [
        {"date": "May 48", "opponent": "Jose Martinez Pascual", "opponent_record": "5 12 1", "result": "L"},
        {"date": "Jul 47", "opponent": "Rafael Ferro", "opponent_record": "7 2 1", "result": "L"},
        {"date": "Jan 47", "opponent": "Jose Martinez Pascual", "opponent_record": "4 6 1", "result": "W"},
        {"date": "Aug 44", "opponent": "Juanito Beltran", "opponent_record": "12 0 1", "result": "L"},
        {"date": "Apr 44", "opponent": "Estanislao Llacer", "opponent_record": "19 11 3", "result": "L"},
        {"date": "Aug 43", "opponent": "Jose Garcia Alvarez", "opponent_record": "40 6 1", "result": "L"},
        {"date": "Jul 43", "opponent": "Beni Levy", "opponent_record": "16 0 0", "result": "L"},
        {"date": "Sep 42", "opponent": "Teodoro Gonzalez", "opponent_record": "21 4 4", "result": "L"},
        {"date": "Sep 42", "opponent": "Jose Garcia Alvarez", "opponent_record": "33 2 1", "result": "L"},
        {"date": "Aug 42", "opponent": "Jose Ferrer", "opponent_record": "25 2 3", "result": "D"},
        {"date": "Jul 42", "opponent": "Estanislao Llacer", "opponent_record": "8 7 3", "result": "W"},
        {"date": "Jun 42", "opponent": "Manuel Meseguer", "opponent_record": "13 16 5", "result": "W"},
        {"date": "Apr 42", "opponent": "Joaquin Nicolas", "opponent_record": "8 1 0", "result": "W"},
        {"date": "Feb 42", "opponent": "Ramon Mir", "opponent_record": "25 40 14", "result": "W"},
        {"date": "Feb 41", "opponent": "Pedro Llorente", "opponent_record": "13 2 4", "result": "L"},
        {"date": "Sep 40", "opponent": "Pedro Ros", "opponent_record": "44 9 4", "result": "L"},
        {"date": "Aug 40", "opponent": "Justo Gascon", "opponent_record": "15 1 0", "result": "L"},
        {"date": "Jul 40", "opponent": "Antonio Pradas", "opponent_record": "19 3 2", "result": "W"},
        {"date": "May 40", "opponent": "Antonio Zuniga", "opponent_record": "7 2 0", "result": "W"},
        {"date": "May 40", "opponent": "Antonio Zuniga", "opponent_record": "6 2 0", "result": "L"},
        {"date": "Mar 40", "opponent": "Luigi De Bellis", "opponent_record": "2 4 3", "result": "W"},
        {"date": "Feb 40", "opponent": "Jose Ferrer", "opponent_record": "6 0 1", "result": "W"},
        {"date": "Nov 39", "opponent": "Antonio Pradas", "opponent_record": "19 2 0", "result": "W"},
        {"date": "May 37", "opponent": "Antonio Pradas", "opponent_record": "17 2 0", "result": "L"},
        {"date": "Apr 37", "opponent": "Cristobal Martinez Valera", "opponent_record": "10 13 0", "result": "W"},
        {"date": "Mar 37", "opponent": "Francisco Mestres", "opponent_record": "28 13 3", "result": "W"},
        {"date": "Jan 37", "opponent": "Antonio Pradas", "opponent_record": "16 1 0", "result": "W"},
        {"date": "Dec 36", "opponent": "Hilario Martinez", "opponent_record": "72 47 9", "result": "W"},
        {"date": "Sep 36", "opponent": "Cesareo Betes", "opponent_record": "23 8 5", "result": "D"},
        {"date": "Mar 36", "opponent": "Hilario Martinez", "opponent_record": "72 43 9", "result": "W"},
        {"date": "Jan 36", "opponent": "Ramon Mir", "opponent_record": "24 30 10", "result": "W"},
        {"date": "Dec 35", "opponent": "Johnny Diaz", "opponent_record": "6 10 6", "result": "W"},
        {"date": "Oct 35", "opponent": "Ricardo Bosch", "opponent_record": "16 13 6", "result": "W"},
        {"date": "Aug 35", "opponent": "Maurice Naudin", "opponent_record": "11 9 0", "result": "W"},
        {"date": "Jun 35", "opponent": "Charles Pernot", "opponent_record": "18 2 8", "result": "D"},
        {"date": "May 35", "opponent": "Jack Contray", "opponent_record": "61 28 16", "result": "W"},
        {"date": "Apr 35", "opponent": "Ricardo Bosch", "opponent_record": "15 10 6", "result": "W"},
        {"date": "Feb 35", "opponent": "Pedro Isasti", "opponent_record": "24 24 8", "result": "W"},
        {"date": "Dec 34", "opponent": "Julian Martinez", "opponent_record": "17 28 12", "result": "W"},
        {"date": "Nov 34", "opponent": "Jack Contray", "opponent_record": "61 27 14", "result": "D"},
        {"date": "Oct 34", "opponent": "Felix Perez", "opponent_record": "19 14 5", "result": "W"},
        {"date": "Sep 34", "opponent": "Sixto de Diego", "opponent_record": "8 0 2", "result": "W"},
        {"date": "Aug 34", "opponent": "Cesareo Betes", "opponent_record": "19 6 4", "result": "W"},
        {"date": "Aug 34", "opponent": "Johnny Diaz", "opponent_record": "1 5 4", "result": "W"},
        {"date": "May 34", "opponent": "Saturnino Tiberio", "opponent_record": "35 21 7", "result": "D"},
        {"date": "Mar 34", "opponent": "Pedro Isasti", "opponent_record": "20 20 7", "result": "W"},
        {"date": "Jan 34", "opponent": "Vicente Fabregat", "opponent_record": "2 4 3", "result": "W"},
        {"date": "Oct 33", "opponent": "Luis Bru", "opponent_record": "44 43 18", "result": "W"},
        {"date": "May 33", "opponent": "Joaquin Torregrosa", "opponent_record": "9 3 5", "result": "L"},
        {"date": "May 33", "opponent": "Juan Llanguas", "opponent_record": "16 11 5", "result": "W"},
        {"date": "Apr 33", "opponent": "Valentin Miro", "opponent_record": "6 8 6", "result": "W"},
        {"date": "Oct 32", "opponent": "Primitivo Sanchez", "opponent_record": "16 10 2", "result": "W"},
        {"date": "Jul 32", "opponent": "Jose Uceda", "opponent_record": "22 10 1", "result": "W"},
        {"date": "Oct 31", "opponent": "Paco Melian", "opponent_record": "1 1 0", "result": "W"},
        {"date": "Sep 31", "opponent": "Jack Contray", "opponent_record": "37 21 11", "result": "W"},
        {"date": "Aug 31", "opponent": "Salvador Farreras", "opponent_record": "9 13 9", "result": "W"},
        {"date": "Apr 31", "opponent": "Isidro Perez", "opponent_record": "22 8 7", "result": "L"},
        {"date": "Mar 31", "opponent": "Marcus", "opponent_record": "debut", "result": "D"},
        {"date": "Feb 31", "opponent": "Jose Altes", "opponent_record": "7 7 0", "result": "W"},
        {"date": "Dec 30", "opponent": "Cesareo Betes", "opponent_record": "6 3 2", "result": "D"},
        {"date": "Sep 30", "opponent": "Juan Antonio Molina", "opponent_record": "14 9 9", "result": "L"},
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
    # Convert date to datetime, handling two-digit years
    df["date"] = pd.to_datetime(df["date"], format="%b %y", errors="coerce")
    df["year"] = df["date"].dt.year
    # Adjust years before 1970 (e.g., '48' -> 1948)
    df["year"] = df["year"].apply(lambda x: x - 100 if x > 2000 else x)
    df["date"] = df.apply(lambda row: row["date"].replace(year=row["year"]), axis=1)
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

    # Boxer Profile in Main Dashboard
    st.header("Boxer Profile")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://via.placeholder.com/150", caption="Miguel Tarre")  # Replace with actual image if available
    with col2:
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
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Fight Outcomes")
        outcome_counts = df["result"].value_counts()
        fig_pie = px.pie(
            names=outcome_counts.index,
            values=outcome_counts.values,
            title="Win/Loss/Draw Distribution",
            color_discrete_sequence=["#00CC96", "#EF553B", "#636EFA"]
        )
        st.plotly_chart(fig_pie)

    with col4:
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
