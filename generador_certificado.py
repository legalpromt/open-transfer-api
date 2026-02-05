from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from datetime import datetime
import requests
from io import BytesIO

def generar_reporte_pdf(datos):
    nombre_pdf = f"Informe_V24_Oficial_{datos.get('meta', {}).get('id_expediente', 'TEMP')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    # --- CABECERA CON LOGO ---
    dest = datos.get('acuerdo_transferencia', {}).get('club_destino', {})
    logo_url = dest.get('logo')
    
    # Preparar imagen si existe
    logo_img = None
    if logo_url:
        try:
            response = requests.get(logo_url)
            img_data = BytesIO(response.content)
            # Dibujamos el logo (tamaño fijo 2.5cm)
            logo_img = Image(img_data, width=2.5*cm, height=2.5*cm)
        except:
            pass # Si falla, no ponemos logo

    # Texto cabecera
    titulo = Paragraph(f"AUDITORÍA PERICIAL FIFA (RSTP)", styles['Heading1'])
    subtitulo = Paragraph(f"Reporte Financiero Oficial | {datetime.now().strftime('%Y-%m-%d')}", styles['Normal'])
    
    # Tabla de Cabecera: [Logo | Títulos]
    if logo_img:
        data_header = [[logo_img, [titulo, subtitulo]]]
        t_header = Table(data_header, colWidths=[3*cm, 12*cm])
        t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t_header)
    else:
        elements.append(titulo)
        elements.append(subtitulo)
        
    elements.append(Spacer(1, 0.5*cm))

    # --- RESTO DEL INFORME (Igual que V23) ---
    acuerdo = datos.get('acuerdo_transferencia', {})
    jugador = datos.get('jugador', {})
    orig = acuerdo.get('club_origen', {}) or {"nombre": "Desconocido"}
    monto_bruto = acuerdo.get('monto_fijo_total', 0)
    
    data_trans = [
        ["JUGADOR", jugador.get('nombre_completo')],
        ["VENDEDOR", f"{orig.get('nombre')} ({orig.get('pais_asociacion', '-')})"],
        ["COMPRADOR", f"{dest.get('nombre')} ({dest.get('pais_asociacion', '-')})"],
        ["MONTO BRUTO", f"{monto_bruto:,.2f} EUR"]
    ]
    t_trans = Table(data_trans, colWidths=[5*cm, 9*cm])
    t_trans.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (0,-1), colors.lightgrey), ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold')]))
    elements.append(t_trans)
    elements.append(Spacer(1, 0.8*cm))

    calculos = datos.get('calculos_auditoria', {})
    lista_sol = calculos.get('lista_solidaridad', [])
    lista_form = calculos.get('lista_formacion', [])
    total_sol = calculos.get('total_solidaridad', 0)
    total_form = calculos.get('total_formacion', 0)

    # TABLA A
    elements.append(Paragraph("A. DESGLOSE SOLIDARIDAD (Retención 5%)", styles['Heading3']))
    if lista_sol:
        data_sol = [["Beneficiario", "Periodo", "%", "Monto Retenido"]]
        for r in lista_sol: data_sol.append([r['club'], r.get('periodo'), r.get('porcentaje'), f"{r['monto']:,.2f} €"])
        data_sol.append(["TOTAL A RETENER", "", "", f"{total_sol:,.2f} EUR"])
        t_sol = Table(data_sol, colWidths=[7*cm, 4*cm, 2*cm, 4*cm])
        t_sol.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1565C0")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_sol)
    else: elements.append(Paragraph("No aplica.", styles['Italic']))
    elements.append(Spacer(1, 0.5*cm))

    # TABLA B
    elements.append(Paragraph("B. DESGLOSE FORMACIÓN (Adicional)", styles['Heading3']))
    if lista_form:
        data_form = [["Beneficiario", "Cat/Edad", "Nota", "Monto Extra"]]
        for r in lista_form:
            m = f"{r['monto']:,.2f} €" if r['monto'] > 0 else "---"
            data_form.append([r['club'], r.get('cat_periodo'), r['nota'], m])
        data_form.append(["TOTAL FORMACIÓN", "", "", f"{total_form:,.2f} EUR"])
        t_form = Table(data_form, colWidths=[7*cm, 4*cm, 3*cm, 3*cm])
        t_form.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2E7D32")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t_form)
    else: elements.append(Paragraph("No aplica.", styles['Italic']))
    elements.append(Spacer(1, 1*cm))

    # LIQUIDACION FINAL
    elements.append(Paragraph("LIQUIDACIÓN FINAL (CLEARING STATEMENT)", styles['Heading2']))
    neto_vendedor = monto_bruto - total_sol
    coste_total = monto_bruto + total_form
    
    data_final = [
        ["CONCEPTO", "IMPACTO", "MONTO"],
        ["1. Monto Bruto Acordado", "Base", f"{monto_bruto:,.2f} EUR"],
        ["2. (-) Retención Solidaridad", "Resta al Vendedor", f"- {total_sol:,.2f} EUR"],
        ["3. (=) Neto Estimado al Vendedor", "Ingreso Vendedor", f"{neto_vendedor:,.2f} EUR"],
        ["4. (+) Indemnización Formación", "Suma al Comprador", f"+ {total_form:,.2f} EUR"],
        ["COSTE TOTAL PARA COMPRADOR", "SALIDA DE CAJA", f"{coste_total:,.2f} EUR"]
    ]
    t_final = Table(data_final, colWidths=[8*cm, 4*cm, 5*cm])
    t_final.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.black), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('ALIGN', (2,1), (2,-1), 'RIGHT'),
        ('BACKGROUND', (0,3), (-1,3), colors.lightgrey), ('FONTNAME', (0,3), (-1,3), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FFD700")), ('TEXTCOLOR', (0,-1), (-1,-1), colors.black),
        ('FONTSIZE', (0,-1), (-1,-1), 11), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')
    ]))
    elements.append(t_final)
    
    doc.build(elements)
    return nombre_pdf