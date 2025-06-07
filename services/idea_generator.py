import json
import time
from typing import Dict

from config import Config
from utils import file_operations
from utils.api_clients import openai_chat


async def generate_idea(config: Config) -> Dict[str, str]:
    history_file = config.pipeline.history_file
    base = await file_operations.read_file("prompts/idea_gen.txt")
    try:
        history = json.loads(await file_operations.read_file(history_file))
    except Exception:
        history = []
    prompt = base
    if history:
        avoid = "\n\nPlease avoid generating ideas similar to:\n" + "\n".join(
            f"{i+1}. {idea}" for i, idea in enumerate(history)
        )
        prompt += avoid
    response = await openai_chat(prompt, config)
    content = response.choices[0].message.content
    idea_part, _, prompt_part = content.partition("Prompt:")
    idea = " ".join(idea_part.replace("Idea:", "").replace("*", "").split())
    result = {"idea": idea.strip(), "prompt": prompt_part.strip()}
    history.append(result["idea"])
    history = history[-config.pipeline.max_stored_ideas:]
    await file_operations.save_file(history_file, json.dumps(history).encode())
    return result
