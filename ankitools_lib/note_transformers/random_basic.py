# ankitools_lib/note_transformers/random_basic.py
"""
This module provides functions for transforming existing Anki notes.
"""

from typing import Dict, Any, Optional

from ..anki_connect import (
    find_notes as anki_find_notes,
    notes_info as anki_notes_info,
    update_note_model_and_fields as anki_update_note_model_and_fields,
    AnkiConnectError
)
from ..ai_services import generate_rephrased_prompts as ai_generate_rephrased_prompts

def transform_notes_to_random_basic(
    query: str,
    prompt_field_name: str,
    num_variations: int = 2,
    max_notes_to_process: Optional[int] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Transforms 'Basic' model notes matching a query to the 'RandomBasic' style.

    This function finds notes using an Anki query, generates AI-powered rephrasings
    of a specified field, and then updates the note to the 'RandomBasic' model,
    which can display one of the variations randomly.

    Args:
        query: The Anki search query to find notes to transform.
        prompt_field_name: The name of the field to rephrase (e.g., "Front").
        num_variations: The number of rephrased variations to generate.
        max_notes_to_process: The maximum number of notes to process.
        dry_run: If True, simulates the process without making changes to Anki.

    Returns:
        A dictionary summarizing the operation, including counts of processed
        notes and any errors.
    """
    results_summary = {
        "notes_found_query": 0,
        "notes_eligible_for_processing": 0, # 'Basic' model notes matching criteria before AI
        "notes_processed_successfully": 0, # Successfully transformed or would be in dry_run
        "notes_updated_anki": 0, # Actual Anki updates (not in dry_run)
        "failed_ai_generation": 0,
        "failed_anki_update": 0,
        "skipped_already_transformed": 0,
        "skipped_field_missing": 0,
        "skipped_not_basic_model": 0,
        "errors_general": []
    }

    print(f"Finding notes with query: \"{query}\"")

    try:
        note_ids = anki_find_notes(query)
        if note_ids is None:
            results_summary["errors_general"].append("Failed to retrieve notes from Anki.")
            return results_summary
        
        results_summary["notes_found_query"] = len(note_ids)
        if not note_ids:
            return results_summary
        
        if max_notes_to_process is not None and max_notes_to_process > 0 and len(note_ids) > max_notes_to_process:
            note_ids = note_ids[:max_notes_to_process]

    except AnkiConnectError as e:
        results_summary["errors_general"].append(f"AnkiConnect error finding notes: {e}")
        return results_summary
    
    print(f"Processing up to {len(note_ids)} notes...")

    for i, note_id in enumerate(note_ids):
        print(f"\nProcessing note {i+1}/{len(note_ids)} (ID: {note_id})...")
        try:
            note_details_list = anki_notes_info([note_id])
            if not note_details_list:
                results_summary["failed_anki_update"] += 1
                continue
            
            note_data = note_details_list[0]
            current_model_name = note_data["modelName"]
            
            # Skip if not a 'Basic' note
            if current_model_name != "Basic":
                results_summary["skipped_not_basic_model"] += 1
                continue

            # Skip if the prompt field doesn't exist
            if prompt_field_name not in note_data["fields"]:
                results_summary["skipped_field_missing"] += 1
                continue
            
            original_prompt = note_data["fields"][prompt_field_name]["value"]
            current_tags = note_data.get("tags", [])

            # Skip if already transformed
            if "|" in original_prompt:
                results_summary["skipped_already_transformed"] += 1
                continue
            
            results_summary["notes_eligible_for_processing"] += 1
            
            # Generate rephrased prompts
            rephrased_prompts = ai_generate_rephrased_prompts(original_prompt, num_variations)
            if not rephrased_prompts:
                results_summary["failed_ai_generation"] += 1
                continue
            
            # Combine original and rephrased prompts
            all_prompts = [original_prompt.strip()] + [rp.strip() for rp in rephrased_prompts]
            new_prompt_field_value = " | ".join(all_prompts)
            target_model_name = "RandomBasic"
            
            # Prepare fields for the new model
            all_fields_for_new_model = {k: v["value"] for k, v in note_data["fields"].items()}
            all_fields_for_new_model[prompt_field_name] = new_prompt_field_value

            if dry_run:
                print(f"  DRY-RUN: Would update note ID {note_id} to '{target_model_name}'.")
                results_summary["notes_processed_successfully"] += 1
            else:
                if anki_update_note_model_and_fields(note_id, target_model_name, all_fields_for_new_model, current_tags):
                    results_summary["notes_processed_successfully"] += 1
                    results_summary["notes_updated_anki"] += 1
                else:
                    results_summary["failed_anki_update"] += 1
        
        except AnkiConnectError as e:
            print(f"  AnkiConnect error processing note ID {note_id}: {e}. Skipping.")
            results_summary["failed_anki_update"] += 1
            results_summary["errors_general"].append(f"AnkiConnect error on note {note_id}: {e}")
        except Exception as e:
            print(f"  Unexpected error processing note ID {note_id}: {e}. Skipping.")
            results_summary["failed_anki_update"] += 1 # Or a new category for unexpected
            results_summary["errors_general"].append(f"Unexpected error on note {note_id}: {e}")
            
    return results_summary
