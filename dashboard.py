# app.py
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import re
import time
import os

# --- Configuración de la página de Streamlit ---
st.set_page_config(
    page_title="Dashboard de Tomás Páez",
    page_icon="🥊",
    layout="wide"
)

URL = "https://boxrec.com/en/box-pro/125969"

# --- Función de Scrapping con SELENIUM (La solución definitiva) ---
@st.cache_data(ttl=3600) # Cacheamos el resultado por 1 hora para no ejecutar Selenium constantemente
def scrape_boxer_data_with_selenium(url):
    """
    Usa Selenium para controlar un navegador Chrome real y obtener el HTML
    de la página, evitando así los bloqueos anti-scraping.
    """
    st.info("Iniciando el scraper con Selenium... Esto puede tardar unos segundos la primera vez.")
    
    # --- Configuración de Selenium para Streamlit Cloud ---
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1920x1080")

    # Inicializa el driver de Chrome
    # Esto funcionará tanto en local como en Streamlit Cloud gracias a la configuración
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        st.error(f"Error al inicializar el driver de Selenium: {e}")
        st.error("Asegúrate de que el archivo 'packages.txt' existe y contiene 'google-chrome-stable' y 'chromedriver'.")
        return None, None

    try:
        driver.get(url)
        # Espera crucial para que todo el JavaScript se cargue
        time.sleep(5) 
        
        # Obtenemos el HTML renderizado
        html = driver.page_source
        
    except Exception as e:
        st.error(f"Error durante la navegación con Selenium: {e}")
        driver.quit()
        return None, None
    finally:
        # Asegurarnos de cerrar el navegador siempre
        driver.quit()

    st.success("Scraper ha obtenido los datos con éxito. Procesando...")

    soup = BeautifulSoup(html, 'html.parser')

    # --- 1. Extraer información del perfil (sin cambios) ---
    profile_data = {}
    name_tag = soup.find('h1')
    profile_data['name'] = name_tag.text.strip() if name_tag else "Nombre no encontrado"
    
    profile_table = soup.find('table', class_='profileTable')
    if profile_table:
        for row in profile_table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].text.strip().lower().replace(':', '')
                value = cells[1].text.strip()
                profile_data[key] = value

    # --- 2. Extraer la tabla de combates (sin cambios en la lógica de parseo) ---
    fight_table = soup.find('table', class_='dataTable')
    if not fight_table:
        return profile_data, None

    fights_data = []
    for tbody in fight_table.find_all('tbody'):
        row = tbody.find('tr')
        if not row or 'SR' in row.get('class', []): continue
        
        cols = row.find_all('td')
        if len(cols) >= 9:
            date_str = re.sub(r'\s+', ' ', cols[0].text).strip()
            opponent_tag = cols[2].find('a', class_='personLink')
            opponent_name = re.sub(r'\s+', ' ', opponent_tag.get_text(separator=' ')).strip() if opponent_tag else 'N/A'
            wld_text = re.sub(r'\s+', ' ', cols[3].text).strip()
            location_text = re.sub(r'\s+', ' ', cols[5].text).strip()
            result_div = cols[6].find('div', class_='boutResult')
            result = result_div.text.strip() if result_div else 'N/A'
            
            fights_data.append({
                'date_str': date_str, 'opponent': opponent_name,
                'opponent_w-l-d': wld_text, 'location': location_text, 'result': result
            })

    if not fights_data:
        return profile_data, None

    df_fights = pd.DataFrame(fights_data)

    # --- 3. Limpieza de datos (sin cambios) ---
    df_fights['date'] = pd.to_datetime('01 ' + df_fights['date_str'], format='%d %b %y', errors='coerce')
    df_fights.dropna(subset=['date'], inplace=True)
    df_fights['Resultado'] = df_fights['result'].map({'W': 'Victoria', 'L': 'Derrota', 'D': 'Empate'}).fillna('Otro')
    df_fights['Año'] = df_fights['date'].dt.year.astype(int)
    
    return profile_data, df_fights

# --- Inicia la construcción de la App ---
profile_data, df_fights = scrape_boxer_data_with_selenium(URL)

if not profile_data:
    st.error("Fallo crítico: El scraper fue bloqueado o no pudo encontrar los datos del perfil. Por favor, revisa los logs.")
else:
    # El resto del código del dashboard es el mismo
    st.title(f"🥊 Dashboard del Boxeador: {profile_data.get('name', 'N/A')}")
    st.markdown(f"Un análisis de la carrera profesional de **{profile_data.get('name', 'N/A')}**, extraído de [BoxRec]({URL}).")
    st.divider()

    st.header("Resumen del Perfil")
    try:
        wins = int(profile_data.get('wins', '0'))
        losses = int(profile_data.get('losses', '0'))
        draws = int(profile_data.get('draws', '0'))
        bouts = int(profile_data.get('bouts', '0', wins + losses + draws))
        kos = int(profile_data.get('kos', '0'))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Combates", bouts)
        if bouts > 0:
            col2.metric("Victorias", wins, f"{round((wins/bouts)*100, 1)}%")
            col3.metric("Derrotas", losses, f"-{round((losses/bouts)*100, 1)}%")
        if wins > 0 and kos > 0:
            col4.metric("Victorias por KO", kos, f"{round((kos/wins)*100, 1)}% de las victorias")

    except (ValueError, ZeroDivisionError):
        st.warning("No se pudieron calcular todas las métricas del perfil.")

    st.subheader("Datos Biográficos")
    bio_col1, bio_col2 = st.columns(2)
    with bio_col1:
        st.write(f"**Alias:** {profile_data.get('alias', 'N/A')}")
        st.write(f"**Nacionalidad:** {profile_data.get('nationality', 'N/A')}")
        st.write(f"**Postura:** {profile_data.get('stance', 'N/A')}")
    with bio_col2:
        st.write(f"**Nacimiento:** {profile_data.get('born', 'N/A')}")
        st.write(f"**Carrera:** {profile_data.get('career', 'N/A')}")
        st.write(f"**Rounds totales:** {profile_data.get('rounds', 'N/A')}")
    
    st.divider()
    
    if df_fights is not None and not df_fights.empty:
        st.header("Análisis de la Carrera")
        viz1, viz2 = st.columns(2)
        
        with viz1:
            st.subheader("Distribución de Resultados")
            outcome_counts = df_fights['Resultado'].value_counts()
            fig_pie = px.pie(
                outcome_counts, values=outcome_counts.values, names=outcome_counts.index,
                title="Resumen de Victorias, Derrotas y Empates",
                color_discrete_map={'Victoria': '#2ca02c', 'Derrota': '#d62728', 'Empate': '#ff7f0e', 'Otro': '#7f7f7f'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with viz2:
            st.subheader("Actividad por Año")
            fights_per_year = df_fights['Año'].value_counts().sort_index()
            fig_bar = px.bar(
                fights_per_year, x=fights_per_year.index, y=fights_per_year.values,
                title="Número de Combates por Año", labels={'x': 'Año', 'y': 'Número de Combates'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        st.header("Registro Completo de Combates")
        display_df = df_fights[['date', 'opponent', 'opponent_w-l-d', 'Resultado', 'location']]
        display_df.columns = ['Fecha', 'Oponente', 'Récord Oponente', 'Resultado', 'Lugar']
        display_df['Fecha'] = display_df['Fecha'].dt.strftime('%d-%m-%Y')
        
        st.dataframe(display_df.sort_values(by='Fecha', ascending=False, key=lambda col: pd.to_datetime(col, format='%d-%m-%Y')), use_container_width=True, height=500)
    else:
        st.warning("No se pudo cargar o procesar la tabla de combates.")
