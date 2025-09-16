import sys
import requests


def fetch_data(url: str):
    """
    Fetch JSON data from a given URL.
    Returns parsed JSON on success, or None on failure.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


# NOTE:
# Data processing should be moved to the parse_input utils file.
# This script should remain as a lightweight entry point.
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./run.py [URL_FILE]")
        sys.exit(1)

    url = sys.argv[1]
    data = fetch_data(url)

    if data is None:
        print("Invalid URL address. Please try again.")
    else:
        # TODO: format data properly
        print(data)
