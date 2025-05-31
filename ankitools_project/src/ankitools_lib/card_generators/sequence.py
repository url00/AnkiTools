# ankitools_lib/card_generators/sequence.py

import uuid
from typing import List, Dict, Any, Tuple, Optional

from ..anki_connect import add_note as anki_add_note, AnkiConnectError

def parse_sequence_input(lines: List[str]) -> Tuple[Optional[str], List[str], Optional[str]]:
    """
    Parses raw input lines into title and sequence elements.
    Expected format:
    Line 1: Title
    Line 2..N: Sequence elements
    """
    if not lines:
        return None, [], "Input is empty."
    if len(lines) < 2:
        return None, [], "Input format error: Expected title and at least one sequence element."
    
    title = lines[0].strip()
    elements = [line.strip() for line in lines[1:] if line.strip()]
    
    if not title:
        return None, [], "Title cannot be empty."
    if not elements:
        return None, [], "Sequence must have at least one element."
        
    return title, elements, None

def create_sequence_anki_cards(
    deck_name: str,
    title: str,
    elements: List[str],
    tag_run: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generates various Anki cards for a given sequence and adds them to the specified deck.
    """
    results_summary = {
        "title": title,
        "elements_count": len(elements),
        "notes_created": 0,
        "run_uuid": None,
        "errors": []
    }

    if not elements:
        results_summary["errors"].append("No elements provided for the sequence.")
        return results_summary

    run_uuid_str = None
    if tag_run:
        run_uuid_str = str(uuid.uuid4())
        results_summary["run_uuid"] = run_uuid_str
        print(f"Tagging sequence notes for '{title}' with UUID: {run_uuid_str}")

    if dry_run:
        print(f"DRY RUN: Processing sequence '{title}' for deck '{deck_name}'. No cards will be added.")

    def _add_card(model_name: str, fields: Dict[str, str], card_type_tag: str, context_info: str):
        nonlocal results_summary
        tags = ["ankitools-generated", "sequence", card_type_tag]
        if run_uuid_str:
            tags.append(run_uuid_str)
        
        if dry_run:
            print(f"  DRY-RUN: Would add {card_type_tag.upper()} card for '{title}' ({context_info}):")
            for k, v in fields.items():
                print(f"    {k}: {v[:100]}{'...' if len(v) > 100 else ''}")
            print(f"    Tags: {tags}")
            results_summary["notes_created"] += 1
        else:
            try:
                note_id = anki_add_note(deck_name, model_name, fields, tags)
                if note_id:
                    results_summary["notes_created"] += 1
                else:
                    msg = f"Failed to add {card_type_tag} card for '{title}' ({context_info})"
                    print(f"    {msg} (returned None).")
                    results_summary["errors"].append(msg)
            except AnkiConnectError as e:
                msg = f"AnkiConnect error adding {card_type_tag} card for '{title}' ({context_info}): {e}"
                print(f"    {msg}")
                results_summary["errors"].append(msg)
            except Exception as e:
                msg = f"Unexpected error adding {card_type_tag} card for '{title}' ({context_info}): {e}"
                print(f"    {msg}")
                results_summary["errors"].append(msg)

    # 1. Recall all elements
    q_recall_all = f"{title}: Recall all elements of the sequence."
    a_recall_all = ", ".join(elements) + "."
    _add_card("Basic", {"Front": q_recall_all, "Back": a_recall_all}, "recall-all", "Recall All")

    # 2. Cloze card: Fill one element of the sequence
    cloze_parts = [f"{{{{c{i+1}::{element}}}}}" for i, element in enumerate(elements)]
    cloze_text = f"{title}: Elements: {' '.join(cloze_parts)}."
    _add_card("Cloze", {"Text": cloze_text, "Extra": f"Sequence: {title}"}, "cloze-all", "Cloze All")

    # 3. For each element:
    for i, element in enumerate(elements):
        position = i + 1

        # 3.1 Forward card
        q_fwd = f"{title}: What is element #{position}?"
        _add_card("Basic", {"Front": q_fwd, "Back": element}, "forward", f"Pos {position}")

        # 3.2 Backward card
        q_bwd = f"{title}: What is the position of '{element}'?"
        _add_card("Basic", {"Front": q_bwd, "Back": str(position)}, "backward", f"Element '{element}'")

        # 3.3 Successor card
        if i < len(elements) - 1:
            next_element = elements[i+1]
            q_succ = f"{title}: What comes after '{element}'?"
            _add_card("Basic", {"Front": q_succ, "Back": next_element}, "successor", f"After '{element}'")

        # 3.4 Predecessor card
        if i > 0:
            prev_element = elements[i-1]
            q_pred = f"{title}: What comes before '{element}'?"
            _add_card("Basic", {"Front": q_pred, "Back": prev_element}, "predecessor", f"Before '{element}'")
                
    return results_summary
