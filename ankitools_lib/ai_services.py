import google.generativeai as genai
from .config import load_google_api_key # Adjusted import

# Global variable to track if Gemini is configured
_gemini_configured = False

def configure_gemini_globally() -> bool:
    """
    Configures the Google Gemini API with the API key from .env file.
    This function should ideally be called once when the library/application starts.
    Sets a global flag _gemini_configured.

    Returns:
        bool: True if configuration was successful or already configured, False otherwise.
    """
    global _gemini_configured
    if _gemini_configured:
        # print("AI Services: Gemini already configured.") # Optional: for debugging
        return True

    api_key = load_google_api_key()
    if not api_key:
        print("AI Services: Gemini API key not loaded. Cannot configure Gemini.")
        _gemini_configured = False
        return False
    
    try:
        genai.configure(api_key=api_key)
        print("AI Services: Google Gemini configured successfully.")
        _gemini_configured = True
        return True
    except Exception as e:
        print(f"AI Services: Error configuring Google Gemini: {e}")
        _gemini_configured = False
        return False

def _ensure_gemini_configured():
    """Internal helper to ensure Gemini is configured before use."""
    if not _gemini_configured:
        # Attempt to configure if not already done.
        # This provides a fallback but it's better to call configure_gemini_globally() explicitly.
        print("AI Services: Gemini not configured. Attempting to configure now...")
        if not configure_gemini_globally():
            raise RuntimeError("AI Services: Gemini is not configured. Please call configure_gemini_globally() first or check API key.")
    # If already configured or successfully configured now, proceed.


def generate_rephrased_prompts(original_prompt: str, num_variations: int = 2) -> list[str] | None:
    """
    Uses Gemini to generate rephrased versions of an original prompt.

    Args:
        original_prompt (str): The prompt to rephrase.
        num_variations (int, optional): The number of rephrased variations to generate. Defaults to 2.

    Returns:
        list[str] | None: A list of rephrased prompts, or None if an error occurs.
    """
    _ensure_gemini_configured() # Ensure Gemini is ready

    try:
        # Using a specific model version as in the original. Consider making this configurable.
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Updated to a common 'latest' tag
        
        prompt_template = (
            f"Rephrase the following question or statement in {num_variations} different ways, "
            f"maintaining its core meaning. Each rephrased version should be distinct. "
            f"Return only the rephrased versions, each on a new line, without any numbering or prefixes.\n\n"
            f"Original: \"{original_prompt}\"\n\n"
            f"Rephrased versions:"
        )
        
        response = model.generate_content(prompt_template)
        
        if response.parts:
            rephrased_text = response.text.strip()
            variations = [line.strip() for line in rephrased_text.split('\n') if line.strip()]
            
            if len(variations) >= num_variations:
                return variations[:num_variations]
            elif variations:
                print(f"AI Services: Warning - Expected {num_variations} variations, but got {len(variations)}.")
                return variations
            else:
                print(f"AI Services: Error - Gemini returned an empty response for rephrasing: {original_prompt}")
                return None
        else:
            print(f"AI Services: Error - Gemini response was empty or blocked for prompt: {original_prompt}")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                print(f"Prompt Feedback: {response.prompt_feedback}")
            return None

    except Exception as e:
        print(f"AI Services: Error generating rephrased prompts with Gemini: {e}")
        return None

def get_word_description(word: str) -> str | None:
    """
    Uses Gemini to generate a concise description for a given word.

    Args:
        word (str): The word to describe.

    Returns:
        str | None: A concise description of the word, or None if an error occurs.
    """
    _ensure_gemini_configured() # Ensure Gemini is ready

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Consistent model
        prompt = (
            f"Provide a very concise definition or a short descriptive phrase for the word \"{word}\". "
            f"The description should be suitable as a brief hint before seeing the word itself. "
            f"For example, for 'apple', a good description might be 'A common fruit'. "
            f"For 'photosynthesis', 'Process plants use to make food'. "
            f"Return only the description, without any introductory phrases like 'The word means...' or 'Description: '."
        )
        
        response = model.generate_content(prompt)
        
        if response.parts:
            description = response.text.strip()
            if description:
                if description.endswith('.'):
                    description = description[:-1]
                if description and description[0].islower(): 
                    description = description[0].upper() + description[1:]
                return description
            else:
                print(f"AI Services: Gemini returned an empty description for '{word}'.")
                return None
        else:
            print(f"AI Services: Error - Gemini response was empty or blocked for word description: {word}")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                print(f"Prompt Feedback: {response.prompt_feedback}")
            return None
            
    except Exception as e:
        print(f"AI Services: Error generating description for '{word}' with Gemini: {e}")
        return None

# Example usage (can be removed or kept for quick testing of this module)
# if __name__ == '__main__':
#     print("Attempting to configure Gemini...")
#     if configure_gemini_globally():
#         print("\nGemini configured. Attempting to generate rephrased prompts...")
#         test_prompt = "Who discovered penicillin?"
#         rephrased = generate_rephrased_prompts(test_prompt, num_variations=3)
#         if rephrased:
#             print(f"\nOriginal prompt: {test_prompt}")
#             print("Rephrased versions:")
#             for i, p_text in enumerate(rephrased):
#                 print(f"{i+1}. {p_text}")
#         else:
#             print("Failed to generate rephrased prompts.")

#         print("\nAttempting to get word description...")
#         test_word = "ephemeral"
#         desc = get_word_description(test_word)
#         if desc:
#             print(f"Description for '{test_word}': {desc}")
#         else:
#             print(f"Failed to get description for '{test_word}'.")
#     else:
#         print("Failed to configure Gemini.")
