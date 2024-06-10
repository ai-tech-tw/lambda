from random import choice
from openai import OpenAI
from config import (
    openai_base_url,
    openai_api_key,
    openai_model,
)

# OpenAI config
openai_client = OpenAI(
    base_url=openai_base_url,
    api_key=openai_api_key,
)


def chat_with_ai(user_text):
    # Generate completion using OpenAI
    completion = openai_client.chat.completions.create(
        model=openai_model,
        messages=[
            {
                "role": "user",
                "content": user_text,
            },
        ],
    )

    # Extract the completion from OpenAI
    completion_choice = choice(completion.choices)
    return completion_choice.message.content
