import sys
import os
import src.utils.parse_input as pi

INPUT_DIR = "input"
keepGoing = True

# Currently, this is only showing a demo of parsing and fetching metadata.

if __name__ == "__main__":
    if not os.path.isdir(INPUT_DIR):
        print(f"Error: input folder '{INPUT_DIR}' not found.")
        sys.exit(1)

    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f))]

    if not files:
        print(f"No files found inside '{INPUT_DIR}'")
        sys.exit(1)

    print("Available input files:")
    for idx, fname in enumerate(files, start=1):
        print(f"  {idx}. {fname}")
    while keepGoing:
        try:
            choice = int(input("Select an input file by number (0 to exit): "))

            if choice == 0:
                print("Exiting.")
                break

            if 1 <= choice <= len(files):
                input_file = os.path.join(INPUT_DIR, files[choice - 1])
                print(f"\nUsing input file: {input_file}\n")

                try:
                    pi.demo(input_file)
                    keepGoing = False
                except Exception as e:
                    print(f"Error running demo: {e}")
                    keepGoing = False
            else:
                print("Invalid selection. Please enter a number from the list.")

        except ValueError:
            print("Invalid input. Please enter a number.")
