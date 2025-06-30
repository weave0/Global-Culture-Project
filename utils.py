import re
import json
import pandas as pd

def is_culture_title(line, known_cultures):
    """
    Returns True if line is likely a culture title by regex or known culture match.
    """
    clean = line.strip().upper()
    regex_match = bool(re.match(r'^[A-Z][A-Z\s\-]{2,}$', clean)) and len(clean) > 3
    known_match = clean in known_cultures
    return regex_match or known_match

def segment_cultures(text, known_cultures):
    """
    Segments a text block into culture sections using is_culture_title.
    Returns a list of dicts with 'title' and 'content'.
    """
    lines = text.splitlines()
    segments = []
    current_title = None
    current_content = []
    overview = []
    found_first_culture = False
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if is_culture_title(line, known_cultures):
            title_lines = [line.strip()]
            while idx + 1 < len(lines) and is_culture_title(lines[idx + 1], known_cultures):
                idx += 1
                title_lines.append(lines[idx].strip())
            title = ' '.join(title_lines)
            if not found_first_culture and current_content:
                overview = current_content
                current_content = []
                found_first_culture = True
            if current_title:
                segments.append({'title': current_title, 'content': '\n'.join(current_content)})
            current_title = title
            current_content = []
            found_first_culture = True
        else:
            current_content.append(line)
        idx += 1
    if current_title:
        segments.append({'title': current_title, 'content': '\n'.join(current_content)})
    elif current_content:
        if segments:
            segments[-1]['content'] += '\n' + '\n'.join(current_content)
        else:
            overview = current_content
    if overview:
        segments.insert(0, {'title': 'Overview', 'content': '\n'.join(overview)})
    return segments

def truncate_for_gpt(text, enc=None, max_tokens=1600):
    """
    Truncates text to a max token count using encoder if provided, else by char length.
    """
    if enc:
        tokens = enc.encode(text)
        return enc.decode(tokens[:max_tokens])
    return text[:6000]

def load_known_cultures(filepath):
    """
    Loads a set of known culture names (uppercased) from a file.
    """
    with open(filepath, encoding='utf-8') as f:
        return set(line.strip().upper() for line in f if line.strip())

def load_enrichment_rules(filepath='enrichment_rules.json'):
    """
    Loads enrichment rules from a JSON file.
    """
    with open(filepath, encoding='utf-8') as f:
        return json.load(f)

def load_content(input_path):
    """
    Loads text content from .txt, .xlsx/.xls, or .docx file.
    """
    ext = input_path.split('.')[-1].lower()
    if ext == "txt":
        with open(input_path, encoding='utf-8') as f:
            return f.read()
    elif ext in ["xlsx", "xls"]:
        df = pd.read_excel(input_path)
        return "\n".join(str(row['Content']).strip() for _, row in df.iterrows() if pd.notnull(row['Content']))
    elif ext == "docx":
        import docx
        doc = docx.Document(input_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError(f"Unsupported file type: {ext}")

__all__ = [
    "is_culture_title",
    "segment_cultures",
    "truncate_for_gpt",
    "load_known_cultures",
    "load_enrichment_rules",
    "load_content"
]
