def load_known_cultures(filepath):
    with open(filepath, encoding='utf-8') as f:
        return set(line.strip().upper() for line in f if line.strip())
KNOWN_CULTURES = load_known_cultures('known_cultures.txt')