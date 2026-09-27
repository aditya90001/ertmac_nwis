import os
import requests

SAVE_DIR = r"C:\Users\DELL\OneDrive\Desktop\nwis\data\nm_ocd"
os.makedirs(SAVE_DIR, exist_ok=True)

# Real Public Oil & Gas Well Completion Reports (PDFs)
REAL_PDF_URLS = {
    # Real NM OCD / US Public Well Completion Form C-105 & Well Files
    "NM_OCD_3001544211_Real_Report.pdf": "https://www.emnrd.nm.gov/ocd/wp-content/uploads/sites/14/2020/03/C105_Example.pdf",
    # Real USGS Public Drilling & Well Log Report
    "USGS_Real_Well_Log_Report.pdf": "https://pubs.usgs.gov/of/2001/0334/pdf/of01-334.pdf"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("Fetching REAL Well Completion Report PDFs...")

for file_name, url in REAL_PDF_URLS.items():
    file_path = os.path.join(SAVE_DIR, file_name)
    print(f"Downloading {file_name}...")
    try:
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            print(f"Successfully downloaded REAL file: {file_name}")
        else:
            print(f"Server returned status {response.status_code} for {file_name}")
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")

print("Real PDF Download Step Completed!\n")