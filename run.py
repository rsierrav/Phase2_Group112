
import sys
import requests
import json


def fetch_data(url):

    try:
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            return None
        
    except requests.exceptions.RequestException as e:
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./run.py [URL_FILE]")
        sys.exit(1)

    url = sys.argv[1]

    data = fetch_data(url)

    if data == None:
        print("Invalid url address. Please try again.")

    else:

        # to do format data
        print(data)
