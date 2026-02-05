import pandas as pd

# Historial EXACTO de Enzo Jeremías Fernández (2001)
data = {
    "Club": [
        "River Plate",      # Formación infantil (12 a 19 años)
        "Defensa y Justicia", # El préstamo clave (agosto 2020 - junio 2021)
        "River Plate",      # Vuelta a casa (Campeón)
        "Benfica"           # El trampolín europeo (6 meses)
    ],
    "Pais": [
        "ARG", 
        "ARG", 
        "ARG", 
        "PRT" # Portugal (Esto es clave: Club UEFA)
    ],
    "Categoria": [
        "I", # River es Top
        "I", # Defensa es Primera División
        "I", 
        "I"  # Benfica es Top Champions
    ],
    "Inicio": [
        "2013-01-17", # Cumpleaños 12 (Inicio periodo FIFA)
        "2020-08-22", # Cesión a Defensa
        "2021-07-01", # Regreso a River
        "2022-07-14"  # Fichaje por Benfica
    ],
    "Fin": [
        "2020-08-21", # Un día antes de irse a Defensa
        "2021-06-30", # Fin del préstamo
        "2022-07-13", # Venta a Benfica
        "2023-01-30"  # Venta al Chelsea (Día del Deadline Day)
    ],
    "Estatus": [
        "Amateur", # En River fue mezcla, pero simplificamos
        "Profesional",
        "Profesional",
        "Profesional"
    ]
}

df = pd.DataFrame(data)
df.to_excel("enzo_chelsea_audit.xlsx", index=False)

print("✅ Expediente 'enzo_chelsea_audit.xlsx' generado con éxito.")