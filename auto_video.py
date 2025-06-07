import os
import base64
import time
import json
import requests
from pathlib import Path
import asyncio
import replicate

from config import load_config, ConfigError
from utils import file_operations
from utils.validation import sanitize_prompt
from utils.api import api_call_with_retry
from exceptions import APIError, FileError
from services import generators

try:
    CONFIG = load_config()
except ConfigError as exc:
    raise SystemExit(str(exc))

os.environ["REPLICATE_API_TOKEN"] = CONFIG.replicate_api_key

# Ensure output directories exist
Path("image").mkdir(exist_ok=True)
Path("video").mkdir(exist_ok=True)
Path("music").mkdir(exist_ok=True)

# Constants for the idea logging system
LAST_IDEAS_FILE = "last_ideas.json"
MAX_STORED_IDEAS = 6

def read_file(file_path: str) -> str:
    """Read file content using secure utilities."""
    return asyncio.run(file_operations.read_file(file_path))

def save_file(file_path: str, content: bytes, mode: str = 'wb') -> None:
    """Securely save content to a file."""
    if mode not in ('wb', 'w'):
        raise FileError('Unsupported file mode')
    asyncio.run(file_operations.save_file(file_path, content))

def load_last_ideas():
    """Load the list of recently generated ideas."""
    if not os.path.exists(LAST_IDEAS_FILE):
        return []
    try:
        data = asyncio.run(file_operations.read_file(LAST_IDEAS_FILE))
        return json.loads(data)
    except (json.JSONDecodeError, FileError):
        return []

def save_idea_to_history(idea):
    """Save an idea to the history file, keeping only the most recent ones."""
    ideas = load_last_ideas()
    
    # Add the new idea
    ideas.append(idea)
    
    # Keep only the most recent MAX_STORED_IDEAS
    if len(ideas) > MAX_STORED_IDEAS:
        ideas = ideas[-MAX_STORED_IDEAS:]
    
    # Save the updated list
    content = json.dumps(ideas)
    asyncio.run(file_operations.save_file(LAST_IDEAS_FILE, content.encode()))

def generate_idea():
    """Step 1: Generate an idea using OpenAI API, avoiding recent ideas."""
    print("Step 1: Generating idea using OpenAI API...")
    
    # Read prompt from idea_gen.txt
    idea_prompt = read_file("prompts/idea_gen.txt")
    
    # Load recently used ideas
    last_ideas = load_last_ideas()
    
    # Add context about avoiding recent ideas if there are any
    if last_ideas:
        avoid_context = "\n\nPlease avoid generating ideas similar to these recently created ones:\n"
        for i, idea in enumerate(last_ideas):
            avoid_context += f"{i+1}. {idea}\n"
        
        # Append the avoidance context to the prompt
        idea_prompt += avoid_context
    
    # Call OpenAI API
    client = OpenAI(api_key=CONFIG.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": idea_prompt
            }
        ]
    )
    
    # Parse the result to get idea and prompt
    result = response.choices[0].message.content
    
    # Parse the result to extract idea and prompt
    # Format expected: "Idea: [idea text]\nPrompt: [prompt text]"
    parts = result.split("Prompt:")
    
    # Clean up the idea text
    idea = parts[0].replace("Idea:", "").strip()
    
    # Remove "Example X:" if present
    if "Example" in idea and ":" in idea.split("Example")[1]:
        # Find where the actual POV text starts
        try:
            example_parts = idea.split(":", 1)
            if len(example_parts) > 1:
                # Take only the part after "Example X:"
                idea = example_parts[1].strip()
        except:
            # If parsing fails, keep the original idea
            pass
    
    # Remove markdown formatting (asterisks for bold/italic)
    idea = idea.replace('*', '')
    # Remove any extra newlines or unnecessary whitespace
    idea = ' '.join(idea.split())
    
    prompt = parts[1].strip() if len(parts) > 1 else ""
    
    print(f"Generated Idea: {idea}")
    print(f"Generated Prompt: {prompt}")
    
    # Save the new idea to history
    save_idea_to_history(idea)
    
    return {"idea": idea, "prompt": prompt}

def generate_image(prompt: str) -> str:
    """Generate an image using the service layer."""
    return asyncio.run(generators.generate_image(prompt, CONFIG))

def generate_video(image_path: str, prompt: str) -> str:
    """Generate a video using the service layer."""
    return asyncio.run(generators.generate_video(image_path, prompt, CONFIG))

def generate_music(idea: str) -> str:
    """Generate music using the service layer."""
    return asyncio.run(generators.generate_music(idea, CONFIG))

def generate_voice_dialog(idea: str) -> dict:
    """Generate voice dialog using the service layer."""
    return asyncio.run(generators.generate_voice_dialog(idea, CONFIG))

def create_final_video(video_path, music_path, idea, voice_data=None):
    """Merge video with music and voice dialog using FFMPEG."""
    print("Creating final video with music and voice...")
    
    # Generate output filename
    output_filename = "final_output.mp4"
    
    # Base FFMPEG command for merging video and music
    ffmpeg_cmd = (
        f'ffmpeg -y -i "{video_path}" -i "{music_path}" '
    )
    
    # Add voice input if available
    if voice_data and os.path.exists(voice_data["filename"]):
        ffmpeg_cmd += f'-i "{voice_data["filename"]}" '
        # Map all streams - video from first input, music from second, voice from third
        # Apply a 1-second delay to the voice track using the adelay filter
        # Adjust volume levels: music at 0.4 (reduced) and voice at 1.5 (amplified)
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]volume=0.4[music];[2:a]adelay=1000|1000,volume=1.5[voice];[music][voice]amix=inputs=2:duration=longest[a]" '
            f'-map 0:v -map "[a]" -shortest -t 10 '
        )
    else:
        # Just map video and music without voice
        ffmpeg_cmd += f'-map 0:v -map 1:a -shortest -t 10 '
    
    # Finish the command with codec settings and output file
    ffmpeg_cmd += f'-c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
    # Print the command for debugging
    print(f"Running FFMPEG command: {ffmpeg_cmd}")
    
    # Execute FFMPEG command
    result = os.system(ffmpeg_cmd)
    
    if result == 0:
        print(f"Final video created successfully: {output_filename}")
        return output_filename
    else:
        print(f"Error creating final video. Exit code: {result}")
        return None

def main():
    """Main function to run the full content generation pipeline."""
    try:
        # Step 1: Generate idea
        result = generate_idea()
        idea, prompt = result["idea"], result["prompt"]
        
        # Step 2: Generate image
        image_path = generate_image(prompt)

        # Step 3: Generate voice dialog
        voice_data = generate_voice_dialog(idea)
        
        # Step 4: Generate video
        video_path = generate_video(image_path, prompt)
        
        # Step 5: Generate music
        music_path = generate_music(idea)
        
        print(f"Using video file: {video_path}")
        print(f"Using music file: {music_path}")
        print(f"Using voice file: {voice_data['filename']}")
        
        # Step 6: Create final video with music and voice
        final_video = create_final_video(video_path, music_path, idea, voice_data)
        
        print("\nContent Generation Pipeline Complete!")
        print(f"Idea: {idea}")
        print(f"Generated Image: {image_path}")
        print(f"Generated Video: {video_path}")
        print(f"Generated Music: {music_path}")
        print(f"Generated Voice: {voice_data['filename']}")
        print(f"Voice Dialog: {voice_data['dialog']} (Voice: {voice_data['voice']})")
        print(f"Final Output: {final_video}")
        
    except Exception as e:
        print(f"Error in content generation pipeline: {str(e)}")
        print("Process failed. Please try running the script again.")

if __name__ == "__main__":
    # Import OpenAI here to avoid potential circular import issues
    from openai import OpenAI
    main()
