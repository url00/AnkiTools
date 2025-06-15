# ankitools_lib/card_generators/spelling.py
"""
This module provides functions for generating spelling Anki cards from a list of words.
"""

import uuid
import pyphen
from typing import Dict, Any

from ..anki_connect import add_note as anki_add_note, AnkiConnectError
from ..ai_services import get_word_description as ai_get_word_description

def generate_spelling_cards_from_file(
    input_file_path: str,
    deck_name: str,
    tag_run: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generates Anki spelling cards with syllable-based cloze deletions and AI-powered
    descriptions from a file containing a list of words.

    For each word, this function:
    1.  Syllabifies the word (e.g., "beautiful" -> "beau-ti-ful").
    2.  Creates a cloze deletion note (e.g., "{{c1::beau}}{{c2::ti}}{{c3::ful}}").
    3.  Fetches a description of the word using an AI service.
    4.  Adds the new note to the specified Anki deck.

    Args:
        input_file_path: Path to a newline-delimited text file of words.
        deck_name: The name of the Anki deck to add the cards to.
        tag_run: Whether to tag the created notes with a unique run UUID.
        dry_run: If True, simulates the process without creating notes in Anki.

    Returns:
        A dictionary summarizing the operation, including the number of notes
        created and any errors.
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
        results_summary["errors"].append(f"Pyphen initialization failed: {e}")
        return results_summary

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
                
                # Syllabify the word
                hyphenated_word = dic.inserted(word)
                syllables = hyphenated_word.split('-')

                if not syllables or not syllables[0]:
                    results_summary["skipped_syllabification"] += 1
                    results_summary["errors"].append(f"Syllabification failed for '{word}'")
                    continue

                # Create the cloze deletion text
                cloze_parts = [f"{{{{c{i+1}::{syl}}}}}" for i, syl in enumerate(syllables)]
                cloze_text = "".join(cloze_parts)
                
                # Get AI-powered description
                description = ai_get_word_description(word)
                if not description:
                    results_summary["skipped_ai_description"] += 1
                
                final_cloze_text = f"{description}: {cloze_text}" if description else cloze_text
                extra_field_content = f"Original word: {word}"
                
                note_tags = ["ankitools-generated", "spelling-cloze"]
                if run_uuid_str:
                    note_tags.append(run_uuid_str)

                if dry_run:
                    print(f"  DRY-RUN: Would add SPELLING card for '{word}':")
                    print(f"    Text: {final_cloze_text}")
                    results_summary["notes_created"] += 1
                else:
                    try:
                        note_id = anki_add_note(
                            deck_name=deck_name,
                            model_name="Cloze",
                            fields={"Text": final_cloze_text, "Extra": extra_field_content},
                            tags=note_tags
                        )
                        if note_id:
                            results_summary["notes_created"] += 1
                        else:
                            results_summary["errors"].append(f"Failed to add note for '{word}'")
                    except AnkiConnectError as e:
                        results_summary["errors"].append(f"AnkiConnect error for '{word}': {e}")
                    except Exception as e:
                        results_summary["errors"].append(f"Unexpected error for '{word}': {e}")
    
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file_path}'")
        results_summary["errors"].append(f"Input file not found: {input_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred during file processing: {e}")
        results_summary["errors"].append(f"File processing error: {e}")

    return results_summary
