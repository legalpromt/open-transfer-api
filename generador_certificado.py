from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

def generar_reporte_pdf(datos):
    nombre_pdf = f"Informe_Audit_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # --- 1. CABECERA ---
    elements.append(Paragraph(f"AUDITORÍA PERICIAL FIFA (RSTP)", styles['Heading1']))
    elements.append(Paragraph(f"Ref: {datos['meta'].get('id_expediente')} | Fecha Emisión: {datos['acuerdo_transferencia'].get('fecha_transferencia')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # --- 2. DATOS DE LA TRANSFERENCIA (NUEVO) ---
    elements.append(Paragraph("1. DETALLES DE LA OPERACIÓN (TRANSFER DATA)", styles['Heading3']))
    
    acuerdo = datos.get('acuerdo_transferencia', {})
    jugador = datos.get('jugador', {})
    origen = acuerdo.get('club_origen', {}).get('nombre', 'N/A')
    destino = acuerdo.get('club_destino', {}).get('nombre', 'N/A')
    pais_dest = acuerdo.get('club_destino', {}).get('pais_asociacion', '-')
    cat_dest = acuerdo.get('club_destino', {}).get('categoria_fifa', '-')
    monto_fmt = f"{acuerdo.get('monto_fijo_total', 0):,.2f} {acuerdo.get('moneda', 'EUR')}"

    # Tabla de Datos Clave
    data_trans = [
        ["JUGADOR", jugador.get('nombre_completo', '').upper(), "NACIONALIDAD", jugador.get('nacionalidad', '')],
        ["VENDEDOR", origen, "FECHA NAC.", jugador.get('fecha_nacimiento', '')],
        ["COMPRADOR", f"{destino} ({pais_dest})", "CATEGORÍA", f"Cat. {cat_dest}"],
        ["FECHA TRANSF.", acuerdo.get('fecha_transferencia', ''), "MONTO FIJO", monto_fmt]
    ]
    
    t_trans = Table(data_trans, colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
    t_trans.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#e0e0e0")), # Gris columnas impares
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#e0e0e0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t_trans)
    elements.append(Spacer(1, 0.5*cm))

    # --- 3. PASAPORTE DEPORTIVO ---
    elements.append(Paragraph("2. PASAPORTE DEPORTIVO (HISTORIAL)", styles['Heading3']))
    data_pass = [["Periodo", "Club (Cat)", "País", "Estatus"]]
    
    for reg in datos.get('historial_formacion', []):
        cat_club = reg.get('categoria', '-')
        data_pass.append([
            f"{reg['inicio']} / {reg['fin']}", 
            f"{reg['club']} (Cat. {cat_club})", 
            reg.get('pais', '-'), 
            reg.get('estatus','Pro')
        ])
    
    t_pass = Table(data_pass, colWidths=[6*cm, 7*cm, 2*cm, 2*cm])
    t_pass.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1a237e")), # Azul oscuro
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
    ]))
    elements.append(t_pass)
    elements.append(Spacer(1, 1*cm))

    # --- 4. LIQUIDACIÓN (RESULTADOS) ---
    elements.append(Paragraph("3. LIQUIDACIÓN FINAL (AUDIT RESULTS)", styles['Heading3']))
    elements.append(Paragraph("Desglose automático de Solidaridad y Formación.", styles['Normal']))
    elements.append(Spacer(1, 0.2*cm))

    calculos = datos.get('calculos_auditoria', {})
    tabla_reparto = calculos.get('tabla_reparto', [])
    total_repartir = calculos.get('total_auditado', 0)
    
    # Encabezados
    data_alloc = [["Concepto", "Beneficiario", "Edad", "Monto", "Estado / Nota"]]
    
    for row in tabla_reparto:
        monto_num = row['monto']
        monto_txt = f"{monto_num:,.2f} {acuerdo.get('moneda', 'EUR')}"
        estilo_texto = colors.black
        
        # Si el monto es 0 (No Aplica), lo ponemos en gris claro
        if monto_num == 0:
            estilo_texto = colors.grey
            monto_txt = "(0.00)"
            
        data_alloc.append([
            row['estatus'], # Concepto (Solidaridad/Formacion)
            row['club'],
            row['edad_ref'],
            monto_txt,
            row['nota']
        ])

    # Fila de TOTALES
    data_alloc.append(["TOTAL EXIGIBLE", "", "", f"{total_repartir:,.2f}", "A PAGAR"])

    t_alloc = Table(data_alloc, colWidths=[3.5*cm, 5*cm, 2*cm, 3*cm, 3.5*cm])
    t_alloc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.black),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (3,1), (3,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        # Color condicional para el texto (se aplica fila por fila en lógica avanzada, aquí simplificamos)
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#ffeb3b")), # Total Amarillo
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))
    elements.append(t_alloc)

    # Nota legal al pie
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("NOTA: Los montos marcados como (0.00) indican que el concepto fue calculado pero no es exigible según normativa vigente (ej. Edad > 23 años para Formación).", styles['Italic']))

    doc.build(elements)
    return nombre_pdf