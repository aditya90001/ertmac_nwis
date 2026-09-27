import os
import requests
import pandas as pd

# Directories setup
BASE_DIR = r"C:\Users\DELL\OneDrive\Desktop\nwis\data\nm_ocd"
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

# CNRA CKAN Data API Endpoint
RESOURCE_ID = "bff565b3-b3b4-4727-b10b-e09e0012ec3b"
API_URL = "https://data.cnra.ca.gov/api/3/action/datastore_search"

print("Fetching REAL Well Completion Data from CNRA CKAN Data API...")

params = {
    "resource_id": RESOURCE_ID,
    "limit": 50  # Initial batch of 50 real wells
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

try:
    response = requests.get(API_URL, params=params, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        records = data.get("result", {}).get("records", [])

        print(f"Successfully fetched {len(records)} REAL well records via API!")

        # Save structured metadata to CSV directly
        df_wells = pd.DataFrame(records)
        csv_output = os.path.join(BASE_DIR, "real_cnra_wells_metadata.csv")
        df_wells.to_csv(csv_output, index=False)
        print(f"Saved Metadata CSV to: {csv_output}")

        # Download associated PDFs if direct URL column exists
        pdf_count = 0
        for idx, record in enumerate(records):
            # Check for PDF/Report Link fields
            pdf_url = record.get("WCRLink") or record.get("PDFLink") or record.get("URL")

            if pdf_url and str(pdf_url).startswith("http"):
                pdf_name = f"CNRA_Real_WCR_{record.get('WCRNumber', idx+1)}.pdf"
                pdf_path = os.path.join(PDF_DIR, pdf_name)

                print(f"Downloading [{pdf_count+1}]: {pdf_name}...")
                try:
                    pdf_res = requests.get(pdf_url, headers=headers, timeout=20, stream=True)
                    if pdf_res.status_code == 200:
                        with open(pdf_path, "wb") as f:
                            for chunk in pdf_res.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                        pdf_count += 1
                        print(f"Saved PDF: {pdf_name}")
                except Exception as e:
                    print(f"Failed PDF download for {pdf_name}: {e}")

        print(f"\nAPI Fetch Completed! Metadata: {len(records)} records, PDFs: {pdf_count} downloaded.\n")

    else:
        print(f"API Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"CNRA API Request Failed: {e}")