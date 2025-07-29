import csv
from difflib import get_close_matches
from pathlib import Path

# Navigate to root, then into data/
CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "brands_202507221104.csv"

def load_brand_names():
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader if row]

def find_closest_brand(name: str):
    brands = load_brand_names()
    matches = get_close_matches(name, brands, n=1, cutoff=0.7)
    return matches[0] if matches else None
