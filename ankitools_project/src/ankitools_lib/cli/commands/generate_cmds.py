import typer
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table
from typing import List, Optional
from pathlib import Path # Added
import click # Added

import sys # For reading from stdin
from ...card_generators.arithmetic import generate_arithmetic_problems, parse_operands_str
from ...card_generators.spelling import generate_spelling_cards_from_file
from ...card_generators.poetry import create_poetry_anki_cards, parse_poem_input
from ...card_generators.sequence import create_sequence_anki_cards, parse_sequence_input
from ...anki_connect import test_connection as test_anki_connection_lib

app = typer.Typer(
    name="generate", 
    help="Generate various types of Anki notes (e.g., arithmetic, spelling)."
)
console = Console()

@app.command("arithmetic")
def generate_arithmetic_cmd(
    deck_name: Annotated[str, typer.Option(help="The name of the Anki deck to add cards to.")],
    operands: Annotated[str, typer.Option(help="A comma-delimited string of numbers (e.g., '3,7,8,9').")],
    operations: Annotated[
        str, typer.Option(help="Type of problems: 'addition', 'multiplication', or 'all'.")
    ] = "all",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print actions but don't modify Anki.")] = False,
):
    """
    Generates Anki cards for arithmetic problems (addition and/or multiplication).
    """
    if not test_anki_connection_lib():
        console.print("[bold red]Failed to connect to AnkiConnect.[/bold red] Ensure Anki is running with AnkiConnect addon.")
        raise typer.Exit(code=1)

    operands_list = parse_operands_str(operands)
    if operands_list is None:
        console.print("[bold red]Invalid operands format.[/bold red] Please use a comma-delimited list of numbers.")
        raise typer.Exit(code=1)
    
    if operations.lower() not in ["addition", "multiplication", "all"]:
        console.print(f"[bold red]Invalid operation type: '{operations}'.[/bold red] Choose from 'addition', 'multiplication', 'all'.")
        raise typer.Exit(code=1)

    console.print(f"Starting arithmetic card generation for deck '{deck_name}'...")
    if dry_run:
        console.print("[yellow]DRY RUN mode enabled. No cards will be actually added.[/yellow]")

    summary = generate_arithmetic_problems(
        deck_name=deck_name,
        operands_list=operands_list,
        operations_to_generate=operations.lower(), # type: ignore
        dry_run=dry_run
    )

    console.print("\n[bold green]--- Generation Summary ---[/bold green]")
    table = Table(show_header=False, box=None)
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Run UUID:", summary.get('run_uuid', 'N/A'))
    table.add_row("Deck Name:", deck_name)
    table.add_row("Operands Processed:", str(operands_list))
    table.add_row("Operations Selected:", operations.lower())
    
    if dry_run:
        table.add_row("Problems That Would Be Generated:", str(summary.get('problems_generated_count', 0)))
        table.add_row("Cards That Would Be Added:", str(summary.get('cards_added', 0)))
    else:
        table.add_row("Unique Problems Considered:", str(summary.get('problems_generated_count', 0)))
        table.add_row("Cards Successfully Added:", str(summary.get('cards_added', 0)))

    errors = summary.get("errors", [])
    if errors:
        table.add_row("[bold red]Errors Encountered:[/bold red]", str(len(errors)))
        for i, err in enumerate(errors):
            table.add_row(f"  Error {i+1}:", err)
    else:
        table.add_row("Errors Encountered:", "0")
        
    console.print(table)

    if not dry_run and summary.get('cards_added', 0) > 0:
        console.print(f"\n[bold green]Successfully completed adding {summary.get('cards_added',0)} arithmetic cards.[/bold green]")
    elif dry_run and summary.get('cards_added', 0) > 0:
        console.print(f"\n[bold yellow]Dry run complete. {summary.get('cards_added',0)} cards would have been added.[/bold yellow]")
    elif not errors:
        console.print("\nNo new cards were added (perhaps all combinations already exist or no valid operations).")


if __name__ == "__main__":
    # For testing: python -m ankitools_lib.cli.commands.generate_cmds arithmetic --deck-name "TestDeck" --operands "1,2,3" --operations "all" --dry-run
    app()

@app.command("spelling")
def generate_spelling_cmd(
    input_file: Annotated[Path, typer.Option(
        help="Path to a newline-delimited text file containing words.",
        click_type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
    )],
    deck_name: Annotated[str, typer.Option(help="The name of the Anki deck to add cards to.")],
    disable_run_tag: Annotated[bool, typer.Option("--disable-run-tag", help="Disable tagging notes with a run-specific UUID.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print actions but don't modify Anki.")] = False,
):
    """
    Generates Anki spelling cards from a file, with syllable clozes and AI descriptions.
    """
    if not test_anki_connection_lib():
        console.print("[bold red]Failed to connect to AnkiConnect.[/bold red] Ensure Anki is running with AnkiConnect addon.")
        raise typer.Exit(code=1)

    console.print(f"Starting spelling card generation for deck '{deck_name}' from file '{input_file}'...")
    if dry_run:
        console.print("[yellow]DRY RUN mode enabled. No cards will be actually added.[/yellow]")

    summary = generate_spelling_cards_from_file(
        input_file_path=str(input_file), # typer.Path gives Path object
        deck_name=deck_name,
        tag_run=not disable_run_tag,
        dry_run=dry_run
    )

    console.print("\n[bold green]--- Generation Summary ---[/bold green]")
    table = Table(show_header=False, box=None)
    table.add_column(style="dim")
    table.add_column()

    if summary.get('run_uuid'):
        table.add_row("Run UUID:", summary.get('run_uuid'))
    table.add_row("Input File:", str(input_file))
    table.add_row("Deck Name:", deck_name)
    table.add_row("Words Processed:", str(summary.get('words_processed', 0)))
    
    if dry_run:
        table.add_row("Cards That Would Be Created:", str(summary.get('notes_created', 0)))
    else:
        table.add_row("Cards Successfully Created:", str(summary.get('notes_created', 0)))
        
    table.add_row("Syllabification Skipped:", str(summary.get('skipped_syllabification', 0)))
    table.add_row("AI Description Skipped (soft fail):", str(summary.get('skipped_ai_description', 0)))
    
    errors = summary.get("errors", [])
    if errors:
        table.add_row("[bold red]Errors Encountered:[/bold red]", str(len(errors)))
        for i, err in enumerate(errors):
            table.add_row(f"  Error {i+1}:", err)
    else:
        table.add_row("Errors Encountered:", "0")
        
    console.print(table)

    if not dry_run and summary.get('notes_created', 0) > 0:
        console.print(f"\n[bold green]Successfully completed creating {summary.get('notes_created',0)} spelling cards.[/bold green]")
    elif dry_run and summary.get('notes_created', 0) > 0:
        console.print(f"\n[bold yellow]Dry run complete. {summary.get('notes_created',0)} cards would have been created.[/bold yellow]")
    elif not errors:
        console.print("\nNo new cards were created (perhaps no words in file or other non-error condition).")

@app.command("poetry")
def generate_poetry_cmd(
    deck_name: Annotated[str, typer.Option(help="The Anki deck to add cards to.")],
    input_file: Annotated[Optional[Path], typer.Option(
        help="Path to a text file containing the poem (Title, Author, Lines...). Reads from stdin if not provided.",
        click_type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
    )] = None,
    disable_run_tag: Annotated[bool, typer.Option("--disable-run-tag", help="Disable tagging notes with a run-specific UUID.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print actions but don't modify Anki.")] = False,
):
    """
    Generates Anki cards for a poem, line by line with context.
    Input format (file or stdin):
    Line 1: Poem Title
    Line 2: Poem Author
    Line 3..N: Poem lines
    """
    if not test_anki_connection_lib():
        console.print("[bold red]Failed to connect to AnkiConnect.[/bold red] Ensure Anki is running with AnkiConnect addon.")
        raise typer.Exit(code=1)

    lines: List[str] = []
    source_name = ""
    if input_file:
        source_name = f"file '{str(input_file)}'"
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines:
                console.print(f"[bold red]Input {source_name} is empty or contains no processable lines.[/bold red]")
                raise typer.Exit(code=1)
        except FileNotFoundError: # Should be caught by typer.Path(exists=True) but good to have.
            console.print(f"[bold red]Error: Input {source_name} not found.[/bold red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[bold red]Error reading input {source_name}: {e}[/bold red]")
            raise typer.Exit(code=1)
    else:
        source_name = "stdin"
        console.print("No input file provided. Reading poem from stdin (Title, Author, then lines). Press Ctrl+D (Unix) or Ctrl+Z then Enter (Windows) to end input.")
        try:
            stdin_lines = sys.stdin.readlines()
            lines = [line.strip() for line in stdin_lines if line.strip()]
        except Exception as e:
            console.print(f"[bold red]Error reading from stdin: {e}[/bold red]")
            raise typer.Exit(code=1)
        if not lines:
            console.print("[bold red]No input provided via stdin.[/bold red]")
            raise typer.Exit(code=1)

    title, author, poem_lines_content, parse_error = parse_poem_input(lines)

    if parse_error:
        console.print(f"[bold red]Input Error from {source_name}: {parse_error}[/bold red]")
        console.print("Expected format:\nLine 1: Poem Title\nLine 2: Poem Author\nLine 3..N: Poem lines")
        raise typer.Exit(code=1)
    
    # Type assertion for mypy, as parse_error being None implies title, author, poem_lines_content are not None
    assert title is not None
    assert author is not None
    
    console.print(f"Starting poetry card generation for '{title}' by {author} in deck '{deck_name}'...")
    if dry_run:
        console.print("[yellow]DRY RUN mode enabled. No cards will be actually added.[/yellow]")

    summary = create_poetry_anki_cards(
        deck_name=deck_name,
        title=title,
        author=author,
        poem_lines=poem_lines_content,
        tag_run=not disable_run_tag,
        dry_run=dry_run
    )

    console.print("\n[bold green]--- Generation Summary ---[/bold green]")
    table = Table(show_header=False, box=None, padding=(0,1))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Poem Title:", summary.get('title', 'N/A'))
    table.add_row("Author:", summary.get('author', 'N/A'))
    if summary.get('run_uuid'):
        table.add_row("Run UUID:", summary.get('run_uuid'))
    table.add_row("Lines Processed:", str(summary.get('lines_processed', 0)))
    
    if dry_run:
        table.add_row("Cards That Would Be Created:", str(summary.get('notes_created', 0)))
    else:
        table.add_row("Cards Successfully Created:", str(summary.get('notes_created', 0)))
        
    errors = summary.get("errors", [])
    if errors:
        table.add_row("[bold red]Errors Encountered:[/bold red]", str(len(errors)))
        for i, err in enumerate(errors):
            table.add_row(f"  Error {i+1}:", err)
    else:
        table.add_row("Errors Encountered:", "0")
        
    console.print(table)

    if not dry_run and summary.get('notes_created', 0) > 0:
        console.print(f"\n[bold green]Successfully completed creating {summary.get('notes_created',0)} poetry cards.[/bold green]")
    elif dry_run and summary.get('notes_created', 0) > 0:
        console.print(f"\n[bold yellow]Dry run complete. {summary.get('notes_created',0)} cards would have been created.[/bold yellow]")
    elif not errors:
        console.print("\nNo new cards were created.")

@app.command("sequence")
def generate_sequence_cmd(
    deck_name: Annotated[str, typer.Option(help="The Anki deck to add cards to.")],
    input_file: Annotated[Optional[Path], typer.Option(
        help="Path to a text file containing the sequence (Title, then Elements...). Reads from stdin if not provided.",
        click_type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
    )] = None,
    disable_run_tag: Annotated[bool, typer.Option("--disable-run-tag", help="Disable tagging notes with a run-specific UUID.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print actions but don't modify Anki.")] = False,
):
    """
    Generates various Anki cards for memorizing a sequence.
    Input format (file or stdin):
    Line 1: Sequence Title
    Line 2..N: Sequence elements (one per line)
    """
    if not test_anki_connection_lib():
        console.print("[bold red]Failed to connect to AnkiConnect.[/bold red] Ensure Anki is running with AnkiConnect addon.")
        raise typer.Exit(code=1)

    lines: List[str] = []
    source_name = ""
    if input_file:
        source_name = f"file '{str(input_file)}'"
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f] # Keep empty lines if user intends them as part of sequence? Original script stripped and filtered. Let's stick to that.
                lines = [line for line in lines if line] # Filter out empty lines after stripping
            if not lines:
                console.print(f"[bold red]Input {source_name} is empty or contains no processable lines.[/bold red]")
                raise typer.Exit(code=1)
        except FileNotFoundError:
            console.print(f"[bold red]Error: Input {source_name} not found.[/bold red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[bold red]Error reading input {source_name}: {e}[/bold red]")
            raise typer.Exit(code=1)
    else:
        source_name = "stdin"
        console.print("No input file provided. Reading sequence from stdin (Title, then elements). Press Ctrl+D (Unix) or Ctrl+Z then Enter (Windows) to end input.")
        try:
            stdin_lines = sys.stdin.readlines()
            lines = [line.strip() for line in stdin_lines if line.strip()]
        except Exception as e:
            console.print(f"[bold red]Error reading from stdin: {e}[/bold red]")
            raise typer.Exit(code=1)
        if not lines:
            console.print("[bold red]No input provided via stdin.[/bold red]")
            raise typer.Exit(code=1)

    title, elements, parse_error = parse_sequence_input(lines)

    if parse_error:
        console.print(f"[bold red]Input Error from {source_name}: {parse_error}[/bold red]")
        console.print("Expected format:\nLine 1: Sequence Title\nLine 2..N: Sequence elements (one per line)")
        raise typer.Exit(code=1)
    
    assert title is not None # For mypy, parse_error being None implies title is not None
    
    console.print(f"Starting sequence card generation for '{title}' ({len(elements)} elements) in deck '{deck_name}'...")
    if dry_run:
        console.print("[yellow]DRY RUN mode enabled. No cards will be actually added.[/yellow]")

    summary = create_sequence_anki_cards(
        deck_name=deck_name,
        title=title,
        elements=elements,
        tag_run=not disable_run_tag,
        dry_run=dry_run
    )

    console.print("\n[bold green]--- Generation Summary ---[/bold green]")
    table = Table(show_header=False, box=None, padding=(0,1))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Sequence Title:", summary.get('title', 'N/A'))
    if summary.get('run_uuid'):
        table.add_row("Run UUID:", summary.get('run_uuid'))
    table.add_row("Number of Elements:", str(summary.get('elements_count', 0)))
    
    if dry_run:
        table.add_row("Cards That Would Be Created:", str(summary.get('notes_created', 0)))
    else:
        table.add_row("Cards Successfully Created:", str(summary.get('notes_created', 0)))
        
    errors = summary.get("errors", [])
    if errors:
        table.add_row("[bold red]Errors Encountered:[/bold red]", str(len(errors)))
        for i, err in enumerate(errors):
            table.add_row(f"  Error {i+1}:", err)
    else:
        table.add_row("Errors Encountered:", "0")
        
    console.print(table)

    if not dry_run and summary.get('notes_created', 0) > 0:
        console.print(f"\n[bold green]Successfully completed creating {summary.get('notes_created',0)} sequence cards.[/bold green]")
    elif dry_run and summary.get('notes_created', 0) > 0:
        console.print(f"\n[bold yellow]Dry run complete. {summary.get('notes_created',0)} cards would have been created.[/bold yellow]")
    elif not errors:
        console.print("\nNo new cards were created.")
