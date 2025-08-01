import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from boxrec_scraper import BoxRecScraper  # Importa el scraper

# Configuración de la página
st.set_page_config(
    page_title="Estadísticas de Boxeo - Bisabuelo",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .metric-card {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(url):
    """Carga los datos del boxeador usando el scraper"""
    try:
        scraper = BoxRecScraper()
        career_df, boxer_info = scraper.scrape_boxer_career(url), scraper.get_boxer_info(url)
        return career_df, boxer_info
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None, {}

def calculate_stats(df):
    """Calcula estadísticas del boxeador"""
    if df is None or df.empty:
        return {}
    
    stats = {}
    
    # Estadísticas básicas
    stats['total_fights'] = len(df)
    
    if 'Win' in df.columns:
        stats['wins'] = df['Win'].sum()
        stats['losses'] = df['Loss'].sum() if 'Loss' in df.columns else 0
        stats['draws'] = df['Draw'].sum() if 'Draw' in df.columns else 0
        stats['win_percentage'] = (stats['wins'] / stats['total_fights'] * 100) if stats['total_fights'] > 0 else 0
    
    if 'KO' in df.columns:
        stats['kos'] = df['KO'].sum()
        stats['ko_percentage'] = (stats['kos'] / stats['wins'] * 100) if stats['wins'] > 0 else 0
    
    # Duración de carrera
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        valid_dates = df['Date'].dropna()
        if not valid_dates.empty:
            stats['career_start'] = valid_dates.min()
            stats['career_end'] = valid_dates.max()
            stats['career_length'] = (stats['career_end'] - stats['career_start']).days / 365.25
    
    return stats

def create_fight_timeline(df):
    """Crea un timeline de las peleas"""
    if df is None or df.empty or 'Date' not in df.columns:
        return None
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df_valid = df.dropna(subset=['Date']).copy()
    
    if df_valid.empty:
        return None
    
    # Añadir colores basados en resultados
    colors = []
    for _, row in df_valid.iterrows():
        if 'Win' in row and row['Win']:
            colors.append('green')
        elif 'Loss' in row and row['Loss']:
            colors.append('red')
        else:
            colors.append('blue')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_valid['Date'],
        y=range(len(df_valid)),
        mode='markers+lines',
        marker=dict(
            color=colors,
            size=10,
            line=dict(color='black', width=1)
        ),
        text=df_valid['Opponent'] if 'Opponent' in df_valid.columns else '',
        hovertemplate='<b>%{text}</b><br>Fecha: %{x}<br>Pelea #%{y}<extra></extra>',
        name='Peleas'
    ))
    
    fig.update_layout(
        title="Timeline de la Carrera",
        xaxis_title="Fecha",
        yaxis_title="Número de Pelea",
        hovermode='closest',
        height=400
    )
    
    return fig

def create_results_pie_chart(stats):
    """Crea un gráfico de pastel con los resultados"""
    if not stats or 'wins' not in stats:
        return None
    
    labels = ['Victorias', 'Derrotas', 'Empates']
    values = [stats.get('wins', 0), stats.get('losses', 0), stats.get('draws', 0)]
    colors = ['#4CAF50', '#F44336', '#FF9800']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>%{value} peleas<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title="Distribución de Resultados",
        height=400
    )
    
    return fig

def main():
    st.markdown("<h1 class='main-header'>🥊 Estadísticas de Boxeo del Bisabuelo</h1>", unsafe_allow_html=True)
    
    # Sidebar para configuración
    st.sidebar.header("⚙️ Configuración")
    
    # URL del boxeador
    default_url = "https://boxrec.com/en/box-pro/125969"
    boxer_url = st.sidebar.text_input("URL del BoxRec:", value=default_url)
    
    if st.sidebar.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
    
    # Cargar datos
    if boxer_url:
        with st.spinner("Cargando datos del boxeador..."):
            career_df, boxer_info = load_data(boxer_url)
        
        if career_df is not None and not career_df.empty:
            # Calcular estadísticas
            stats = calculate_stats(career_df)
            
            # Información del boxeador
            st.header("📋 Información del Boxeador")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Nombre:** {boxer_info.get('name', 'No disponible')}")
            with col2:
                st.info(f"**Récord:** {boxer_info.get('record', 'No disponible')}")
            
            # Métricas principales
            st.header("📊 Estadísticas Principales")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Peleas", stats.get('total_fights', 0))
            with col2:
                st.metric("Victorias", stats.get('wins', 0))
            with col3:
                st.metric("Derrotas", stats.get('losses', 0))
            with col4:
                st.metric("% de Victoria", f"{stats.get('win_percentage', 0):.1f}%")
            
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                st.metric("KOs", stats.get('kos', 0))
            with col6:
                st.metric("% KO", f"{stats.get('ko_percentage', 0):.1f}%")
            with col7:
                if 'career_length' in stats:
                    st.metric("Años Activo", f"{stats['career_length']:.1f}")
            with col8:
                st.metric("Empates", stats.get('draws', 0))
            
            # Gráficos
            st.header("📈 Visualizaciones")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pastel
                pie_fig = create_results_pie_chart(stats)
                if pie_fig:
                    st.plotly_chart(pie_fig, use_container_width=True)
            
            with col2:
                # Timeline de peleas
                timeline_fig = create_fight_timeline(career_df)
                if timeline_fig:
                    st.plotly_chart(timeline_fig, use_container_width=True)
            
            # Tabla de datos
            st.header("📋 Historial de Peleas")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                show_all = st.checkbox("Mostrar todas las peleas", value=True)
            with col2:
                if 'Result' in career_df.columns:
                    result_filter = st.selectbox(
                        "Filtrar por resultado:",
                        ['Todos'] + list(career_df['Result'].unique())
                    )
                else:
                    result_filter = 'Todos'
            
            # Aplicar filtros
            filtered_df = career_df.copy()
            if result_filter != 'Todos' and 'Result' in career_df.columns:
                filtered_df = filtered_df[filtered_df['Result'] == result_filter]
            
            if not show_all:
                filtered_df = filtered_df.head(10)
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # Descargar datos
            st.header("💾 Descargar Datos")
            csv = career_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"carrera_boxeo_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        else:
            st.error("No se pudieron cargar los datos. Verifica la URL y que la página sea accesible.")
            
            # Opción para cargar archivo CSV manualmente
            st.header("📁 Cargar Datos Manualmente")
            uploaded_file = st.file_uploader("Sube un archivo CSV con los datos de las peleas", type="csv")
            
            if uploaded_file is not None:
                try:
                    career_df = pd.read_csv(uploaded_file)
                    st.success("Archivo cargado exitosamente!")
                    st.dataframe(career_df.head())
                    
                    # Procesar datos cargados manualmente
                    stats = calculate_stats(career_df)
                    
                    # Mostrar métricas básicas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Peleas", stats.get('total_fights', 0))
                    with col2:
                        st.metric("Victorias", stats.get('wins', 0))
                    with col3:
                        st.metric("% Victoria", f"{stats.get('win_percentage', 0):.1f}%")
                        
                except Exception as e:
                    st.error(f"Error procesando el archivo: {e}")
    
    # Información adicional en sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Información")
    st.sidebar.markdown("""
    Este dashboard muestra las estadísticas de boxeo extraídas de BoxRec.
    
    **Características:**
    - Timeline de peleas
    - Estadísticas de victoria/derrota
    - Análisis de KOs
    - Descarga de datos
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Hecho con ❤️ para preservar la historia familiar*")

if __name__ == "__main__":
    main()
