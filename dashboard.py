# app.py
import streamlit as st
import requests
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import re

# --- Configuración de la página de Streamlit ---
st.set_page_config(
    page_title="Dashboard de Tomás Páez",
    page_icon="🥊",
    layout="wide"
)

URL = "https://boxrec.com/en/box-pro/125969"

# --- Función de Scrapping (Versión Final y Robusta) ---
@st.cache_data(ttl=3600) # Cache por 1 hora
def scrape_boxer_data(url):
    """
    Extrae información de perfil y la tabla de combates usando cloudscraper
    y un análisis preciso de la estructura HTML proporcionada.
    """
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )

    try:
        response = scraper.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión al obtener la página: {e}")
        return None, None
    except Exception as e:
        st.error(f"Error de Cloudscraper: {e}")
        st.info("El scraper fue bloqueado por la seguridad de la web. Esto a veces es temporal. Intenta recargar la página en unos minutos.")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    # --- 1. Extraer información del perfil ---
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

    # --- 2. Extraer la tabla de combates (Análisis Preciso) ---
    fight_table = soup.find('table', class_='dataTable')
    if not fight_table:
        return profile_data, None

    fights_data = []
    # Iteramos sobre cada <tbody>, ya que cada uno contiene un combate
    for tbody in fight_table.find_all('tbody'):
        # Buscamos la fila (tr) dentro del tbody
        row = tbody.find('tr')
        if not row:
            continue

        # Nos aseguramos de que no sea una fila de publicidad o vacía
        if 'midAdvert' in row.get('class', []):
            continue

        cols = row.find_all('td')
        
        # Una fila de combate válida tiene al menos 9 celdas
        if len(cols) >= 9:
            # Limpiamos la fecha de espacios y saltos de línea
            date_str = re.sub(r'\s+', ' ', cols[0].text).strip()
            
            # Limpiamos el nombre del oponente
            opponent_tag = cols[2].find('a', class_='personLink')
            opponent_name = re.sub(r'\s+', ' ', opponent_tag.get_text(separator=' ')).strip() if opponent_tag else 'N/A'
            
            # Obtenemos el record W-L-D
            wld_text = re.sub(r'\s+', ' ', cols[3].text).strip()
            
            # Obtenemos la localización
            location_text = re.sub(r'\s+', ' ', cols[5].text).strip()
            
            # Obtenemos el resultado
            result_div = cols[6].find('div', class_='boutResult')
            result = result_div.text.strip() if result_div else 'N/A'
            
            fights_data.append({
                'date_str': date_str,
                'opponent': opponent_name,
                'opponent_w-l-d': wld_text,
                'location': location_text,
                'result': result
            })

    if not fights_data:
        return profile_data, None

    df_fights = pd.DataFrame(fights_data)

    # --- 3. Limpieza y Procesamiento de Datos del DataFrame ---
    # Convertir fechas aproximadas ('May 48') a fechas reales ('1948-05-01')
    try:
        # Añadimos un día '01' para que pandas pueda interpretarlo como fecha
        df_fights['date'] = pd.to_datetime('01 ' + df_fights['date_str'], format='%d %b %y', errors='coerce')
    except Exception:
        # Si falla el formato anterior, intentamos sin el día
        df_fights['date'] = pd.to_datetime(df_fights['date_str'], format='%b %y', errors='coerce')

    df_fights = df_fights.dropna(subset=['date']) # Eliminar filas donde la fecha no se pudo parsear
    df_fights['Resultado'] = df_fights['result'].map({'W': 'Victoria', 'L': 'Derrota', 'D': 'Empate'}).fillna('Otro')
    df_fights['Año'] = df_fights['date'].dt.year
    df_fights['Año'] = df_fights['Año'].astype(int)
    
    return profile_data, df_fights

# --- Inicia la construcción de la App ---
profile_data, df_fights = scrape_boxer_data(URL)

if not profile_data:
    st.error("Fallo crítico: Eliii scraper fue bloqueado o no pudo encontrar los datos del perfil.")
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
        st.markdown("Puedes ordenar la tabla y filtrar los datos. Los datos se muestran del más reciente al más antiguo.")
        
        display_df = df_fights[['date', 'opponent', 'opponent_w-l-d', 'Resultado', 'location']]
        display_df.columns = ['Fecha', 'Oponente', 'Récord Oponente', 'Resultado', 'Lugar']
        display_df['Fecha'] = display_df['Fecha'].dt.strftime('%d-%m-%Y')
        
        st.dataframe(display_df.sort_values(by='Fecha', ascending=False), use_container_width=True, height=500)
    else:
        st.warning("No se pudo cargar o procesar la tabla de combates. Esto puede deberse a que no hay combates registrados o a un cambio en la estructura de la web.")
