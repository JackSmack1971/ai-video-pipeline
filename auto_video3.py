import os
import json
from pathlib import Path
import asyncio
from utils import file_operations

from services import generators, idea_generator

from config import load_config, ConfigError

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
LAST_IDEAS_FILE = "last_ideas2.json"
MAX_STORED_IDEAS = 6

def read_file(file_path):
    """Read file content using shared utilities."""
    return asyncio.run(file_operations.read_file(file_path))

def save_file(file_path, content, mode='wb'):
    """Save content using shared utilities."""
    return asyncio.run(file_operations.save_file(file_path, content))

def load_last_ideas():
    """Load the list of recently generated ideas."""
    if os.path.exists(LAST_IDEAS_FILE):
        try:
            with open(LAST_IDEAS_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            # If the file exists but is corrupted, return an empty list
            return []
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
    with open(LAST_IDEAS_FILE, 'w') as file:
        json.dump(ideas, file)

def generate_idea():
    """Generate an idea using the shared service."""
    result = asyncio.run(idea_generator.generate_idea(CONFIG, LAST_IDEAS_FILE))
    save_idea_to_history(result["idea"])
    return result

def generate_second_prompt(idea, first_prompt):
    """Generate a second complementary prompt for the same idea."""
    print("Generating second complementary prompt...")
    
    # Create a prompt to ask for a complementary scene
    second_prompt_request = f"""
    Based on the following idea and first prompt, create a SECOND complementary prompt that shows a different aspect or moment related to the same horror concept.
    
    IDEA: {idea}
    
    FIRST PROMPT: {first_prompt}
    
    Create a SECOND prompt that:
    1. Maintains the same horror concept but shows a different scene/moment
    2. Include captured digitally with examples like "RED Komodo 6K and anamorphic lenses" or "Sony FX9 and vintage cine lenses" or similar professional camera setups
    3. MUST prominently feature a close-up of a woman's face showing intense terror and despair as she encounters or reacts to the horrifying entity/demon/creature
    4. Include specific details about the woman's expressions (e.g., wide eyes, trembling lips, tears streaming down her face)
    5. Uses the same visual style but shows the horrifying entity/creature in frame causing her terror
    6. Would work well as a second scene in a short video about this horror
    7. Has a natural transition potential from/to the first scene
    
    Format your response as a single detailed prompt paragraph only, similar in structure to the first prompt.
    """
    
    # Call OpenAI API
    client = OpenAI(api_key=CONFIG.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": second_prompt_request
            }
        ]
    )
    
    # Get the second prompt
    second_prompt = response.choices[0].message.content.strip()
    
    # Clean up potential formatting
    if second_prompt.startswith("PROMPT:"):
        second_prompt = second_prompt.replace("PROMPT:", "", 1).strip()
    
    print(f"Generated Second Prompt: {second_prompt[:100]}...")
    return second_prompt

def generate_third_prompt(idea, first_prompt, second_prompt):
    """Generate a third complementary prompt for the same idea."""
    print("Generating third complementary prompt...")
    
    # Create a prompt to ask for a third complementary scene
    third_prompt_request = f"""
    Based on the following idea and existing prompts, create a THIRD complementary prompt that shows the final aspect or culmination related to the same horror concept.
    
    IDEA: {idea}
    
    FIRST PROMPT: {first_prompt}
    
    SECOND PROMPT: {second_prompt}
    
    Create a THIRD prompt that:
    1. Maintains the same horror concept but shows the final or climactic scene
    2. Include captured digitally with examples like "RED Komodo 6K and anamorphic lenses" or "Sony FX9 and vintage cine lenses" or similar professional camera setups
    3. MUST feature an intense close-up shot of the woman's face in absolute terror and despair at the climactic moment
    4. Include vivid details of her facial expressions showing pure horror (e.g., bloodshot eyes, mascara-stained tears, contorted features)
    5. Show the horrifying entity/demon/creature in its most terrifying form as it claims its victim
    6. Uses the same visual style as the previous prompts including ultra realistic details
    7. Would work well as the conclusion of a short horror video trilogy
    8. Has a natural transition from the second scene
    9. Provides a shocking and horrifying final revelation
    
    Format your response as a single detailed prompt paragraph only, similar in structure to the previous prompts.
    """
    
    # Call OpenAI API
    client = OpenAI(api_key=CONFIG.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": third_prompt_request
            }
        ]
    )
    
    # Get the third prompt
    third_prompt = response.choices[0].message.content.strip()
    
    # Clean up potential formatting
    if third_prompt.startswith("PROMPT:"):
        third_prompt = third_prompt.replace("PROMPT:", "", 1).strip()
    
    print(f"Generated Third Prompt: {third_prompt[:100]}...")
    return third_prompt

def generate_image(prompt: str) -> str:
    return asyncio.run(generators.generate_image(prompt, CONFIG))

def generate_video(image_path: str, prompt: str) -> str:
    return asyncio.run(generators.generate_video(image_path, prompt, CONFIG))

def generate_music(idea: str) -> str:
    return asyncio.run(generators.generate_music(idea, CONFIG))
def generate_voice_dialog(idea: str) -> dict:
    return asyncio.run(generators.generate_voice_dialog(idea, CONFIG))




def merge_videos(video_paths, music_path, voice_data=None):
    """Merge videos with music and voice dialog using FFMPEG."""
    print(f"Creating final video by merging {len(video_paths)} videos with music and voice...")
    
    # Generate output filename
    output_filename = "final_output.mp4"
    
    # Create a temporary file for concatenation
    with open("temp_list.txt", "w") as f:
        for video_path in video_paths:
            f.write(f"file '{video_path}'\n")
    
    # First concatenate the videos
    concat_output = "temp_concat.mp4"
    concat_cmd = f'ffmpeg -y -f concat -safe 0 -i temp_list.txt -c copy {concat_output}'
    
    print(f"Running video concatenation command: {concat_cmd}")
    concat_result = os.system(concat_cmd)
    
    if concat_result != 0:
        print(f"Error concatenating videos. Exit code: {concat_result}")
        return None
    
    # Now add music and voice to the concatenated video
    ffmpeg_cmd = (
        f'ffmpeg -y -i "{concat_output}" -i "{music_path}" '
    )
    
    # Add voice input if available
    if voice_data and os.path.exists(voice_data["filename"]):
        ffmpeg_cmd += f'-i "{voice_data["filename"]}" '
        # Map all streams - video from first input, music from second, voice from third
        # Apply a 1-second delay to the voice track using the adelay filter
        # Adjust volume levels: music at 0.4 (reduced) and voice at 1.5 (amplified)
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]volume=0.4[music];[2:a]adelay=1000|1000,volume=1.5[voice];[music][voice]amix=inputs=2:duration=longest[a]" '
            f'-map 0:v -map "[a]" -shortest -t 30 '
        )
    else:
        # Just map video and music without voice
        ffmpeg_cmd += f'-map 0:v -map 1:a -shortest -t 30 '
    
    # Finish the command with codec settings and output file
    ffmpeg_cmd += f'-c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
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
    """Main function to run the full content generation pipeline."""
    try:
        # Step 1: Generate idea
        result = generate_idea()
        idea, prompt1 = result["idea"], result["prompt"]
        
        # Step 2: Generate two more complementary prompts
        prompt2 = generate_second_prompt(idea, prompt1)
        prompt3 = generate_third_prompt(idea, prompt1, prompt2)
        
        # Step 3: Generate images for all three prompts
        image_path1 = generate_image(prompt1)
        image_path2 = generate_image(prompt2)
        image_path3 = generate_image(prompt3)

        # Step 4: Generate voice dialog
        voice_data = generate_voice_dialog(idea)
        
        # Step 5: Generate videos from all three images
        video_path1 = generate_video(image_path1, prompt1)
        video_path2 = generate_video(image_path2, prompt2)
        video_path3 = generate_video(image_path3, prompt3)
        
        # Step 6: Generate music
        music_path = generate_music(idea)
        
        print(f"Using video files: {video_path1}, {video_path2}, and {video_path3}")
        print(f"Using music file: {music_path}")
        print(f"Using voice file: {voice_data['filename']}")
        
        # Step 7: Merge videos with music and voice
        video_paths = [video_path1, video_path2, video_path3]
        final_video = merge_videos(video_paths, music_path, voice_data)
        
        print("\nContent Generation Pipeline Complete!")
        print(f"Idea: {idea}")
        print(f"Generated Images: {image_path1}, {image_path2}, and {image_path3}")
        print(f"Generated Videos: {video_path1}, {video_path2}, and {video_path3}")
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
