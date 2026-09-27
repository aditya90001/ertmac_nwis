import os
import re
import pandas as pd
import pdfplumber

PDF_DIR = r"C:\Users\DELL\OneDrive\Desktop\nwis\data\nm_ocd\pdfs"
OUTPUT_CSV = r"C:\Users\DELL\OneDrive\Desktop\nwis\data\extracted_well_events.csv"

processed_records = []

print("Starting WCR PDF Parsing & Entity Extraction Pipeline...")

if os.path.exists(PDF_DIR):
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    print(f"Total {len(pdf_files)} PDFs processing ke liye ready hain.\n")

    for idx, file_name in enumerate(pdf_files):
        pdf_path = os.path.join(PDF_DIR, file_name)
        print(f"[{idx+1}/{len(pdf_files)}] Parsing PDF: {file_name}...")

        try:
            full_text = ""
            tables = []

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Text extraction
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                    # Table extraction for casing/completion schedules
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

            # --- NLP / Regex Entity Extraction Logic ---
            # 1. Depth Intervals Extraction (e.g. 1200 - 2400 ft/m)
            depth_matches = re.findall(r'(\d{2,5})\s*(?:ft|m)?\s*[-–to]+\s*(\d{2,5})\s*(?:ft|m)?', full_text, re.IGNORECASE)

            # 2. Event Keyword Matching (Mud Loss, Stuck Pipe, Kick, Water Influx, Casing)
            events_found = []
            if re.search(r'loss|lost circulation|mud loss', full_text, re.IGNORECASE):
                events_found.append("Mud Loss")
            if re.search(r'stuck|stuck pipe|freeing', full_text, re.IGNORECASE):
                events_found.append("Stuck Pipe")
            if re.search(r'kick|gas cut|blowout|influx', full_text, re.IGNORECASE):
                events_found.append("Well Kick")
            if re.search(r'casing|cementing|perf', full_text, re.IGNORECASE):
                events_found.append("Casing/Completion")

            event_type = ", ".join(events_found) if events_found else "Normal Drilling / Routine Log"

            # Extract depth range
            start_depth = int(depth_matches[0][0]) if depth_matches else 0
            end_depth = int(depth_matches[0][1]) if depth_matches else 0

            # Store snippet for RAG Citation Engine
            raw_snippet = full_text[:400].replace("\n", " ") if full_text else "No extractable text (Scanned image)"

            processed_records.append({
                "report_id": file_name.replace(".pdf", ""),
                "start_depth": start_depth,
                "end_depth": end_depth,
                "detected_event": event_type,
                "raw_snippet": raw_snippet,
                "file_path": pdf_path
            })

        except Exception as e:
            print(f"Error parsing {file_name}: {e}")

# Save extracted records
if processed_records:
    df_extracted = pd.DataFrame(processed_records)
    df_extracted.to_csv(OUTPUT_CSV, index=False)
    print(f"\nExtraction Pipeline Complete!")
    print(f"Processed: {len(df_extracted)} WCR Reports.")
    print(f"Output saved to: {OUTPUT_CSV}\n")