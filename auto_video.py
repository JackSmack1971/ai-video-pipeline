import os
import asyncio
import json
from pathlib import Path

from config import load_config, ConfigError
from utils import file_operations
from exceptions import FileError
from services import generators, idea_generator
from utils.media_processing import merge_video_audio

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


def create_final_video(video_path, music_path, idea, voice_data=None):
    """Merge media files asynchronously using FFMPEG."""
    voice = voice_data["filename"] if voice_data else None
    try:
        return asyncio.run(
            merge_video_audio(video_path, music_path, voice, "final_output.mp4")
        )
    except Exception as exc:
        print(f"Error creating final video: {exc}")
        return None

def main():
    """Main function to run the full content generation pipeline."""
    try:
        # Step 1: Generate idea
        result = asyncio.run(idea_generator.generate_idea(CONFIG))
        idea, prompt = result["idea"], result["prompt"]

        image_path = asyncio.run(generators.generate_image(prompt, CONFIG))
        voice_data = asyncio.run(generators.generate_voice_dialog(idea, CONFIG))
        video_path = asyncio.run(generators.generate_video(image_path, prompt, CONFIG))
        music_path = asyncio.run(generators.generate_music(idea, CONFIG))
        
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
    main()
