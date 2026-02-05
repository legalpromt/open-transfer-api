import pandas as pd

# Datos Reales de Julián Álvarez (Con la nueva columna CATEGORÍA)
data = {
    "Club": [
        "CA Calchin",       # Club de Barrio
        "River Plate",      # Gigante Argentino
        "Manchester City"   # Gigante Europeo
    ],
    "Pais": [
        "ARG", 
        "ARG", 
        "ENG"
    ],
    "Categoria": [
        "IV",  # Importante: Era un club amateur/regional
        "I",   # River es Categoría 1 en CONMEBOL
        "I"    # City es Categoría 1 en UEFA
    ],
    "Inicio": [
        "2012-01-01", 
        "2016-01-01", 
        "2022-07-08"
    ],
    "Fin": [
        "2015-12-31", 
        "2022-07-07", 
        "2024-08-11"
    ],
    "Estatus": [
        "Amateur", 
        "Profesional", 
        "Profesional"
    ]
}

# Creamos el DataFrame
df = pd.DataFrame(data)

# Guardamos como Excel real (.xlsx) para que sea más profesional
nombre_archivo = "prueba_julian_expert.xlsx"
df.to_excel(nombre_archivo, index=False)

print(f"✅ Archivo '{nombre_archivo}' creado. ¡Listo para subir al Dashboard!")