import cloudscraper
from bs4 import BeautifulSoup

def obtener_datos_besoccer(url):
    # Usamos cloudscraper igual por si acaso, es más seguro
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        datos = {}
        
        # --- LÓGICA PARA BESOCCER ---
        
        # 1. NOMBRE (Suele estar en un h1 con clase 'title')
        # Buscamos varias opciones por si cambia el diseño
        nombre_box = soup.find('h1', class_='title')
        if not nombre_box:
            nombre_box = soup.find('h1') # Intento genérico
            
        if nombre_box:
            # Limpiamos espacios y saltos de línea
            datos['nombre'] = nombre_box.text.strip().replace('\n', '')
        else:
            datos['nombre'] = "Desconocido"

        # 2. CLUB ACTUAL
        # En BeSoccer suele salir arriba junto al escudo
        # Buscamos el texto del equipo principal
        club_box = soup.find('a', class_='team-name')
        if not club_box:
            # Plan B: buscar en la ficha técnica
            club_box = soup.select_one('.main-logo-name')
            
        if club_box:
            datos['club'] = club_box.text.strip()
        else:
            datos['club'] = "Agente Libre / Desconocido"

        # 3. NACIONALIDAD
        # BeSoccer suele tener esto en la tabla de datos "Personal"
        datos['nacionalidad'] = "Desconocido"
        
        # Buscamos todas las filas de tablas
        filas = soup.find_all('tr')
        for fila in filas:
            texto_fila = fila.text.lower()
            if 'nacionalidad' in texto_fila or 'lugar de nacimiento' in texto_fila:
                # Intentamos sacar el dato de la columna derecha
                celdas = fila.find_all('td')
                if len(celdas) > 1:
                    datos['nacionalidad'] = celdas[1].text.strip()
                    break

        return datos

    except Exception as e:
        print(f"Error BeSoccer: {e}")
        return None