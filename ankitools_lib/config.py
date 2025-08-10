import os
from dotenv import load_dotenv

DOTENV_PATH = os.path.join(os.getcwd(), '.env')

def throw_if_spending_money_is_disabled() -> None:
    _load_dotenv()
    spending_money_enabled =  os.getenv("ENABLE_THINGS_THAT_COST_MONEY") == "1"
    if not spending_money_enabled:
        raise Exception("ENABLE_THINGS_THAT_COST_MONEY was set to false, cannot continue.")

def _load_dotenv() -> None:
    if os.path.exists(DOTENV_PATH):
        load_dotenv(dotenv_path=DOTENV_PATH)
    else:
        load_dotenv() 

def load_google_api_key() -> str | None:
    """
    Loads the Google API key from the .env file located at the project root.

    Returns:
        str | None: The API key if found and valid, otherwise None.
    """
    throw_if_spending_money_is_disabled()
    _load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print(f"Error: GOOGLE_API_KEY not found. Searched in {DOTENV_PATH} and environment variables.")
        print("Please ensure you have a .env file in the project root (e.g., ankitools_project/.env) or the variable is set in your environment.")
        print("Example .env file content:")
        print("GOOGLE_API_KEY=\"YOUR_ACTUAL_API_KEY\"")
        return None
    
    if api_key == "YOUR_GOOGLE_API_KEY_HERE" or not api_key.strip():
        print("Error: GOOGLE_API_KEY is set to the placeholder value or is empty.")
        print("Please replace 'YOUR_GOOGLE_API_KEY_HERE' in your .env file with your actual Google API key.")
        return None
        
    return api_key

# Consider adding functions for other configurations if needed, e.g., ANKICONNECT_URL
def get_ankiconnect_url() -> str:
    """
    Retrieves the AnkiConnect URL.
    Defaults to http://127.0.0.1:8765 if not set in .env.
    """
    if os.path.exists(DOTENV_PATH):
        load_dotenv(dotenv_path=DOTENV_PATH)
    else:
        load_dotenv()
        
    return os.getenv("ANKICONNECT_URL", "http://127.0.0.1:8765")


# Example usage (can be removed or kept for quick testing of this module)
# if __name__ == '__main__':
#     print(f"Attempting to load .env from: {DOTENV_PATH}")
#     key = load_google_api_key()
#     if key:
#         print(f"Successfully loaded API key (first 5 chars): {key[:5]}...")
#     else:
#         print("Failed to load API key.")
    
#     ankiconnect_url = get_ankiconnect_url()
#     print(f"AnkiConnect URL: {ankiconnect_url}")
