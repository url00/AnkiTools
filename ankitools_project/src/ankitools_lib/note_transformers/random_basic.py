# ankitools_lib/note_transformers/random_basic.py

from typing import List, Dict, Any, Optional

from ..anki_connect import (
    find_notes as anki_find_notes,
    notes_info as anki_notes_info,
    update_note_model_and_fields as anki_update_note_model_and_fields,
    AnkiConnectError
)
from ..ai_services import generate_rephrased_prompts as ai_generate_rephrased_prompts
# AI services configuration is handled by the CLI entry point

def transform_notes_to_random_basic(
    query: str,
    prompt_field_name: str,
    num_variations: int = 2,
    max_notes_to_process: Optional[int] = None, # 0 or None for no limit
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Transforms 'Basic' model notes matching a specified Anki query to 'RandomBasic' style.
    It rephrases content from `prompt_field_name` using AI, combines variations,
    and updates the note's model and field.

    Args:
        query (str): The Anki search query to find notes to process.
        prompt_field_name (str): The field containing the original prompt (e.g., 'Front').
        num_variations (int, optional): Number of AI rephrased variations. Defaults to 2.
        max_notes_to_process (Optional[int], optional): Max notes to process. None or 0 for no limit. Defaults to None.
        dry_run (bool, optional): If True, prints actions instead of performing them. Defaults to False.

    Returns:
        Dict[str, Any]: A summary of the transformation process.
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

    # anki_query is now directly the 'query' parameter
    print(f"Finding notes with query: \"{query}\"")

    try:
        note_ids = anki_find_notes(query)
        if note_ids is None:
            results_summary["errors_general"].append("Failed to retrieve notes from Anki (findNotes returned None).")
            return results_summary
        
        results_summary["notes_found_query"] = len(note_ids)
        if not note_ids:
            print("No notes found matching the query. Nothing to process.")
            return results_summary
        
        print(f"Found {len(note_ids)} notes matching the query.")
        if max_notes_to_process is not None and max_notes_to_process > 0 and len(note_ids) > max_notes_to_process:
            print(f"Limiting processing to the first {max_notes_to_process} notes.")
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
                print(f"  Could not retrieve details for note ID {note_id}. Skipping.")
                results_summary["failed_anki_update"] += 1
                continue
            
            note_data = note_details_list[0]
            current_model_name = note_data["modelName"]
            
            if current_model_name != "Basic":
                print(f"  Note ID {note_id} (model: '{current_model_name}') is not 'Basic'. Skipping.")
                results_summary["skipped_not_basic_model"] += 1
                continue

            if prompt_field_name not in note_data["fields"]:
                print(f"  Field '{prompt_field_name}' not found in note ID {note_id}. Skipping.")
                results_summary["skipped_field_missing"] += 1
                continue
            
            original_prompt = note_data["fields"][prompt_field_name]["value"]
            current_tags = note_data.get("tags", []) # Ensure tags is a list

            print(f"  Original prompt from '{prompt_field_name}': \"{original_prompt[:100]}{'...' if len(original_prompt) > 100 else ''}\"")

            # Check if already processed (contains '|') - this is a simple heuristic
            if "|" in original_prompt:
                print("  Prompt already seems to be in RandomBasic format (contains '|'). Skipping.")
                results_summary["skipped_already_transformed"] += 1
                continue
            
            results_summary["notes_eligible_for_processing"] += 1
            print(f"  Generating {num_variations} rephrased versions...")
            rephrased_prompts = ai_generate_rephrased_prompts(original_prompt, num_variations)

            if not rephrased_prompts:
                print(f"  Failed to generate rephrased prompts for note ID {note_id}. Skipping.")
                results_summary["failed_ai_generation"] += 1
                continue
            
            all_prompts = [original_prompt.strip()] + [rp.strip() for rp in rephrased_prompts]
            new_prompt_field_value = " | ".join(all_prompts)
            target_model_name = "RandomBasic" # Target model name
            
            # Prepare fields for the new model, ensuring all existing fields are carried over
            all_fields_for_new_model = {k: v["value"] for k, v in note_data["fields"].items()}
            all_fields_for_new_model[prompt_field_name] = new_prompt_field_value

            if dry_run:
                print(f"  DRY-RUN: Would update note ID {note_id} model from '{current_model_name}' to '{target_model_name}'.")
                print(f"  DRY-RUN: Field '{prompt_field_name}' would be set to: \"{new_prompt_field_value[:100]}{'...' if len(new_prompt_field_value) > 100 else ''}\"")
                results_summary["notes_processed_successfully"] += 1
            else:
                print(f"  Updating note ID {note_id}: model to '{target_model_name}', fields, and preserving tags {current_tags}...")
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
