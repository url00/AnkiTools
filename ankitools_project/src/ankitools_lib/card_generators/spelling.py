# ankitools_lib/card_generators/spelling.py

import uuid
import pyphen # type: ignore
from typing import List, Dict, Any

from ..anki_connect import add_note as anki_add_note, AnkiConnectError
from ..ai_services import get_word_description as ai_get_word_description 
# ai_services also handles configure_gemini_globally, which should be called by CLI entry point

def generate_spelling_cards_from_file(
    input_file_path: str,
    deck_name: str,
    tag_run: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generates Anki spelling cards with syllable-based cloze deletions and AI descriptions.

    Args:
        input_file_path (str): Path to a newline-delimited text file containing words.
        deck_name (str): The name of the Anki deck to add cards to.
        tag_run (bool, optional): If True, tags notes with a run-specific UUID. Defaults to True.
        dry_run (bool, optional): If True, prints actions instead of performing them. Defaults to False.
    
    Returns:
        Dict[str, Any]: A summary of the operation.
    """
    results_summary = {
        "words_processed": 0,
        "notes_created": 0,
        "run_uuid": None,
        "errors": [],
        "skipped_syllabification": 0,
        "skipped_ai_description": 0
    }

    try:
        dic = pyphen.Pyphen(lang='en_US')
    except Exception as e:
        print(f"Error initializing Pyphen: {e}")
        results_summary["errors"].append(f"Pyphen initialization failed: {e}")
        return results_summary # Cannot proceed without pyphen

    run_uuid_str = None
    if tag_run:
        run_uuid_str = str(uuid.uuid4())
        results_summary["run_uuid"] = run_uuid_str
        print(f"Tagging notes for this run with UUID: {run_uuid_str}")
    
    if dry_run:
        print("DRY RUN: No cards will be actually added to Anki.")

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if not word:
                    continue

                results_summary["words_processed"] += 1
                hyphenated_word = dic.inserted(word) # e.g., "beau-ti-ful"
                syllables = hyphenated_word.split('-')

                if not syllables or not syllables[0]:
                    print(f"Could not syllabify '{word}'. Skipping.")
                    results_summary["skipped_syllabification"] += 1
                    results_summary["errors"].append(f"Syllabification failed for '{word}'")
                    continue

                cloze_parts = [f"{{{{c{i+1}::{syl}}}}}" for i, syl in enumerate(syllables)]
                cloze_text = "".join(cloze_parts) # "{{c1::beau}}{{c2::ti}}{{c3::ful}}"
                
                description = ai_get_word_description(word)
                if not description:
                    print(f"Could not get AI description for '{word}'. Proceeding without it.")
                    results_summary["skipped_ai_description"] += 1
                    # No error appended here, as it's a soft failure for description
                
                final_cloze_text = f"{description}: {cloze_text}" if description else cloze_text
                extra_field_content = f"Original word: {word}"
                
                note_tags = []
                if run_uuid_str:
                    note_tags.append(run_uuid_str)
                note_tags.extend(["ankitools-generated", "spelling-cloze"])

                if dry_run:
                    print(f"  DRY-RUN: Would add SPELLING card for '{word}':")
                    print(f"    Deck: {deck_name}, Model: Cloze")
                    print(f"    Text: {final_cloze_text}")
                    print(f"    Extra: {extra_field_content}")
                    print(f"    Tags: {note_tags}")
                    results_summary["notes_created"] += 1 # Count as if created
                else:
                    try:
                        note_id = anki_add_note(
                            deck_name=deck_name,
                            model_name="Cloze",
                            fields={"Text": final_cloze_text, "Extra": extra_field_content},
                            tags=note_tags
                        )
                        if note_id:
                            print(f"  Successfully added SPELLING note for '{word}', ID: {note_id}")
                            results_summary["notes_created"] += 1
                        else:
                            print(f"    Failed to add SPELLING note for '{word}' (returned None).")
                            results_summary["errors"].append(f"Failed to add note for '{word}'")
                    except AnkiConnectError as e:
                        print(f"    AnkiConnect error adding note for '{word}': {e}")
                        results_summary["errors"].append(f"AnkiConnect error for '{word}': {e}")
                    except Exception as e:
                        print(f"    Unexpected error adding note for '{word}': {e}")
                        results_summary["errors"].append(f"Unexpected error for '{word}': {e}")
    
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file_path}'")
        results_summary["errors"].append(f"Input file not found: {input_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred during file processing: {e}")
        results_summary["errors"].append(f"File processing error: {e}")

    return results_summary
