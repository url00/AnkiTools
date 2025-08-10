# ankitools_lib/deck_utils.py

from .anki_connect import get_deck_names as ac_get_deck_names, AnkiConnectError

def list_all_deck_names() -> list[str] | None:
    """
    Retrieves a list of all deck names from Anki.

    Returns:
        list[str] | None: A list of deck names, or None if an error occurs.
    """
    try:
        return ac_get_deck_names()
    except AnkiConnectError as e:
        print(f"Error listing deck names: {e}") # Or log this
        return None

# Add other deck utility functions here later, e.g.:
# - create_deck(deck_name: str)
# - delete_deck(deck_name: str)
# - get_deck_stats(deck_name: str)
