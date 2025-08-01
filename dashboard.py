# app.py
import streamlit as st
import requests
import cloudscraper  # ### CAMBIO 1: Importamos la nueva librería ###
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px

# --- Configuración de la página de Streamlit ---
st.set_page_config(
    page_title="Dashboard de Tomás Páez",
    page_icon="🥊",
    layout="wide"
)

# La URL del perfil de tu bisabuelo en BoxRec
URL = "https://boxrec.com/en/box-pro/125969"

# --- Función de Scrapping (USANDO CLOUDSCRAPER) ---
def scrape_boxer_data(url):
    """
    Extrae la información de perfil y la tabla de combates de una URL de BoxRec,
    usando cloudscraper para evitar el bloqueo 403.
    """
    # ### CAMBIO 2: Creamos una instancia de cloudscraper ###
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )

    try:
        # ### CAMBIO 3: Usamos scraper.get() en lugar de requests.get() ###
        response = scraper.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener la página: {e}")
        return None, None
    except Exception as e:
        # Cloudscraper puede lanzar otros errores si no puede resolver el desafío
        st.error(f"Error de Cloudscraper: {e}")
        st.info("Esto puede ocurrir si BoxRec ha actualizado su sistema de seguridad. Intenta recargar la página en unos minutos.")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    # --- 1. Extraer información del perfil ---
    profile_data = {}
    name_tag = soup.find('h1')
    profile_data['name'] = name_tag.text.strip() if name_tag else "Nombre no encontrado"
    
    profile_table = soup.find('table', class_='profileTable')
    if profile_table:
        rows = profile_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].text.strip().lower().replace(':', '')
                value = cells[1].text.strip()
                profile_data[key] = value

    # --- 2. Extraer la tabla de combates ---
    fight_table = soup.find('table', class_='dataTable')
    if not fight_table:
        st.warning("No se encontró la tabla de combates. La estructura de la página puede haber cambiado.")
        return profile_data, None

    rows_data = []
    for row in fight_table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 8:
            opponent_cell = cols[2]
            opponent_name = opponent_cell.find('a').text.strip() if opponent_cell.find('a') else ''
            
            location_cell = cols[5]
            location = location_cell.text.strip()

            result_cell = cols[6]
            result_div = result_cell.find('div', class_='boutResult')
            result = result_div.text.strip() if result_div else ''

            row_dict = {
                'date': cols[0].text.strip().replace('\n', '').replace(' ', ''),
                'opponent': opponent_name,
                'opponent_w-l-d': cols[3].text.strip().replace('\n', ' ').replace(u'\xa0', ' '),
                'location': location,
                'result': result,
            }
            rows_data.append(row_dict)

    if not rows_data:
        st.warning("No se pudieron extraer datos de las filas de combates.")
        return profile_data, None

    df_fights = pd.DataFrame(rows_data)
    
    return profile_data, df_fights

# --- Función para cargar y cachear los datos ---
@st.cache_data(ttl=3600)
def load_data():
    profile, df_fights = scrape_boxer_data(URL)
    
    if df_fights is None or df_fights.empty:
        return profile, None

    # --- Limpieza y procesamiento de datos ---
    # Intenta convertir las fechas aproximadas ('May48', 'Jul47') a fechas reales
    # Creamos una fecha para el primer día del mes/año extraído
    df_fights['date_parsed'] = pd.to_datetime(df_fights['date'], format='%b%y', errors='coerce')
    
    df_fights['Resultado'] = df_fights['result'].map({'W': 'Victoria', 'L': 'Derrota', 'D': 'Empate'}).fillna('Otro')
    df_fights = df_fights.dropna(subset=['date_parsed'])
    df_fights['Año'] = df_fights['date_parsed'].dt.year
    df_fights['Año'] = df_fights['Año'].astype(int)

    return profile, df_fights


# --- Inicia la construcción de la App ---
profile_data, df_fights = load_data()

if not profile_data:
    st.error("Fallo crítico: No se pudo cargar la información del perfil del boxeador.")
else:
    st.title(f"🥊 Dashboard del Boxeador: {profile_data.get('name', 'N/A')}")
    st.markdown(f"Un análisis de la carrera profesional de **{profile_data.get('name', 'N/A')}**, extraído de [BoxRec]({URL}).")
    st.divider()

    st.header("Resumen del Perfil")
    try:
        wins = int(profile_data.get('wins', '0'))
        losses = int(profile_data.get('losses', '0'))
        draws = int(profile_data.get('draws', '0'))
        bouts = int(profile_data.get('bouts', '0')) if 'bouts' in profile_data else (wins + losses + draws)
        kos = int(profile_data.get('kos', '0')) if 'kos' in profile_data else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Combates", bouts)
        if bouts > 0:
            col2.metric("Victorias", wins, f"{round((wins/bouts)*100, 1)}%")
            col3.metric("Derrotas", losses, f"-{round((losses/bouts)*100, 1)}%")
        if wins > 0 and kos > 0:
            col4.metric("Victorias por KO", kos, f"{round((kos/wins)*100, 1)}% de las victorias")

    except (ValueError, ZeroDivisionError):
        st.warning("No se pudieron calcular todas las métricas del perfil.")

    # ... el resto del código del dashboard sigue igual ...
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
                outcome_counts, 
                values=outcome_counts.values, 
                names=outcome_counts.index, 
                title="Resumen de Victorias, Derrotas y Empates",
                color_discrete_map={'Victoria': '#2ca02c', 'Derrota': '#d62728', 'Empate': '#ff7f0e', 'Otro': '#7f7f7f'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with viz2:
            st.subheader("Actividad por Año")
            fights_per_year = df_fights['Año'].value_counts().sort_index()
            fig_bar = px.bar(
                fights_per_year,
                x=fights_per_year.index,
                y=fights_per_year.values,
                title="Número de Combates por Año",
                labels={'x': 'Año', 'y': 'Número de Combates'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        st.header("Registro Completo de Combates")
        st.markdown("Puedes ordenar la tabla haciendo clic en las cabeceras de las columnas.")
        
        display_df = df_fights[['date_parsed', 'opponent', 'Resultado', 'location']]
        display_df.columns = ['Fecha', 'Oponente', 'Resultado', 'Lugar']
        display_df['Fecha'] = display_df['Fecha'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(display_df.sort_values(by='Fecha', ascending=False), use_container_width=True, height=500)
    else:
        st.warning("No se pudo cargar o procesar la tabla de combates. La estructura de BoxRec puede haber cambiado o el scraper fue bloqueado.")
