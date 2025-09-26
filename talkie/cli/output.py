"""Output formatting module for Talkie CLI."""

def print_response(response_data):
    """Print HTTP response data."""
    print("Response received:")
    print(f"Status: {response_data.get('status', 'Unknown')}")
    print(f"Headers: {response_data.get('headers', {})}")
    print(f"Body: {response_data.get('body', '')}")
