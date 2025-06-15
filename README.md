# AnkiTools

AnkiTools is a Python-based library and Command Line Interface (CLI) designed to automate common Anki tasks, enhance note creation, and help manage Anki decks more efficiently. It leverages AI capabilities (via Google Gemini) for certain features, such as generating descriptions for spelling words or rephrasing existing notes.

This tool is intended for Anki users who are comfortable with the command line and want to streamline their card creation process.

## Features

- **Generate Arithmetic Cards:** Quickly create cards for addition and multiplication problems.
- **Generate Spelling Cards:** Create spelling cards from a list of words, complete with syllable-based clozes and AI-generated definitions.
- **Generate Poetry Cards:** Create line-by-line cards for memorizing poetry.
- **Generate Sequence Cards:** Create cards for memorizing ordered sequences of items.
- **Transform Existing Notes:** Convert standard "Basic" notes into a "RandomBasic" format, where the prompt is rephrased in multiple ways by an AI to aid in generalization.
- **List Decks:** List all available decks in your Anki collection.

## Installation

1.  **Prerequisites:**

    - You must have [Anki](https://apps.ankiweb.net/) installed and running on your computer.
    - You must have the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed in Anki.
    - For the `transform random-basic` command, you must have the [Randomized Cards](https://ankiweb.net/shared/info/171015247) note type installed.
    - You will need a Google Gemini API key. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).

2.  **Installation:**

    - Install AnkiTools using `pip`:
      ```bash
      pip install .
      ```

3.  **Configuration:**
    - AnkiTools requires your Gemini API key to be set as an environment variable. Create a file named `.env` in the `ankitools_project` directory and add the following line:
      ```
      GEMINI_API_KEY="YOUR_API_KEY"
      ```
      Replace `"YOUR_API_KEY"` with your actual Gemini API key.

## Usage

All commands are accessed through the `ankitools` CLI. You can see a full list of commands by running:

```bash
ankitools --help
```

### Examples

#### Listing Decks

To see all the decks in your Anki collection:

```bash
ankitools list decks
```

#### Generating Spelling Cards

Create a file named `words.txt` with one word per line:

```
onomatopoeia
photosynthesis
ubiquitous
```

Then, run the following command to generate spelling cards in a deck named "English Vocabulary":

```bash
ankitools generate spelling --deck "English Vocabulary" --input-file words.txt
```

**Output:** This will create new notes in your "English Vocabulary" deck. Each note will have:

- The word on the front.
- The word with syllable clozes on the back (e.g., `pho-to-syn-the-sis`).
- An AI-generated definition of the word.

#### Transforming Notes to `RandomBasic`

If you have a deck of "Basic" notes and you want to rephrase the prompts to help with memorization, you can use the `transform random-basic` command.

For example, to transform all notes in the "History Facts" deck, where the prompt is in the "Front" field:

```bash
ankitools transform random-basic --query "deck:'History Facts'" --prompt-field "Front"
```

**Output:** This will find all the notes in the "History Facts" deck, take the content from the "Front" field, generate two AI-powered rephrasings of it, and then update the note to use the "RandomBasic" note type, with the original prompt and the new variations.

## Development

This project uses `pyproject.toml` for dependency management and packaging. To install the project in an editable mode for development, run:

```bash
pip install -e .
```

## License

This project is licensed under the MIT License.

## Acknowledgements

The poetry and sequence generation features were inspired by Fernando Borretti's excellent collection of spaced repetition tools, which can be found [here](https://github.com/eudoxia0/spaced-repetition-tools).

This project was developed with the assistance of Cline powered by Google's Gemini model gemini-2.5-pro-preview-06-05.
