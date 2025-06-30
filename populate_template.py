def main():
    # Read the content of the batch file
    try:
        with open("d:\\Global Culture Project\\Global Culture Alignment\\Global_Culture_Profiles_Batch_1.txt", 'r', encoding='utf-8') as f:
            batch_content = f.read()
            print("File read successfully.")
            print(batch_content[:500])  # Print the first 500 characters for verification
    except FileNotFoundError:
        print("Error: Global_Culture_Profiles_Batch_1.txt not found.")
        return

if __name__ == "__main__":
    main()
