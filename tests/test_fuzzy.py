import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) 
from src.utils.fuzzy_match import find_closest_brand

if __name__ == "__main__":
    query = "Nivi"  # intentionally misspelled brand name
    matches = find_closest_brand(query)
    print(f"Closest matches for '{query}': {matches}")
