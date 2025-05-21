import re

def chunk_text_by_paragraph(text: str) -> list[str]:
    """
    Splits a long text into chunks by paragraphs.
    A paragraph is considered text separated by one or more new lines.
    Multiple blank lines are handled to avoid empty chunks.

    Args:
        text (str): The long text to be chunked.

    Returns:
        list[str]: A list of strings, where each string is a paragraph.
    """
    if not text:
        return []

    # Split by one or more newlines
    paragraphs = re.split(r'\n\s*\n+', text)

    # Filter out any empty strings or strings consisting only of whitespace
    # that might result from multiple newlines or leading/trailing whitespace.
    # Also, strip whitespace from each paragraph.
    cleaned_paragraphs = [p.strip() for p in paragraphs if p and not p.isspace()]
    
    return cleaned_paragraphs

if __name__ == '__main__':
    sample_text_empty = ""
    sample_text_single_paragraph = "Este es un solo párrafo."
    sample_text_multiple_paragraphs = """Este es el primer párrafo.

Este es el segundo párrafo.
Tiene dos líneas.

Este es el tercer párrafo.


Este es el cuarto párrafo, separado por múltiples líneas en blanco.
"""
    sample_text_leading_trailing_newlines = "\n\nEste párrafo tiene espacios antes y después.\n\n   \n\n"

    print("--- Prueba con texto vacío ---")
    chunks = chunk_text_by_paragraph(sample_text_empty)
    print(f"Número de fragmentos: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Fragmento {i}: '{chunk}'")

    print("\n--- Prueba con un solo párrafo ---")
    chunks = chunk_text_by_paragraph(sample_text_single_paragraph)
    print(f"Número de fragmentos: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Fragmento {i}: '{chunk}'")

    print("\n--- Prueba con múltiples párrafos ---")
    chunks = chunk_text_by_paragraph(sample_text_multiple_paragraphs)
    print(f"Número de fragmentos: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Fragmento {i}: '{chunk}'")
        
    print("\n--- Prueba con saltos de línea al inicio/final y párrafos vacíos ---")
    chunks = chunk_text_by_paragraph(sample_text_leading_trailing_newlines)
    print(f"Número de fragmentos: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Fragmento {i}: '{chunk}'")

    sample_text_with_only_whitespace_paragraphs = "Párrafo 1\n\n   \n\nPárrafo 2"
    print("\n--- Prueba con párrafos que solo contienen espacios en blanco ---")
    chunks = chunk_text_by_paragraph(sample_text_with_only_whitespace_paragraphs)
    print(f"Número de fragmentos: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"Fragmento {i}: '{chunk}'")
