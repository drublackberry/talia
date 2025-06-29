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

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert researcher and talent acquisition specialist. "
                "Your task is to provide a comprehensive analysis of a candidate's LinkedIn profile and return the data in a specific JSON format. "
                "The JSON output must contain the following fields: 'candidate_name' (string), 'overall_score' (integer between 0 and 100), and 'summary' (string). "
                "Do not include any text outside of the JSON object."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Please analyze the LinkedIn profile at the following URL: {linkedin_url}. "
                "Based on their profile, generate a professional summary, determine their full name, and provide an overall score reflecting their career achievements and experience. "
                "Return the data in the specified JSON format."
            ),
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
