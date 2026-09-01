import os
import glob

INPUT_FOLDER = "./calendars"
OUTPUT_FILE = "combined_calendar.ics"

def merge_ics_files():
    # Create input folder if it doesn't exist
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"Created '{INPUT_FOLDER}' directory. Add your .ics files there.")
        return

    combined_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Cloud Folder Merger//EN",
        "CALSCALE:GREGORIAN"
    ]
    
    # Search for all .ics files inside the folder
    ics_files = glob.glob(os.path.join(INPUT_FOLDER, "*.ics"))
    
    if not ics_files:
        print("No .ics files found to merge.")
        # Write an empty but valid calendar file so the URL doesn't break
        combined_content.append("END:VCALENDAR")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(combined_content))
        return

    # Extract event details from files
    for file_path in ics_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                in_event = False
                for line in f:
                    if line.strip() == "BEGIN:VEVENT":
                        in_event = True
                    if in_event:
                        combined_content.append(line.rstrip())
                    if line.strip() == "END:VEVENT":
                        in_event = False
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    combined_content.append("END:VCALENDAR")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(combined_content))
    
    print(f"Successfully compiled {len(ics_files)} calendars into {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_ics_files()
