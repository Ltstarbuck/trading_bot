import requests


def fetch_economic_data(api_url):
    """Fetch economic data from the given API URL."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return the JSON data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching economic data: {e}")
        return None
