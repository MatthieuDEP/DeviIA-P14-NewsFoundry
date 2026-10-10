"""Agent Mistral et conversion de l'historique PydanticAI pour l'interface."""

import os
from datetime import timezone

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

SYSTEM_PROMPT = """Tu es NewsFoundry, un assistant de discussion et de revue de presse.
Réponds en français, de manière claire, concise et factuelle. Utilise le contexte
de la discussion et pose une question de clarification lorsque c'est nécessaire.
Tu peux utiliser du Markdown simple pour structurer les réponses.
N'invente jamais de sources, de citations, de chiffres ni de dates.
À cette étape tu n'as pas d'accès au web ni à une source d'actualités en temps réel.
Si une question exige des informations récentes que tu ne peux pas vérifier,
indique cette limite et distingue les informations connues des hypothèses.
"""

chat_agent = Agent(
    f"mistral:{os.getenv('MISTRAL_MODEL') or 'ministral-8b-latest'}",
    system_prompt=SYSTEM_PROMPT,
    defer_model_check=True,
    model_settings={"timeout": 45, "max_tokens": 2048},
    retries=0,
)


def public_messages(history):
    """Ne transmettre que les messages visibles, pas les prompts système ou tools."""
    messages = []
    for message in history:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                    messages.append({"role": "user", "content": part.content, "timestamp": part.timestamp})
        elif isinstance(message, ModelResponse):
            content = "\n\n".join(part.content for part in message.parts if isinstance(part, TextPart))
            if content:
                messages.append({"role": "assistant", "content": content, "timestamp": message.timestamp})
    return messages


def as_utc(value):
    # SQLite ne conserve pas le fuseau ; PostgreSQL utilise une colonne timezone.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
