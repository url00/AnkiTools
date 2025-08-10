import json
import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"
ANKICONNECT_VERSION = 6

class AnkiConnectError(Exception):
    """Custom exception for AnkiConnect API errors."""
    pass

def _anki_request(action: str, params: dict | None = None) -> dict:
    """
    Helper function to make a request to AnkiConnect.

    Args:
        action (str): The AnkiConnect action to perform.
        params (dict | None, optional): Parameters for the action. Defaults to None.

    Returns:
        dict: The 'result' part of the AnkiConnect response.

    Raises:
        AnkiConnectError: If the AnkiConnect API returns an error or the response is malformed.
        requests.exceptions.RequestException: If there's a network issue.
    """
    payload = {"action": action, "version": ANKICONNECT_VERSION}
    if params:
        payload["params"] = params
    
    try:
        response = requests.post(ANKICONNECT_URL, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()
    except requests.exceptions.RequestException as e:
        raise AnkiConnectError(f"Network error connecting to AnkiConnect: {e}")
    except json.JSONDecodeError:
        raise AnkiConnectError("Failed to decode JSON response from AnkiConnect.")

    if "error" not in response_data or "result" not in response_data:
        raise AnkiConnectError("Malformed response from AnkiConnect: missing 'error' or 'result' field.")

    if response_data["error"] is not None:
        raise AnkiConnectError(f"AnkiConnect API error: {response_data['error']}")
    
    return response_data["result"]

def test_connection() -> bool:
    """
    Tests the connection to AnkiConnect by requesting the API version.

    Returns:
        bool: True if connection is successful and API version matches, False otherwise.
    """
    try:
        version = _anki_request("version")
        if version == ANKICONNECT_VERSION:
            print(f"Successfully connected to AnkiConnect. API Version: {version}")
            return True
        else:
            print(f"Connected to AnkiConnect, but API version mismatch. Expected {ANKICONNECT_VERSION}, got {version}")
            return False
    except AnkiConnectError as e:
        print(f"Failed to connect to AnkiConnect: {e}")
        print("Please ensure Anki is running and the AnkiConnect addon is installed and enabled.")
        return False

def get_deck_names() -> list[str] | None:
    """
    Retrieves a list of all deck names from Anki.

    Returns:
        list[str] | None: A list of deck names, or None if an error occurs.
    """
    try:
        deck_names = _anki_request("deckNames")
        return deck_names
    except AnkiConnectError as e:
        print(f"Error getting deck names: {e}")
        return None

# Example usage if run directly (can be removed or kept for quick testing)
# if __name__ == '__main__':
#     if test_connection():
#         print("\nAttempting to get deck names...")
#         decks = get_deck_names()
#         if decks is not None:
#             print("Available decks:")
#             for deck in decks:
#                 print(f"- {deck}")
#         else:
#             print("Could not retrieve deck names.")

def find_notes(query: str) -> list[int] | None:
    """
    Finds notes based on a query.

    Args:
        query (str): The Anki search query (e.g., "deck:current", "tag:mytag").

    Returns:
        list[int] | None: A list of note IDs, or None if an error occurs.
    """
    try:
        note_ids = _anki_request("findNotes", {"query": query})
        return note_ids
    except AnkiConnectError as e:
        print(f"Error finding notes with query '{query}': {e}")
        return None

def notes_info(note_ids: list[int]) -> list[dict] | None:
    """
    Retrieves detailed information for a list of notes.

    Args:
        note_ids (list[int]): A list of note IDs.

    Returns:
        list[dict] | None: A list of note information objects, or None if an error occurs.
                           Each object contains details like fields, modelName, tags, etc.
    """
    if not note_ids:
        return []
    try:
        info = _anki_request("notesInfo", {"notes": note_ids})
        return info
    except AnkiConnectError as e:
        print(f"Error getting info for notes {note_ids}: {e}")
        return None

def update_note_fields(note_id: int, fields: dict) -> bool:
    """
    Updates the fields of a specific note.

    Args:
        note_id (int): The ID of the note to update.
        fields (dict): A dictionary where keys are field names and values are the new content.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    note_params = {
        "id": note_id,
        "fields": fields
    }
    try:
        _anki_request("updateNoteFields", {"note": note_params})
        # print(f"Successfully updated fields for note ID: {note_id}") # Consider logging instead of printing
        return True
    except AnkiConnectError as e:
        # print(f"Error updating fields for note ID {note_id}: {e}") # Consider logging
        return False

def update_note_model_and_fields(note_id: int, new_model_name: str, fields_for_new_model: dict, tags: list[str] | None = None) -> bool:
    """
    Updates the model and fields (and optionally tags) of an existing note using the 'updateNoteModel' action.

    Args:
        note_id (int): The ID of the note to update.
        new_model_name (str): The name of the new model to apply to the note.
        fields_for_new_model (dict): A dictionary containing all field names and their values
                                     for the new model.
        tags (list[str] | None, optional): A list of tags to set for the note.
                                           If None, tags are not changed.
                                           If an empty list is provided, all existing tags will be removed.
                                           Defaults to None.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    note_details_payload = {
        "id": note_id,
        "modelName": new_model_name,
        "fields": fields_for_new_model
    }
    if tags is not None: # An empty list [] means remove all tags
        note_details_payload["tags"] = tags

    params = {"note": note_details_payload}

    try:
        _anki_request("updateNoteModel", params)
        # print(f"Successfully updated note ID {note_id} to model '{new_model_name}' and updated fields.")
        # if tags is not None:
            # print(f"  Tags for note ID {note_id} set to: {tags}")
        return True
    except AnkiConnectError as e:
        # print(f"Error updating note ID {note_id} using updateNoteModel (new model: '{new_model_name}'): {e}")
        return False

def add_note(deck_name: str, model_name: str, fields: dict, tags: list[str] | None = None) -> int | None:
    """
    Adds a new note to Anki.

    Args:
        deck_name (str): The name of the deck to add the note to.
        model_name (str): The name of the model to use for the note.
        fields (dict): A dictionary of field names and their content.
        tags (list[str] | None, optional): A list of tags to add to the note. Defaults to None.

    Returns:
        int | None: The ID of the newly created note, or None if an error occurs.
    """
    note_params = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "options": {
            "allowDuplicate": False, 
            "duplicateScope": "deck" 
        }
    }
    if tags: 
        note_params["tags"] = tags
    
    try:
        result = _anki_request("addNote", {"note": note_params})
        if result: 
            # print(f"Successfully added note to deck '{deck_name}' with model '{model_name}'. Note ID: {result}")
            return result
        else: 
            # print(f"Failed to add note to deck '{deck_name}' (result was empty but no error reported).")
            return None
    except AnkiConnectError as e:
        # print(f"Error adding note to deck '{deck_name}': {e}")
        return None
