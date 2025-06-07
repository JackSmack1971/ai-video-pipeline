import os
import time
from pathlib import Path
import cv2
import asyncio

from config import load_config, ConfigError
from utils import file_operations
from exceptions import FileError
from services import generators
from utils.validation import validate_file_path

try:
    CONFIG = load_config()
except ConfigError as exc:
    raise SystemExit(str(exc))

os.environ["REPLICATE_API_TOKEN"] = CONFIG.replicate_api_key

# Ensure output directories exist
Path("image").mkdir(exist_ok=True)
Path("video").mkdir(exist_ok=True)
Path("music").mkdir(exist_ok=True)

from utils import file_operations
from exceptions import FileError


def read_file(file_path: str) -> str:
    """Read the content of a file securely."""
    return asyncio.run(file_operations.read_file(file_path))

def save_file(file_path: str, content: bytes, mode: str = 'wb') -> None:
    """Save content to a file securely."""
    if mode not in ('wb', 'w'):
        raise FileError('Unsupported file mode')
    asyncio.run(file_operations.save_file(file_path, content))

def extract_last_frame(video_path, output_path):
    """
    Extract the last frame from a video file and save it as an image.
    
    Args:
        video_path (str): Path to the video file
        output_path (str): Path where the extracted frame will be saved
    """
    # Check if the video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    # Check if video opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return False
    
    # Get total number of frames
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        print(f"Error: No frames found in the video file {video_path}")
        return False
    
    # Set the position to the last frame
    # Note: Setting to total_frames-1 as frame counting starts from 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    
    # Read the last frame
    ret, frame = cap.read()
    
    # Check if frame was successfully read
    if not ret:
        print("Error: Could not read the last frame")
        return False
    
    # Save the frame as an image
    cv2.imwrite(output_path, frame)
    print(f"Last frame successfully saved to {output_path}")
    
    # Release video capture object
    cap.release()

    return True


def generate_video(image_path: str, prompt: str) -> str:
    return asyncio.run(generators.generate_video(image_path, prompt, CONFIG))


def generate_music(prompt: str) -> str:
    return asyncio.run(generators.generate_music(prompt, CONFIG))

def merge_videos(video_paths, music_path):
    """Merge videos with music using FFMPEG."""
    print(f"Creating final video by merging {len(video_paths)} videos with music...")
    
    # Generate output filename
    output_filename = "final_output.mp4"
    
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
    
    # Now add music to the concatenated video
    ffmpeg_cmd = f'ffmpeg -y -i "{concat_output}" -i "{music_path}" -map 0:v -map 1:a -shortest -t 50 -c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
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
        # Use an existing image from the images directory
        first_image_path = "image/music.png"  # Update this path to match your actual image
        
        # Create a default prompt for the video generation
        first_prompt = "music video, cinematic"
        
        print(f"Using existing image: {first_image_path}")
        
        # Step 1: Generate first video from the existing image
        first_video_path = generate_video(first_image_path, first_prompt)
        
        # Step 2: Extract the last frame from the first video
        second_image_path = f"image/last_frame_video1_{int(time.time())}.png"
        extract_last_frame(first_video_path, second_image_path)
        
        # Step 3: Generate second video from the last frame of the first video
        second_video_path = generate_video(second_image_path, first_prompt)
        
        # Step 4: Extract the last frame from the second video
        third_image_path = f"image/last_frame_video2_{int(time.time())}.png"
        extract_last_frame(second_video_path, third_image_path)
        
        # Step 5: Generate third video from the last frame of the second video
        third_video_path = generate_video(third_image_path, first_prompt)
        
        # Step 6: Extract the last frame from the third video
        fourth_image_path = f"image/last_frame_video3_{int(time.time())}.png"
        extract_last_frame(third_video_path, fourth_image_path)
        
        # Step 7: Generate fourth video from the last frame of the third video
        fourth_video_path = generate_video(fourth_image_path, first_prompt)
        
        # Step 8: Extract the last frame from the fourth video
        fifth_image_path = f"image/last_frame_video4_{int(time.time())}.png"
        extract_last_frame(fourth_video_path, fifth_image_path)
        
        # Step 9: Generate fifth video from the last frame of the fourth video
        fifth_video_path = generate_video(fifth_image_path, first_prompt)
        
        # Step 10: Generate music using a prompt
        music_prompt = "country music, female vocals, acoustic guitar, cowboy"
        music_path = generate_music(music_prompt)
        
        print(f"Using video files: {first_video_path}, {second_video_path}, {third_video_path}, {fourth_video_path}, {fifth_video_path}")
        print(f"Using music file: {music_path}")
        
        # Step 11: Merge videos with music
        video_paths = [first_video_path, second_video_path, third_video_path, fourth_video_path, fifth_video_path]
        final_video = merge_videos(video_paths, music_path)
        
        print("\nContent Generation Pipeline Complete!")
        print(f"Input Image: {first_image_path}")
        print(f"Generated Images: {second_image_path}, {third_image_path}, {fourth_image_path}, {fifth_image_path}")
        print(f"Generated Videos: {first_video_path}, {second_video_path}, {third_video_path}, {fourth_video_path}, {fifth_video_path}")
        print(f"Generated Music: {music_path}")
        print(f"Final Output: {final_video}")
        
    except Exception as e:
        print(f"Error in content generation pipeline: {str(e)}")
        print("Process failed. Please try running the script again.")

if __name__ == "__main__":
    main()
