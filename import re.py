import re
import logging

logging.basicConfig(
    filename='segmenter.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def is_culture_title(line):
    # Tune: Require at least 3 characters, all caps, allow spaces/dashes, not just numbers
    return bool(re.match(r'^[A-Z][A-Z\s\-]{2,}$', line.strip())) and len(line.strip()) > 3

def segment_cultures(text):
    lines = text.splitlines()
    segments = []
    current_title = None
    current_content = []
    overview = []
    found_first_culture = False

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        # Multi-line title detection: join consecutive ALL CAPS lines
        if is_culture_title(line):
            title_lines = [line.strip()]
            while idx + 1 < len(lines) and is_culture_title(lines[idx + 1]):
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

    # Handle last segment
    if current_title:
        segments.append({'title': current_title, 'content': '\n'.join(current_content)})
    elif current_content:
        # Orphaned text at end, assign to previous culture if exists
        if segments:
            logging.warning("Orphaned text found after last culture, appending to previous culture.")
            segments[-1]['content'] += '\n' + '\n'.join(current_content)
        else:
            overview = current_content

    # Assign overview if present
    if overview:
        segments.insert(0, {'title': 'Overview', 'content': '\n'.join(overview)})

    # Logging malformed docs
    if not segments:
        logging.warning("No culture segments found in document.")
    for seg in segments:
        if not seg['content'].strip():
            logging.warning(f"Empty content for segment: {seg['title']}")

    return segments

# Example usage:
if __name__ == "__main__":
    with open('Global_Culture_Profiles_Batch_1.txt', encoding='utf-8') as f:
        text = f.read()
    segments = segment_cultures(text)
    for seg in segments:
        print(f"== {seg['title']} ==\n{seg['content'][:200]}...\n")