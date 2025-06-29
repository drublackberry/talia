import os
from openai import OpenAI
import httpx

def get_profile_from_linkedin_url(linkedin_url: str, research_model: str = 'sonar-deep-research'):
    """
    Gets a user's profile from a LinkedIn URL using the Perplexity API.

    Args:
        linkedin_url: The URL of the LinkedIn profile.

    Returns:
        A string containing the user's profile information.
    """
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        # In a production app, you might want to return a more user-friendly error
        # or have a fallback mechanism.
        raise ValueError("PERPLEXITY_API_KEY environment variable not set.")

    # Explicitly create an httpx client to handle proxy settings correctly.
    # This will respect HTTP_PROXY and HTTPS_PROXY environment variables.
    http_client = httpx.Client()

    client = OpenAI(
        api_key=api_key, 
        base_url="https://api.perplexity.ai",
        http_client=http_client
    )

    system_prompt = (
        "You are an expert researcher. Your task is to provide a detailed and comprehensive professional profile "
        "based on the provided LinkedIn URL. The profile should include the person's full name, current role, "
        "company, a summary of their experience, key skills, and education. "
        "Present the information in a clear, well-structured format."
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"Please generate a profile for the person at this LinkedIn URL: {linkedin_url}",
        },
    ]

    stream = client.chat.completions.create(
        model=research_model,
        messages=messages,
        stream=True,
    )
    try:
        for chunk in stream:
            yield chunk
    except Exception as e:
        print(f"An error occurred while streaming from the Perplexity API: {e}")
        raise e
