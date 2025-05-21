import os
from .pdf_extractor import extract_text_from_pdf
from .docx_extractor import extract_text_from_docx
from .txt_extractor import extract_text_from_txt

def extract_text(filepath):
    """
    Extracts text from a file based on its extension.

    Args:
        filepath (str): The path to the file.

    Returns:
        str: The extracted text, or None if the file type is not supported or an error occurs.
    """
    _, extension = os.path.splitext(filepath)
    extension = extension.lower()

    if extension == '.pdf':
        return extract_text_from_pdf(filepath)
    elif extension == '.docx':
        return extract_text_from_docx(filepath)
    elif extension == '.txt':
        return extract_text_from_txt(filepath)
    else:
        print(f"Unsupported file type: {extension}")
        return None

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Extract text from PDF, DOCX, or TXT files.")
    parser.add_argument("filepath", help="Path to the file to extract text from.")
    args = parser.parse_args()

    extracted_text = extract_text(args.filepath)

    if extracted_text:
        print("\n--- Extracted Text ---")
        print(extracted_text)
    else:
        print("No text could be extracted.")
