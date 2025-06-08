import asyncio
import time
from typing import Dict

from config import Config
from utils import file_operations
from utils.api_clients import openai_chat, openai_speech
from utils.validation import sanitize_prompt


async def generate_voice_dialog(idea: str, config: Config) -> Dict[str, str]:
    idea = sanitize_prompt(idea)
    examples = await file_operations.read_file("prompts/voice_examples.txt")
    prompt = f"Create a brief question for: {idea}\n{examples}"
    chat = await openai_chat(prompt, config)
    content = chat.choices[0].message.content
    fields = {
        k.lower(): v.strip().strip('"')
        for line in content.split("\n") if ':' in line
        for k, v in [line.split(':', 1)]
    }
    dialog = fields.get('dialog', '')
    instructions = fields.get('instructions', 'Speak naturally')
    voice = 'shimmer' if 'shimmer' in fields.get('voice', '').lower() else 'onyx'
    speech = await openai_speech(dialog, voice, instructions, config)
    filename = f"voice/openai_voice_{int(time.time())}.mp3"
    await asyncio.to_thread(speech.stream_to_file, filename)
    return {"filename": filename, "dialog": dialog, "voice": voice, "instructions": instructions}
