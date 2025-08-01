import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

# Configuración de la página
st.set_page_config(
    page_title="🥊 BoxRec Stats Dashboard",
    page_icon="🥊",
    layout="wide"
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
    .metric-container {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .fight-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

class SimpleBoxRecScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_boxer_page(self, url):
        """Scraper simplificado para BoxRec"""
        try:
            time.sleep(1)  # Ser respetuoso con el servidor
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer información básica del boxeador
            boxer_info = self.extract_boxer_info(soup)
            
            # Buscar la tabla de carrera
            career_data = self.extract_career_table(soup)
            
            return boxer_info, career_data
            
        except Exception as e:
            st.error(f"Error scraping: {str(e)}")
            return None, None
    
    def extract_boxer_info(self, soup):
        """Extrae información básica del boxeador"""
        info = {}
        
        try:
            # Buscar el nombre
            name_elem = soup.find('h1')
            if name_elem:
                info['name'] = name_elem.get_text(strip=True)
            
            # Buscar el récord
            record_pattern = re.compile(r'\d+-\d+-\d+')
            record_elem = soup.find(text=record_pattern)
            if record_elem:
                info['record'] = record_elem.strip()
            
            return info
            
        except Exception as e:
            st.warning(f"Error extrayendo info del boxeador: {e}")
            return {}
    
    def extract_career_table(self, soup):
        """Extrae datos de la tabla de carrera"""
        try:
            # Buscar diferentes posibles selectores para la tabla
            table_selectors = [
                'table.overflowScroll.careerTable',
                'table.careerTable',
                'table#careerTable',
                'div.careerTable table',
                'table[class*="career"]'
            ]
            
            career_table = None
            for selector in table_selectors:
                career_table = soup.select_one(selector)
                if career_table:
                    break
            
            if not career_table:
                # Buscar cualquier tabla grande
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 5:  # Asumimos que la tabla de carrera tiene más de 5 filas
                        career_table = table
                        break
            
            if not career_table:
                return []
            
            # Extraer filas de la tabla
            rows = career_table.find_all('tr')
            
            # Obtener headers
            header_row = rows[0] if rows else None
            headers = []
            
            if header_row:
                for cell in header_row.find_all(['th', 'td']):
                    headers.append(cell.get_text(strip=True))
            
            # Si no hay headers claros, usar genéricos
            if not headers or len(headers) < 3:
                headers = ['Date', 'Opponent', 'Result', 'Rounds', 'Location', 'Notes']
            
            # Extraer datos
            fights_data = []
            for row in rows[1:]:  # Saltar header
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    fight = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            fight[headers[i]] = cell.get_text(strip=True)
                    
                    if any(fight.values()):  # Solo añadir si tiene datos
                        fights_data.append(fight)
            
            return fights_data
            
        except Exception as e:
            st.warning(f"Error extrayendo tabla: {e}")
            return []

def calculate_stats(fights_data):
    """Calcula estadísticas de los datos de peleas"""
    if not fights_data:
        return {}
    
    stats = {
        'total_fights': len(fights_data),
        'wins': 0,
        'losses': 0,
        'draws': 0,
        'kos': 0,
        'decisions': 0
    }
    
    for fight in fights_data:
        result = fight.get('Result', '').upper()
        
        if 'W' in result:
            stats['wins'] += 1
        elif 'L' in result:
            stats['losses'] += 1
        elif 'D' in result:
            stats['draws'] += 1
        
        if 'KO' in result or 'TKO' in result:
            stats['kos'] += 1
        elif any(decision in result for decision in ['UD', 'SD', 'MD', 'PTS']):
            stats['decisions'] += 1
    
    # Calcular porcentajes
    if stats['total_fights'] > 0:
        stats['win_percentage'] = (stats['wins'] / stats['total_fights']) * 100
    else:
        stats['win_percentage'] = 0
    
    if stats['wins'] > 0:
        stats['ko_percentage'] = (stats['kos'] / stats['wins']) * 100
    else:
        stats['ko_percentage'] = 0
    
    return stats

def create_results_chart(stats):
    """Crear gráfico de resultados"""
    labels = ['Victorias', 'Derrotas', 'Empates']
    values = [stats.get('wins', 0), stats.get('losses', 0), stats.get('draws', 0)]
    colors = ['#4CAF50', '#F44336', '#FF9800']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo='label+percent+value'
    )])
    
    fig.update_layout(title="Distribución de Resultados")
    return fig

def main():
    st.markdown("<h1 class='main-header'>🥊 BoxRec Stats Dashboard</h1>", unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("⚙️ Configuración")
    
    # URL input
    default_url = "https://boxrec.com/en/box-pro/125969"
    url = st.sidebar.text_input("URL de BoxRec:", value=default_url)
    
    # Botón para scrapear
    if st.sidebar.button("🔍 Scrapear Datos"):
        if url:
            scraper = SimpleBoxRecScraper()
            
            with st.spinner("Scrapeando datos de BoxRec..."):
                boxer_info, fights_data = scraper.scrape_boxer_page(url)
            
            if boxer_info and fights_data:
                # Guardar en session state
                st.session_state['boxer_info'] = boxer_info
                st.session_state['fights_data'] = fights_data
                st.success("¡Datos scrapeados exitosamente!")
            else:
                st.error("No se pudieron obtener los datos. Revisa la URL.")
    
    # Mostrar datos si están disponibles
    if 'boxer_info' in st.session_state and 'fights_data' in st.session_state:
        boxer_info = st.session_state['boxer_info']
        fights_data = st.session_state['fights_data']
        
        # Información del boxeador
        st.header("📋 Información del Boxeador")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Nombre:** {boxer_info.get('name', 'No disponible')}")
        with col2:
            st.info(f"**Récord:** {boxer_info.get('record', 'No disponible')}")
        
        # Calcular estadísticas
        stats = calculate_stats(fights_data)
        
        # Mostrar métricas
        st.header("📊 Estadísticas")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Peleas", stats.get('total_fights', 0))
        with col2:
            st.metric("Victorias", stats.get('wins', 0))
        with col3:
            st.metric("Derrotas", stats.get('losses', 0))
        with col4:
            st.metric("% Victoria", f"{stats.get('win_percentage', 0):.1f}%")
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("KOs", stats.get('kos', 0))
        with col6:
            st.metric("% KO", f"{stats.get('ko_percentage', 0):.1f}%")
        with col7:
            st.metric("Decisiones", stats.get('decisions', 0))
        with col8:
            st.metric("Empates", stats.get('draws', 0))
        
        # Gráfico
        if stats.get('total_fights', 0) > 0:
            st.header("📈 Visualización")
            fig = create_results_chart(stats)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de peleas
        st.header("🥊 Historial de Peleas")
        if fights_data:
            df = pd.DataFrame(fights_data)
            st.dataframe(df, use_container_width=True)
            
            # Descargar CSV
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV",
                csv,
                f"boxeo_stats_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        else:
            st.info("No hay datos de peleas para mostrar.")
    
    else:
        st.info("👆 Introduce la URL de BoxRec en el sidebar y haz clic en 'Scrapear Datos'")
        
        # Opción de subir CSV
        st.header("📁 O sube un archivo CSV")
        uploaded_file = st.file_uploader("Sube datos de peleas en CSV", type="csv")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.success("Archivo cargado exitosamente!")
                st.dataframe(df.head())
                
                # Convertir a formato de fights_data
                fights_data = df.to_dict('records')
                stats = calculate_stats(fights_data)
                
                # Mostrar estadísticas básicas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Peleas", stats.get('total_fights', 0))
                with col2:
                    st.metric("Victorias", stats.get('wins', 0))
                with col3:
                    st.metric("% Victoria", f"{stats.get('win_percentage', 0):.1f}%")
                
            except Exception as e:
                st.error(f"Error procesando archivo: {e}")

if __name__ == "__main__":
    main()
