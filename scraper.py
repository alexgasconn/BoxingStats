# scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd

# La URL del perfil de tu bisabuelo en BoxRec
URL = "https://boxrec.com/en/box-pro/125969"

def scrape_boxer_data(url):
    """
    Extrae la información de perfil y la tabla de combates de una URL de BoxRec.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza un error si la solicitud falla
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la página: {e}")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    # --- 1. Extraer información del perfil ---
    profile_data = {}
    
    # El nombre está en la etiqueta <h1>
    name = soup.find('h1')
    profile_data['name'] = name.text.strip() if name else "Nombre no encontrado"
    
    # El resto de los datos está en tablas dentro de 'profileTable'
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
    fight_table = soup.find('table', id='ratingsDataTable')
    if not fight_table:
        print("No se encontró la tabla de combates.")
        return profile_data, None

    # Extraer cabeceras de la tabla
    headers = [header.text.strip() for header in fight_table.find('thead').find_all('th')]
    
    # Extraer filas de la tabla
    rows_data = []
    for row in fight_table.find('tbody').find_all('tr'):
        cols = [ele.text.strip() for ele in row.find_all('td')]
        rows_data.append(cols)

    # Crear un DataFrame de Pandas
    df_fights = pd.DataFrame(rows_data, columns=headers)
    
    return profile_data, df_fights

if __name__ == '__main__':
    # Esto es para probar el scraper por sí solo
    profile, fights = scrape_boxer_data(URL)
    if profile:
        print("--- Perfil ---")
        print(profile)
    if fights is not None:
        print("\n--- Primeros 5 Combates ---")
        print(fights.head())
