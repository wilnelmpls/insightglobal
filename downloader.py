import requests
import csv
import os
import re

from concurrent.futures import ThreadPoolExecutor

# CMS API endpoint
url = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items"

# Directory to save CSVs
output_dir = "cms_csvs"
os.makedirs(output_dir, exist_ok=True)

def to_snake_case(s):
    # Replace spaces and hyphens with underscores, remove non-alphanumerics
    s = re.sub(r"[^\w\s-]", "", s)
    s = s.replace(" ", "_").replace("-", "_")
    return s.lower()

# Function to download and process a single CSV
def download_and_process_csv(item):
    download_url = item.get("downloadURL")
    title = item.get("title", "unknown_dataset").replace(" ", "_")
    
    if not download_url or not download_url.endswith(".csv"):
        return f"Skipped: {title} (invalid or missing CSV URL)"

    try:
        response = requests.get(download_url)
        response.raise_for_status()
        lines = response.text.splitlines()
        reader = csv.reader(lines)

        # Example transformation: uppercase all headers
        rows = list(reader)
        if rows:
            rows[0] = [to_snake_case(col) for col in rows[0]]

        # Write to disk
        output_path = os.path.join(output_dir, f"{title}.csv")
        with open(output_path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        return f"Saved: {title}.csv"
    except Exception as e:
        return f"Error: {title} — {str(e)}"

# Main logic
def main():
    response = requests.get(url)
    data = response.json()

    # Flatten all distribution items across datasets
    tasks = []
    for dataset in data:
        title = dataset.get("title")
        for item in dataset.get("distribution", []):
            item["title"] = title  # Attach title for naming
            tasks.append(item)

    # Run downloads concurrently
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(download_and_process_csv, tasks)

    # Print results
    for result in results:
        print(result)

if __name__ == "__main__":
    main()