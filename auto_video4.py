import os
import json
from pathlib import Path
import asyncio

from config import load_config, ConfigError
from utils import file_operations
from exceptions import FileError
from services import generators

def generate_music(idea: str) -> str:
    return asyncio.run(generators.generate_music(idea, CONFIG))

try:
    CONFIG = load_config()
except ConfigError as exc:
    raise SystemExit(str(exc))

def read_file(file_path: str) -> str:
    """Read the content of a file securely."""
    return asyncio.run(file_operations.read_file(file_path))

def save_file(file_path: str, content: bytes, mode: str = 'wb') -> None:
    """Save content to a file securely."""
    if mode not in ('wb', 'w'):
        raise FileError('Unsupported file mode')
    asyncio.run(file_operations.save_file(file_path, content))

def merge_videos(video_paths, music_path, voice_path):
    """Merge videos with music and voice dialog using FFMPEG."""
    print(f"Creating final video by merging {len(video_paths)} videos with music and voice...")
    
    # Make sure all files exist
    for video_path in video_paths:
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
    
    # Check if music path is valid
    has_music = music_path and os.path.exists(music_path)
    if not has_music:
        print("Warning: Music file not found. Creating video without music.")
    else:
        print(f"Using music file: {music_path}")
    
    # Check if voice path is valid
    has_voice = voice_path and os.path.exists(voice_path)
    if not has_voice:
        print("Warning: Voice file not found. Creating video without narration.")
    else:
        print(f"Using voice file: {voice_path}")
    
    # Generate output filename
    output_filename = "final_output.mp4"
    
    # Create a temporary file for concatenation
    temp_list = "temp_list.txt"
    content = "".join([f"file '{p}'\n" for p in video_paths])
    asyncio.run(file_operations.save_file(temp_list, content.encode()))
    
    # First concatenate the videos
    concat_output = "temp_concat.mp4"
    concat_cmd = f'ffmpeg -y -f concat -safe 0 -i temp_list.txt -c copy {concat_output}'
    
    print(f"Running video concatenation command: {concat_cmd}")
    concat_result = os.system(concat_cmd)
    
    if concat_result != 0:
        print(f"Error concatenating videos. Exit code: {concat_result}")
        return None
    
    # Now add music and voice to the concatenated video
    ffmpeg_cmd = f'ffmpeg -y -i "{concat_output}" '
    
    # Add input files if available
    if has_music:
        ffmpeg_cmd += f'-i "{music_path}" '
    
    if has_voice:
        ffmpeg_cmd += f'-i "{voice_path}" '
    
    # Set up audio filtering based on available inputs
    if has_music and has_voice:
        # Both music and voice available
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]volume=0.4[music];[2:a]adelay=1000|1000,volume=1.5[voice];'
            f'[music][voice]amix=inputs=2:duration=longest[a]" '
            f'-map 0:v -map "[a]" '
        )
    elif has_music:
        # Only music available
        ffmpeg_cmd += f'-filter_complex "[1:a]volume=0.4[a]" -map 0:v -map "[a]" '
    elif has_voice:
        # Only voice available
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]adelay=1000|1000,volume=1.5[a]" '
            f'-map 0:v -map "[a]" '
        )
    else:
        # No audio, just use video
        ffmpeg_cmd += f'-map 0:v '
    
    # Set duration and finishing options
    ffmpeg_cmd += f'-shortest -t 30 -c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
    # Print the command for debugging
    print(f"Running FFMPEG command: {ffmpeg_cmd}")
    
    # Execute FFMPEG command
    result = os.system(ffmpeg_cmd)
    
    # Clean up temporary files
    try:
        os.remove("temp_list.txt")
        os.remove(concat_output)
    except:
        pass
    
    if result == 0:
        print(f"Final video created successfully: {output_filename}")
        return output_filename
    else:
        print(f"Error creating final video. Exit code: {result}")
        return None

def main():
    # Provide the Noppera-bō idea text for music generation
    idea = "The Discordant Paraclete is an ancient, accursed entity chronicled in forbidden religious manuscripts."
    
    # Generate music
    music_path = generate_music(idea)
    
    # Video paths from the previous run
    video_paths = [
        "video/kling_video_1743059223.mp4", 
        "video/kling_video_1743059442.mp4", 
        "video/kling_video_1743059651.mp4"
    ]
    
    # Voice path from the previous run
    voice_path = "voice/openai_voice_1743059216.mp3"
    
    # Merge videos
    final_video = merge_videos(video_paths, music_path, voice_path)
    
    print("\nProcess Complete!")
    if final_video:
        print(f"Final Output: {final_video}")

if __name__ == "__main__":
    main()