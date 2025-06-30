import re
import openpyxl

def parse_profile_text(text_content):
    profiles = text_content.strip().split('\n\n---\n\n')
    parsed_data = []

    for profile_text in profiles:
        profile = {}
        matches = re.findall(r'\*\*(.*?):\*\*\s*(.*?)(?=\n\n\*\*|\Z)', profile_text, re.DOTALL)

        for key, value in matches:
            key = key.strip()
            value = value.strip()
            value = re.sub(r'^- ', '', value, flags=re.MULTILINE)
            value = re.sub(r'\n\s*\n', '\n', value)
            value = value.replace('\n', '\\n')
            profile[key] = value
        parsed_data.append(profile)
    return parsed_data

def main():
    template_headers = [
        "Country", "Region", "Languages", "Religion", "Key Norms", "Etiquette Notes",
        "Interpreter Notes", "Client Onboarding Notes", "Workplace Insights",
        "Historical Context", "Visual Symbols", "Image", "Point-to-Language Supported",
        "PGLS Language Match", "Communication Style", "Touch Norms", "Time Orientation",
        "Gender Role Dynamics"
    ]

    try:
        with open("d:\\Global Culture Project\\Global Culture Alignment\\Global_Culture_Profiles_Batch_1.txt", 'r', encoding='utf-8') as f:
            batch_content = f.read()
            print("File read successfully.")
    except FileNotFoundError:
        print("Error: Global_Culture_Profiles_Batch_1.txt not found.")
        return

    parsed_profiles = parse_profile_text(batch_content)
    print(f"Parsed {len(parsed_profiles)} profiles.")

    wb = openpyxl.load_workbook("d:\\Global Culture Project\\Global Culture Project CORE.xlsx")
    ws = wb.active

    for profile in parsed_profiles:
        row = []
        for header in template_headers:
            value = profile.get(header, "")
            row.append(value)
        ws.append(row)

    wb.save("d:\\Global Culture Project\\Global Culture Project CORE.xlsx")
    print("Data written to Excel file successfully.")

if __name__ == "__main__":
    main()
