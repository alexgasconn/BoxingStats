# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from scraper import scrape_boxer_data, URL  # Importamos desde nuestro archivo scraper

# --- Configuración de la página ---
st.set_page_config(
    page_title="Dashboard de Tomás Páez",
    page_icon="🥊",
    layout="wide"
)

# --- Función para cargar y cachear los datos ---
# Usamos @st.cache_data para que los datos se extraigan solo una vez y no en cada recarga.
@st.cache_data
def load_data():
    profile, df_fights = scrape_boxer_data(URL)
    
    if df_fights is None:
        return profile, None

    # --- Limpieza y procesamiento de datos ---
    
    # 1. Convertir la columna 'date' a formato de fecha
    df_fights['date'] = pd.to_datetime(df_fights['date'], errors='coerce')
    
    # 2. Limpiar y convertir columnas numéricas
    # La columna '#' a veces tiene valores no numéricos, los ignoramos
    df_fights['#'] = pd.to_numeric(df_fights['#'], errors='coerce')

    # 3. Crear una columna de 'Resultado' más clara
    # Mapeamos 'W', 'L', 'D' a textos más descriptivos
    result_map = {
        'W': 'Victoria',
        'L': 'Derrota',
        'D': 'Empate'
    }
    df_fights['Resultado'] = df_fights['result'].map(result_map).fillna('Otro')

    # 4. Extraer el año del combate para análisis
    df_fights['Año'] = df_fights['date'].dt.year

    return profile, df_fights


# --- Carga de datos ---
profile_data, df_fights = load_data()

if profile_data is None:
    st.error("No se pudo cargar la información del boxeador. Revisa la URL o tu conexión a internet.")
else:
    # --- Título y Cabecera ---
    st.title(f"🥊 Dashboard del Boxeador: {profile_data.get('name', 'N/A')}")
    st.markdown(f"Un análisis de la carrera profesional de **{profile_data.get('name', 'N/A')}**, extraído de [BoxRec]({URL}).")
    st.divider()

    # --- Resumen del Perfil y Métricas Clave ---
    st.header("Resumen del Perfil")

    # Extraemos las victorias, derrotas y KOs del perfil
    wins = int(profile_data.get('wins', '0'))
    losses = int(profile_data.get('losses', '0'))
    draws = int(profile_data.get('draws', '0'))
    kos = int(profile_data.get('KOs', '0'))
    bouts = int(profile_data.get('bouts', '0'))
    
    # Mostramos las métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Combates", bouts)
    col2.metric("Victorias", wins, f"{round((wins/bouts)*100, 1)}%")
    col3.metric("Derrotas", losses, f"-{round((losses/bouts)*100, 1)}%")
    col4.metric("Victorias por KO", kos, f"{round((kos/wins)*100, 1)}% de las victorias")

    # Mostramos otros datos del perfil
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
    
    if df_fights is not None:
        # --- Visualizaciones ---
        st.header("Análisis de la Carrera")
        
        viz1, viz2 = st.columns(2)
        
        with viz1:
            # Gráfico de Torta de Resultados
            st.subheader("Distribución de Resultados")
            outcome_counts = df_fights['Resultado'].value_counts()
            fig_pie = px.pie(
                values=outcome_counts.values, 
                names=outcome_counts.index, 
                title="Resumen de Victorias, Derrotas y Empates",
                color_discrete_map={'Victoria': 'green', 'Derrota': 'red', 'Empate': 'orange', 'Otro': 'grey'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with viz2:
            # Gráfico de Barras de Combates por Año
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
        
        # Seleccionamos y renombramos las columnas para que sean más claras
        display_df = df_fights[['date', 'opponent', 'Resultado', 'type', 'rounds', 'location']]
        display_df.columns = ['Fecha', 'Oponente', 'Resultado', 'Tipo', 'Rounds', 'Lugar']
        
        st.dataframe(display_df, use_container_width=True, height=500)
    else:
        st.warning("No se pudo cargar la tabla de combates.")
