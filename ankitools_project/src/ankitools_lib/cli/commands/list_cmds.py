import typer
from rich.console import Console
from rich.table import Table

from ...deck_utils import list_all_deck_names
from ...anki_connect import test_connection as test_anki_connection_lib

app = typer.Typer(name="list", help="List various Anki information (e.g., decks, notes, models).")
console = Console()

@app.command("decks")
def list_decks_cmd():
    """
    Lists all available deck names in your Anki collection.
    """
    if not test_anki_connection_lib():
        console.print("[bold red]Failed to connect to AnkiConnect.[/bold red] Ensure Anki is running with AnkiConnect addon.")
        raise typer.Exit(code=1)
    
    console.print("Fetching deck names...")
    deck_names = list_all_deck_names()

    if deck_names is None:
        console.print("[bold red]Could not retrieve deck names.[/bold red] AnkiConnect request might have failed or an error occurred.")
        raise typer.Exit(code=1)
    elif not deck_names:
        console.print("[yellow]No decks found in your Anki collection.[/yellow]")
    else:
        table = Table(title="Available Anki Decks")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Deck Name", style="cyan")

        for i, deck_name in enumerate(deck_names):
            table.add_row(str(i + 1), deck_name)
        
        console.print(table)

if __name__ == "__main__":
    # For testing this command module directly
    # Example: python -m ankitools_lib.cli.commands.list_cmds decks
    # Requires Anki to be running with AnkiConnect
    app()
