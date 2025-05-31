import os
from dotenv import load_dotenv

# Determine the project root assuming this file is at src/ankitools_lib/config.py
# and .env is at the project root (e.g., ankitools_project/.env)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')

def load_google_api_key() -> str | None:
    """
    Loads the Google API key from the .env file located at the project root.

    Returns:
        str | None: The API key if found and valid, otherwise None.
    """
    if os.path.exists(DOTENV_PATH):
        load_dotenv(dotenv_path=DOTENV_PATH)
    else:
        # Fallback to loading .env from the current working directory if not found at project root.
        # This might be useful if the library is used in a context where CWD is the project root.
        load_dotenv() 
        # Check if .env was loaded from CWD by checking if a key exists
        # This is a bit indirect; a more robust way might be needed if complex scenarios arise.
        # For now, we assume load_dotenv() without path checks standard locations or does nothing if no .env.
        # print(f"Warning: .env file not found at {DOTENV_PATH}. Attempting to load from current working directory or environment.")


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
