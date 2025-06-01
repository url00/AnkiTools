import typer
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table
from typing import Optional

from ...note_transformers.random_basic import transform_notes_to_random_basic
from ...anki_connect import test_connection as test_anki_connection_lib

app = typer.Typer(
    name="transform",
    help="Transform existing Anki notes (e.g., to RandomBasic style)."
)
console = Console()

@app.command("random-basic")
def transform_random_basic_cmd(
    query: Annotated[str, typer.Option("--query", "-q", help="Anki search query to select notes for transformation (required).")],
    prompt_field: Annotated[str, typer.Option(help="Name of the field containing the original prompt (e.g., 'Front').")],
    num_variations: Annotated[int, typer.Option(help="Number of AI-generated rephrased variations.")] = 2,
    max_notes: Annotated[Optional[int], typer.Option(help="Maximum number of notes to process (0 or omit for no limit).")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print changes but don't modify Anki.")] = False,
):
    """
    Transforms 'Basic' model notes matching the given Anki QUERY into 'RandomBasic' style.
    
    It rephrases content from the specified PROMPT_FIELD, combines variations,
    updates the note's model to 'RandomBasic', and updates the field.
    The QUERY must be a valid Anki search string.
    """
    if not test_anki_connection_lib():
        console.print("[bold red]Failed to connect to AnkiConnect.[/bold red] Ensure Anki is running with AnkiConnect addon.")
        raise typer.Exit(code=1)

    console.print(f"Starting 'RandomBasic' transformation for notes matching query '{query}' on field '{prompt_field}'...")
    if dry_run:
        console.print("[yellow]DRY RUN mode enabled. No notes will be actually modified.[/yellow]")

    # Handle max_notes: typer.Option(default=None) is fine, library function expects Optional[int]
    # The original script used 0 for no limit, here None means no limit.
    # We can adjust this in the CLI or library if strict 0 for no limit is desired.
    # For now, None from Typer will correctly mean no limit in the library function.
    # If user explicitly passes --max-notes 0, Typer will pass 0.
    
    max_n = max_notes
    if max_notes is not None and max_notes == 0: # If user explicitly types 0, treat as no limit for library
        max_n = None


    summary = transform_notes_to_random_basic(
        query=query,
        prompt_field_name=prompt_field,
        num_variations=num_variations,
        max_notes_to_process=max_n,
        dry_run=dry_run
    )

    console.print("\n[bold green]--- Transformation Summary ---[/bold green]")
    table = Table(show_header=False, box=None, padding=(0,1))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Query Used:", query)
    table.add_row("Prompt Field:", prompt_field)
    table.add_row("Notes Found by Query:", str(summary.get('notes_found_query', 0)))
    table.add_row("Notes Eligible (Basic model, field exists, not already transformed):", str(summary.get('notes_eligible_for_processing', 0)))
    if dry_run:
        table.add_row("Notes That Would Be Processed Successfully:", str(summary.get('notes_processed_successfully', 0)))
    else:
        table.add_row("Notes Processed Successfully (AI + Anki Update):", str(summary.get('notes_processed_successfully', 0)))
        table.add_row("Notes Actually Updated in Anki:", str(summary.get('notes_updated_anki', 0)))
    
    table.add_row("Skipped (Not 'Basic' model):", str(summary.get('skipped_not_basic_model',0)))
    table.add_row("Skipped (Prompt field missing):", str(summary.get('skipped_field_missing',0)))
    table.add_row("Skipped (Already in RandomBasic format):", str(summary.get('skipped_already_transformed',0)))
    table.add_row("Failed AI Generation:", str(summary.get('failed_ai_generation', 0)))
    table.add_row("Failed Anki Update (after successful AI):", str(summary.get('failed_anki_update', 0)))
    
    errors = summary.get("errors_general", [])
    if errors:
        table.add_row("[bold red]Other Errors Encountered:[/bold red]", str(len(errors)))
        for i, err in enumerate(errors):
            table.add_row(f"  Error {i+1}:", err)
    else:
        table.add_row("Other Errors Encountered:", "0")
        
    console.print(table)

    if not dry_run and summary.get('notes_updated_anki', 0) > 0:
        console.print(f"\n[bold green]Successfully transformed {summary.get('notes_updated_anki',0)} notes.[/bold green]")
    elif dry_run and summary.get('notes_processed_successfully', 0) > 0:
        console.print(f"\n[bold yellow]Dry run complete. {summary.get('notes_processed_successfully',0)} notes would have been processed.[/bold yellow]")
    elif not errors and summary.get('notes_found_query', 0) > 0 :
         console.print("\nNo notes were transformed (they might not be eligible or already processed).")
    elif not errors and summary.get('notes_found_query', 0) == 0:
        console.print("\nNo notes found matching the specified query to process.")


if __name__ == "__main__":
    # For testing: 
    # python -m ankitools_lib.cli.commands.transform_cmds random-basic --query "deck:Test" --prompt-field "Front" --num-variations 1 --max-notes 5 --dry-run
    app()
