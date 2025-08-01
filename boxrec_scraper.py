import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from datetime import datetime
import re

class BoxRecScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_boxer_career(self, boxer_url):
        """
        Scrapes the career table from a BoxRec boxer page
        """
        try:
            # Añadir delay para ser respetuoso con el servidor
            time.sleep(1)
            
            response = self.session.get(boxer_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar la tabla con class "overflowScroll careerTable"
            career_table = soup.find('table', class_='overflowScroll careerTable')
            
            if not career_table:
                # Buscar alternativas comunes
                career_table = soup.find('table', class_='careerTable')
                if not career_table:
                    career_table = soup.find('table', id='careerTable')
                    
            if not career_table:
                print("No se encontró la tabla de carrera")
                return None
                
            # Extraer headers
            headers = []
            header_row = career_table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
            
            # Si no hay headers explícitos, usar los típicos de BoxRec
            if not headers or len(headers) < 5:
                headers = ['Date', 'Opponent', 'Result', 'Rounds', 'Location', 'Notes']
            
            # Extraer datos de las filas
            fights_data = []
            rows = career_table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Asegurar que hay suficientes columnas
                    fight_data = {}
                    
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            text = cell.get_text(strip=True)
                            fight_data[headers[i]] = text
                    
                    # Solo añadir si tiene información relevante
                    if any(fight_data.values()):
                        fights_data.append(fight_data)
            
            # Crear DataFrame
            df = pd.DataFrame(fights_data)
            
            # Limpiar y procesar datos
            if not df.empty:
                df = self.clean_fight_data(df)
                
            return df
            
        except Exception as e:
            print(f"Error scraping boxer career: {e}")
            return None
    
    def clean_fight_data(self, df):
        """
        Limpia y procesa los datos de las peleas
        """
        try:
            # Limpiar columna de fecha si existe
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Procesar resultados
            if 'Result' in df.columns:
                df['Win'] = df['Result'].str.contains('W', case=False, na=False)
                df['Loss'] = df['Result'].str.contains('L', case=False, na=False)
                df['Draw'] = df['Result'].str.contains('D', case=False, na=False)
                df['KO'] = df['Result'].str.contains('KO|TKO', case=False, na=False)
                df['Decision'] = df['Result'].str.contains('UD|MD|SD|PTS', case=False, na=False)
            
            # Extraer información de rounds si existe
            if 'Rounds' in df.columns:
                df['Rounds_Numeric'] = df['Rounds'].str.extract(r'(\d+)').astype(float)
            
            # Limpiar nombres de oponentes
            if 'Opponent' in df.columns:
                df['Opponent'] = df['Opponent'].str.replace(r'\s+', ' ', regex=True).str.strip()
            
            return df
            
        except Exception as e:
            print(f"Error cleaning data: {e}")
            return df
    
    def get_boxer_info(self, boxer_url):
        """
        Extrae información básica del boxeador
        """
        try:
            response = self.session.get(boxer_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            info = {}
            
            # Extraer nombre
            name_elem = soup.find('h1')
            if name_elem:
                info['name'] = name_elem.get_text(strip=True)
            
            # Extraer récord básico (W-L-D)
            record_elem = soup.find(text=re.compile(r'\d+-\d+-\d+'))
            if record_elem:
                info['record'] = record_elem.strip()
            
            return info
            
        except Exception as e:
            print(f"Error getting boxer info: {e}")
            return {}

# Ejemplo de uso
def main():
    scraper = BoxRecScraper()
    
    # URL del boxeador (reemplaza con la URL real)
    boxer_url = "https://boxrec.com/en/box-pro/125969"
    
    print("Obteniendo información básica del boxeador...")
    boxer_info = scraper.get_boxer_info(boxer_url)
    print(f"Información: {boxer_info}")
    
    print("\nScraping tabla de carrera...")
    career_df = scraper.scrape_boxer_career(boxer_url)
    
    if career_df is not None and not career_df.empty:
        print(f"Se encontraron {len(career_df)} peleas")
        print("\nPrimeras 5 filas:")
        print(career_df.head())
        
        # Guardar en CSV
        filename = f"boxer_career_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        career_df.to_csv(filename, index=False)
        print(f"\nDatos guardados en: {filename}")
        
        return career_df, boxer_info
    else:
        print("No se pudieron obtener los datos de la carrera")
        return None, boxer_info

if __name__ == "__main__":
    main()
