# ankitools_lib/card_generators/arithmetic.py

import itertools
import uuid
from typing import List, Literal, Set

from ..anki_connect import add_note as anki_add_note, AnkiConnectError

def parse_operands_str(operands_str: str) -> List[int] | None:
    """Parses a comma-delimited string of numbers into a list of integers."""
    try:
        return [int(op.strip()) for op in operands_str.split(',')]
    except ValueError:
        # Consider raising a custom error or returning None for the CLI to handle
        print("Error: Operands must be a comma-delimited list of numbers (e.g., '3,7,8,9').")
        return None

def generate_arithmetic_problems(
    deck_name: str,
    operands_list: List[int],
    operations_to_generate: Literal["addition", "multiplication", "all"] = "all",
    dry_run: bool = False
) -> dict:
    """
    Generates arithmetic problems and adds them as Anki notes.

    Args:
        deck_name (str): The name of the Anki deck.
        operands_list (List[int]): A list of numbers to use as operands.
        operations_to_generate (Literal["addition", "multiplication", "all"], optional):
            Type of problems. Defaults to "all".
        dry_run (bool, optional): If True, prints actions instead of performing them. Defaults to False.

    Returns:
        dict: A summary of actions taken (e.g., cards_added, problems_generated).
    """
    if not operands_list or len(operands_list) < 1:
        # print("Error: At least one operand must be provided.") # Library should raise or return error status
        return {"error": "At least one operand must be provided.", "cards_added": 0, "problems_generated_count": 0}

    run_uuid = str(uuid.uuid4())
    generated_problems_set: Set[str] = set()  # To avoid duplicate cards in a single run
    cards_added_count = 0
    problems_generated_count = 0
    
    results_summary = {
        "run_uuid": run_uuid,
        "cards_added": 0,
        "problems_generated_count": 0,
        "errors": []
    }

    print(f"Generating arithmetic cards for deck: '{deck_name}'")
    print(f"Operands: {operands_list}")
    print(f"Operations: {operations_to_generate}")
    if dry_run:
        print("DRY RUN: No cards will be added to Anki.")

    for op1, op2 in itertools.product(operands_list, repeat=2):
        if operations_to_generate == "addition" or operations_to_generate == "all":
            problem_front = f"{op1}+{op2}"
            problem_back = str(op1 + op2)
            
            if problem_front not in generated_problems_set:
                problems_generated_count += 1
                note_tags = [run_uuid, "ankitools-generated", "mental-arithmetic", "addition"]
                if dry_run:
                    print(f"  DRY-RUN: Would add ADDITION card: Front='{problem_front}', Back='{problem_back}', Tags: {note_tags}")
                    results_summary["cards_added"] +=1 # Count as if added for dry run summary
                else:
                    try:
                        note_id = anki_add_note(
                            deck_name=deck_name,
                            model_name="Basic", # Assuming Basic model
                            fields={"Front": problem_front, "Back": problem_back},
                            tags=note_tags
                        )
                        if note_id:
                            results_summary["cards_added"] += 1
                            print(f"  Added ADDITION card: Front='{problem_front}', Back='{problem_back}', ID: {note_id}")
                        else:
                            print(f"    Failed to add card '{problem_front}' (returned None).")
                            results_summary["errors"].append(f"Failed to add card '{problem_front}'")
                    except AnkiConnectError as e:
                        print(f"    Error adding card '{problem_front}': {e}")
                        results_summary["errors"].append(f"Error adding card '{problem_front}': {e}")
                generated_problems_set.add(problem_front)

        if operations_to_generate == "multiplication" or operations_to_generate == "all":
            problem_front = f"{op1}x{op2}"
            problem_back = str(op1 * op2)

            if problem_front not in generated_problems_set:
                problems_generated_count += 1
                note_tags = [run_uuid, "ankitools-generated", "mental-arithmetic", "multiplication"]
                if dry_run:
                    print(f"  DRY-RUN: Would add MULTIPLICATION card: Front='{problem_front}', Back='{problem_back}', Tags: {note_tags}")
                    results_summary["cards_added"] +=1 # Count as if added for dry run summary
                else:
                    try:
                        note_id = anki_add_note(
                            deck_name=deck_name,
                            model_name="Basic", # Assuming Basic model
                            fields={"Front": problem_front, "Back": problem_back},
                            tags=note_tags
                        )
                        if note_id:
                            results_summary["cards_added"] += 1
                            print(f"  Added MULTIPLICATION card: Front='{problem_front}', Back='{problem_back}', ID: {note_id}")
                        else:
                            print(f"    Failed to add card '{problem_front}' (returned None).")
                            results_summary["errors"].append(f"Failed to add card '{problem_front}'")
                    except AnkiConnectError as e:
                        print(f"    Error adding card '{problem_front}': {e}")
                        results_summary["errors"].append(f"Error adding card '{problem_front}': {e}")
                generated_problems_set.add(problem_front)
    
    results_summary["problems_generated_count"] = len(generated_problems_set) # More accurate count of unique problems
    return results_summary
