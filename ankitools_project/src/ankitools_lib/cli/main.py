import typer
from typing_extensions import Annotated # For Typer >=0.7 for Optional typer.Option defaults
import logging

# Assuming your library's __init__ might expose version or other info
from .. import __version__ as lib_version # Relative import from parent package
from ..ai_services import configure_gemini_globally # To configure AI early
from ..anki_connect import test_connection as test_anki_connection # To test Anki connection

# Import command modules here once they are created
# from .commands import generate_cmds, list_cmds, transform_cmds

app = typer.Typer(
    name="ankitools",
    help="A CLI for automating Anki tasks and enhancing note creation with AI.",
    add_completion=False, # Disable shell completion for now, can be enabled later
    no_args_is_help=True, # Show help if no command is given
)

# Global state or context if needed, e.g., for verbose mode
# class CLIGlobalState:
#     verbose: bool = False
# cli_state = CLIGlobalState()


def version_callback(value: bool):
    if value:
        print(f"AnkiTools CLI version: {lib_version}") # Using library version
        raise typer.Exit()

@app.callback()
def main_callback(
    ctx: typer.Context,
    # verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output.")] = False,
    version: Annotated[
        bool, typer.Option("--version", callback=version_callback, is_eager=True, help="Show the version and exit.")
    ] = False,
):
    """
    AnkiTools: Automate and enhance your Anki workflow.
    """
    # if verbose:
    #     cli_state.verbose = True
    #     # Configure logging level if using logging module
    #     logging.basicConfig(level=logging.DEBUG)
    #     print("Verbose mode enabled.")
    # else:
    #     logging.basicConfig(level=logging.INFO)
    
    # It's good practice to configure services early if they are globally needed.
    # However, some commands might not need AI or Anki, so this could be conditional
    # or handled within specific command groups/callbacks.
    # For now, let's attempt to configure Gemini globally.
    # Anki connection test can be a dedicated command or part of commands that need it.
    
    # Suppressing print output from configure_gemini_globally for cleaner CLI startup
    # Actual errors will still print from the function itself.
    # If a command *requires* Gemini, it should check the return status or handle exceptions.
    _ = configure_gemini_globally()


# Register command groups from other files
# app.add_typer(generate_cmds.app, name="generate", help="Generate various types of Anki notes.")
# app.add_typer(list_cmds.app, name="list", help="List Anki information (e.g., decks).")
# app.add_typer(transform_cmds.app, name="transform", help="Transform existing Anki notes.")


# A simple command to test Anki connection directly from the CLI
@app.command()
def check_anki_connection():
    """
    Tests the connection to the AnkiConnect service.
    """
    print("Attempting to connect to AnkiConnect...")
    if test_anki_connection():
        print("AnkiConnect connection successful.")
    else:
        print("Failed to connect to AnkiConnect. Ensure Anki is running with AnkiConnect addon.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    # This allows running the CLI for development by executing this file directly.
    # e.g., python -m ankitools_lib.cli.main --help
    # However, the entry point in pyproject.toml (`ankitools = "ankitools_lib.cli.main:app"`)
    # is what makes it runnable as `ankitools` after installation.
    app()
