def handle_duplicate_file(file_path):
    """Handle duplicate files by prompting user for action"""
    while True:
        print(f"⚠️ File already exists: {file_path}")
        print("What would you like to do?")
        print("1. Overwrite existing file")
        print("2. Save with auto-incremented suffix (e.g., filename_1.ext)")
        print("3. Cancel save operation")

        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == '1':
            # Overwrite
            return file_path
        elif choice == '2':
            # Auto-increment suffix
            base, ext = os.path.splitext(file_path)
            counter = 1
            new_path = f"{base}_{counter}{ext}"
            while os.path.exists(new_path):
                counter += 1
                new_path = f"{base}_{counter}{ext}"
            print(f"📝 Will save as: {new_path}")
            return new_path
        elif choice == '3':
            # Cancel
            return None
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")