from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os

MAX_EXTRACTED_TEXT_LINES = 30

def generate_report_pdf(query_filename, extracted_text, relevant_documents, output_pdf_path):
    """
    Genera un informe en PDF con los resultados de la búsqueda.

    Args:
        query_filename (str): Nombre del archivo de consulta.
        extracted_text (str): Texto extraído del documento de consulta.
        relevant_documents (list): Lista de rutas de archivos de documentos relevantes.
        output_pdf_path (str): Ruta donde se guardará el PDF generado.
    """
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title = "Informe de Búsqueda de Referencias"
    story.append(Paragraph(title, styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Nombre del archivo de consulta
    story.append(Paragraph(f"<b>Documento de Consulta:</b> {query_filename}", styles['Normal']))
    story.append(Spacer(1, 0.1 * inch))

    # Texto extraído (primeras N líneas)
    story.append(Paragraph("<b>Extracto del Documento de Consulta (primeras líneas):</b>", styles['h3']))
    if extracted_text:
        lines = extracted_text.splitlines()
        text_to_show = "\n".join(lines[:MAX_EXTRACTED_TEXT_LINES])
        if len(lines) > MAX_EXTRACTED_TEXT_LINES:
            text_to_show += "\n..."
        
        # Usar un estilo que preserve los saltos de línea
        preformatted_style = styles['Code'] # 'Code' o 'Normal' con preWrap='CJK'
        # O crear uno nuevo si es necesario para mejor formato
        # preformatted_style = ParagraphStyle('Preformatted', parent=styles['Normal'], spaceBefore=6, leading=14, fontName='Courier')

        # Reemplazar múltiples espacios con uno para evitar desbordamientos si no es 'Code'
        # text_to_show_cleaned = re.sub(r'\s+', ' ', text_to_show) # Podría perder formato intencional
        
        # Dividir en párrafos para mejor manejo de saltos de línea por ReportLab
        for line_para in text_to_show.splitlines():
            story.append(Paragraph(line_para if line_para.strip() else "&nbsp;", preformatted_style)) # &nbsp; para líneas vacías
        # story.append(Preformatted(text_to_show, styles['Code'])) # Otra opción con Preformatted
    else:
        story.append(Paragraph("No se extrajo texto del documento de consulta o el texto estaba vacío.", styles['Italic']))
    story.append(Spacer(1, 0.2 * inch))

    # Documentos Relevantes
    story.append(Paragraph("Documentos Relevantes Encontrados:", styles['h3']))
    if relevant_documents:
        # Usar ListFlowable para una lista con viñetas
        list_items = []
        for doc_path in relevant_documents:
            list_items.append(ListItem(Paragraph(doc_path, styles['Normal'])))
        
        story.append(ListFlowable(list_items, bulletType='bullet', start='bulletchar'))
        # Alternativa sin ListFlowable, solo párrafos:
        # for doc_path in relevant_documents:
        #     story.append(Paragraph(f"- {doc_path}", styles['Normal']))
    else:
        story.append(Paragraph("No se encontraron documentos relevantes.", styles['Italic']))

    try:
        doc.build(story)
        print(f"INFO (PDF Generator): Informe PDF generado y guardado en '{output_pdf_path}'")
        return True
    except Exception as e:
        print(f"ERROR (PDF Generator): No se pudo generar el PDF. Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("--- Prueba de Generación de PDF ---")
    
    # Datos de muestra
    sample_query_filename = "mi_consulta_test.txt"
    sample_extracted_text = ("Esta es la primera línea del texto extraído.\n"
                             "Esta es la segunda línea, un poco más larga para ver cómo se ajusta.\n"
                             "Y una tercera línea.\n" * 15) # Hacerlo más largo para probar truncamiento
    sample_relevant_documents = [
        "/ruta/al/documento_relevante_1.pdf",
        "otro/directorio/documento_importante.docx",
        "../relativa/referencia.txt"
    ]
    output_dir = "test_pdf_reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    sample_output_pdf_path = os.path.join(output_dir, "informe_de_prueba.pdf")

    # Generar PDF con datos
    print(f"\nGenerando PDF con datos de muestra en '{sample_output_pdf_path}'...")
    success = generate_report_pdf(sample_query_filename, sample_extracted_text, sample_relevant_documents, sample_output_pdf_path)
    if success:
        print(f"PDF de prueba generado exitosamente. Por favor, revise '{sample_output_pdf_path}'.")
    else:
        print("Fallo al generar el PDF de prueba con datos.")

    # Generar PDF sin documentos relevantes
    sample_output_pdf_path_no_results = os.path.join(output_dir, "informe_sin_resultados.pdf")
    print(f"\nGenerando PDF sin resultados en '{sample_output_pdf_path_no_results}'...")
    success_no_results = generate_report_pdf(sample_query_filename, sample_extracted_text, [], sample_output_pdf_path_no_results)
    if success_no_results:
        print(f"PDF de prueba (sin resultados) generado. Revise '{sample_output_pdf_path_no_results}'.")
    else:
        print("Fallo al generar el PDF de prueba sin resultados.")

    # Generar PDF con texto extraído vacío
    sample_output_pdf_path_no_text = os.path.join(output_dir, "informe_sin_texto_extraido.pdf")
    print(f"\nGenerando PDF con texto extraído vacío en '{sample_output_pdf_path_no_text}'...")
    success_no_text = generate_report_pdf(sample_query_filename, "", sample_relevant_documents, sample_output_pdf_path_no_text)
    if success_no_text:
        print(f"PDF de prueba (sin texto extraído) generado. Revise '{sample_output_pdf_path_no_text}'.")
    else:
        print("Fallo al generar el PDF de prueba sin texto extraído.")

    print("\n--- Fin de la Prueba de Generación de PDF ---")

```
