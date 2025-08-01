# app.py
import streamlit as st
import requests
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

# --- Función de Scrapping (MÁS ROBUSTA) ---
def scrape_boxer_data(url):
    """
    Extrae la información de perfil y la tabla de combates de una URL de BoxRec,
    adaptado para la estructura HTML dinámica.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener la página: {e}")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    # --- 1. Extraer información del perfil (esto no ha cambiado) ---
    profile_data = {}
    name = soup.find('h1')
    profile_data['name'] = name.text.strip() if name else "Nombre no encontrado"
    profile_table = soup.find('table', class_='profileTable')
    if profile_table:
        rows = profile_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].text.strip().lower().replace(':', '')
                value = cells[1].text.strip()
                profile_data[key] = value

    # --- 2. Extraer la tabla de combates (LÓGICA MEJORADA) ---
    # Buscamos la tabla por su clase 'dataTable', que es más estable que el ID.
    fight_table = soup.find('table', class_='dataTable')
    if not fight_table:
        st.warning("No se encontró la tabla de combates con la clase 'dataTable'.")
        return profile_data, None

    # Extraer cabeceras (headers)
    headers = []
    # Usamos .find() para obtener solo la primera fila de cabeceras
    header_row = fight_table.find('thead').find('tr')
    if header_row:
        headers = [th.text.strip() for th in header_row.find_all('th')]
        # Limpiamos las cabeceras, eliminando las que no tienen texto
        headers = [h for h in headers if h] 
        # Añadimos nombres para las columnas que no tienen cabecera de texto
        if len(headers) == 6: # Estructura esperada
            headers.insert(1, 'opponent_name')
            headers.insert(2, 'opponent_record')
            headers.insert(4, 'location')
            headers.insert(6, 'details')

    # Extraer filas de la tabla
    rows_data = []
    # Iteramos sobre todas las filas 'tr' de la tabla, sin importar en qué 'tbody' estén
    for row in fight_table.find_all('tr'):
        # Las filas de datos válidas tienen más de 5 celdas 'td'
        cols = row.find_all('td')
        if len(cols) > 5:  # Esto filtra las filas de cabecera y las filas de notas especiales
            # Extraer el oponente de la celda correcta
            opponent_cell = cols[2]
            opponent_name = opponent_cell.find('a').text.strip() if opponent_cell.find('a') else ''
            
            # Extraer la localización de la celda correcta
            location_cell = cols[5]
            location = location_cell.text.strip()

            # Extraer el resultado de la celda correcta
            result_cell = cols[6]
            result = result_cell.find('div', class_='boutResult').text.strip() if result_cell.find('div', class_='boutResult') else ''
            
            # Construir la fila con los datos importantes
            row_dict = {
                'date': cols[0].text.strip(),
                'opponent': opponent_name,
                'opponent_w-l-d': cols[3].text.strip().replace('\n', ' '),
                'location': location,
                'result': result,
                'rounds': cols[7].text.strip(),
            }
            rows_data.append(row_dict)

    if not rows_data:
        st.warning("No se pudieron extraer datos de las filas de combates.")
        return profile_data, None

    # Crear un DataFrame de Pandas
    df_fights = pd.DataFrame(rows_data)
    
    return profile_data, df_fights

# --- Función para cargar y cachear los datos ---
@st.cache_data(ttl=3600) # Cache por 1 hora para no sobrecargar el servidor de BoxRec
def load_data():
    profile, df_fights = scrape_boxer_data(URL)
    
    if df_fights is None or df_fights.empty:
        return profile, None

    # --- Limpieza y procesamiento de datos ---
    df_fights['date_parsed'] = pd.to_datetime(df_fights['date'], format='%b %y', errors='coerce')
    df_fights['Resultado'] = df_fights['result'].map({'W': 'Victoria', 'L': 'Derrota', 'D': 'Empate'}).fillna('Otro')
    df_fights['Año'] = df_fights['date_parsed'].dt.year
    df_fights = df_fights.dropna(subset=['Año']) # Eliminar filas donde no se pudo parsear la fecha
    df_fights['Año'] = df_fights['Año'].astype(int)

    return profile, df_fights


# --- Inicia la construcción de la App ---
profile_data, df_fights = load_data()

if not profile_data:
    st.error("Fallo crítico: No se pudo cargar la información del perfil del boxeador.")
else:
    # --- Título y Cabecera ---
    st.title(f"🥊 Dashboard del Boxeador: {profile_data.get('name', 'N/A')}")
    st.markdown(f"Un análisis de la carrera profesional de **{profile_data.get('name', 'N/A')}**, extraído de [BoxRec]({URL}).")
    st.divider()

    # --- Resumen del Perfil y Métricas Clave ---
    st.header("Resumen del Perfil")

    try:
        wins = int(profile_data.get('wins', '0'))
        losses = int(profile_data.get('losses', '0'))
        draws = int(profile_data.get('draws', '0'))
        bouts = int(profile_data.get('bouts', '0')) if 'bouts' in profile_data else (wins + losses + draws)
        kos = int(profile_data.get('kos', '0'))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Combates", bouts)
        if bouts > 0:
            col2.metric("Victorias", wins, f"{round((wins/bouts)*100, 1)}%")
            col3.metric("Derrotas", losses, f"-{round((losses/bouts)*100, 1)}%")
        if wins > 0:
             col4.metric("Victorias por KO", kos, f"{round((kos/wins)*100, 1)}% de las victorias")

    except (ValueError, ZeroDivisionError) as e:
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
        # --- Visualizaciones ---
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

        # --- Tabla de Datos Interactiva ---
        st.header("Registro Completo de Combates")
        st.markdown("Puedes ordenar la tabla haciendo clic en las cabeceras de las columnas.")
        
        display_df = df_fights[['date', 'opponent', 'Resultado', 'location', 'rounds']]
        display_df.columns = ['Fecha (Aprox)', 'Oponente', 'Resultado', 'Lugar', 'Rounds']
        
        st.dataframe(display_df, use_container_width=True, height=500)
    else:
        st.warning("No se pudo cargar o procesar la tabla de combates. La estructura de BoxRec puede haber cambiado.")
