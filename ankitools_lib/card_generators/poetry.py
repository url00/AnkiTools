# ankitools_lib/card_generators/poetry.py
"""
This module provides functions for generating Anki cards for memorizing poetry.
"""

import uuid
from typing import List, Dict, Any, Tuple, Optional

from ..anki_connect import add_note as anki_add_note, AnkiConnectError

def parse_poem_input(lines: List[str]) -> Tuple[Optional[str], Optional[str], List[str], Optional[str]]:
    """
    Parses raw input lines into a title, author, and list of poem lines.

    The expected format is:
    - Line 1: Poem Title
    - Line 2: Poem Author
    - Lines 3 to N: The lines of the poem.

    Args:
        lines: A list of strings from the input file or stdin.

    Returns:
        A tuple containing:
        - The poem title (str)
        - The poem author (str)
        - A list of the poem's lines (List[str])
        - An error message (str) if parsing fails, otherwise None.
    """
    if len(lines) < 3:
        return None, None, [], "Input format error: Expected title, author, and at least one line of the poem."
    
    title = lines[0]
    author = lines[1]
    poem_lines_content = lines[2:]
    
    if not title.strip():
        return None, None, [], "Title cannot be empty."
    if not author.strip():
        return None, None, [], "Author cannot be empty."
    if not poem_lines_content or not any(line.strip() for line in poem_lines_content):
        return None, None, [], "Poem must have at least one line."
        
    return title.strip(), author.strip(), [line.strip() for line in poem_lines_content if line.strip()], None


def create_poetry_anki_cards(
    deck_name: str,
    title: str,
    author: str,
    poem_lines: List[str],
    tag_run: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Generates Anki cards for a given poem and adds them to the specified deck.
    Each card prompts for the next line of the poem, providing the previous one or
    two lines as context.

    Args:
        deck_name: The name of the Anki deck to add the cards to.
        title: The title of the poem.
        author: The author of the poem.
        poem_lines: A list of strings, where each string is a line of the poem.
        tag_run: Whether to tag the created notes with a unique run UUID.
        dry_run: If True, simulates the process without creating notes in Anki.

    Returns:
        A dictionary summarizing the operation, including the number of notes
        created and any errors.
    """
    results_summary = {
        "title": title,
        "author": author,
        "lines_processed": len(poem_lines),
        "notes_created": 0,
        "run_uuid": None,
        "errors": []
    }

    if not poem_lines:
        results_summary["errors"].append("No poem lines provided.")
        return results_summary

    run_uuid_str = None
    if tag_run:
        run_uuid_str = str(uuid.uuid4())
        results_summary["run_uuid"] = run_uuid_str
        print(f"Tagging poetry notes for '{title}' with UUID: {run_uuid_str}")

    if dry_run:
        print(f"DRY RUN: Processing poem '{title}' by {author} for deck '{deck_name}'. No cards will be added.")

    # Iterate through each line of the poem to create a card for it.
    for i, current_line in enumerate(poem_lines):
        if not current_line.strip():
            continue

        # Determine the context to show on the front of the card.
        context_display_lines = []
        if i == 0:
            # For the first line, show a simple prompt.
            question_front = "<i>Beginning</i><br>..."
        elif i == 1:
            # For the second line, show the first line as context.
            context_display_lines.append(poem_lines[0])
            question_front = f"<i>Beginning</i><br>{'<br>'.join(context_display_lines)}<br>..."
        else:
            # For subsequent lines, show the previous two lines as context.
            context_display_lines.append(poem_lines[i-2])
            context_display_lines.append(poem_lines[i-1])
            question_front = f"{'<br>'.join(context_display_lines)}<br>..."
        
        answer_back = current_line
        
        fields = {"Front": question_front, "Back": answer_back}
        tags = ["ankitools-generated", "poetry"]
        if run_uuid_str:
            tags.append(run_uuid_str)

        if dry_run:
            print(f"  DRY-RUN: Would add POETRY card for line {i+1}:")
            print(f"    Front: {question_front}")
            print(f"    Back: {answer_back}")
            print(f"    Tags: {tags}")
            results_summary["notes_created"] += 1
        else:
            try:
                note_id = anki_add_note(deck_name, "Basic", fields, tags)
                if note_id:
                    results_summary["notes_created"] += 1
                else:
                    results_summary["errors"].append(f"Failed to add card for line {i+1} of '{title}'")
            except AnkiConnectError as e:
                results_summary["errors"].append(f"AnkiConnect error for line {i+1} of '{title}': {e}")
            except Exception as e:
                results_summary["errors"].append(f"Unexpected error for line {i+1} of '{title}': {e}")
                
    return results_summary
