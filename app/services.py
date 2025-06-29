import os
from openai import OpenAI
import httpx
from flask import current_app

def get_profile_from_linkedin_url(linkedin_url: str, project_prompt: str, research_model: str): 
    """
    Gets a user's profile from a LinkedIn URL using the Perplexity API.

    Args:
        linkedin_url: The URL of the LinkedIn profile.

    Returns:
        A string containing the user's profile information.
    """
    api_key = current_app.config.get('PERPLEXITY_API_KEY')
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY not set in the application configuration.")

    # Explicitly create an httpx client to handle proxy settings correctly.
    # This will respect HTTP_PROXY and HTTPS_PROXY environment variables.
    # Set a longer timeout to accommodate potentially long-running research tasks
    http_client = httpx.Client(timeout=120.0)

    client = OpenAI(
        api_key=api_key, 
        base_url=current_app.config['PERPLEXITY_API_BASE'],
        http_client=http_client
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert researcher. "
                "Provide a structured JSON response with four fields: 'candidate_name', 'overall_score', 'summary', and 'full_report'. "
                "The 'candidate_name' should be the full name of the person. "
                "The 'overall_score' should be an integer between 0 and 100, representing the candidate's suitability based on the project requirements. "
                "The 'summary' should be a very concise, one or two-sentence overview of the candidate's profile. "
                "The 'full_report' should be a detailed analysis of the candidate's profile, highlighting their skills, experience, and suitability for the role described in the project requirements."
            ),
        },
        {
            "role": "user",
            "content": f"""Project Requirements:\n{project_prompt}\n\n---\n\nResearch the following LinkedIn profile:\n{linkedin_url}"""
        },
    ]

    import json
    print("--- PROMPT SENT TO PERPLEXITY API ---")
    print(json.dumps(messages, indent=2))
    print("-------------------------------------")

    response = client.chat.completions.create(
        model=research_model,
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content
