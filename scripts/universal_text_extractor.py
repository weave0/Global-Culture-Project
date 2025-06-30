import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from docx import Document
import fitz  # PyMuPDF

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def extract_all_text(base_folder):
    records = []
    for root, _, files in os.walk(base_folder):
        for file in files:
            ext = Path(file).suffix.lower()
            file_path = os.path.join(root, file)
            try:
                if ext == '.docx':
                    content = extract_text_from_docx(file_path)
                    ftype = 'DOCX'
                elif ext == '.txt':
                    content = extract_text_from_txt(file_path)
                    ftype = 'TXT'
                elif ext == '.pdf':
                    content = extract_text_from_pdf(file_path)
                    ftype = 'PDF'
                else:
                    continue

                if content.strip():
                    records.append({
                        "File Path": file_path,
                        "File Name": file,
                        "File Type": ftype,
                        "Content Type": "Text",
                        "Content": content.strip(),
                        "Extracted At": datetime.now().isoformat()
                    })

            except Exception as e:
                print(f"❌ Error reading {file_path}: {e}")

    return pd.DataFrame(records)

if __name__ == "__main__":
    folder_to_scan = r"d:\Global Culture Project"
    output_path = r"d:\Global Culture Project\All_Text_Extraction.xlsx"

    df = extract_all_text(folder_to_scan)
    df.to_excel(output_path, index=False)
    print(f"✅ Extraction complete. Output saved to:\n{output_path}")
