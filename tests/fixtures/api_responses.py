from dataclasses import dataclass

@dataclass
class OpenAIResponse:
    idea: str
    prompt: str

@dataclass
class ReplicateVideoResponse:
    url: str

@dataclass
class ReplicateImageResponse:
    url: str

@dataclass
class SonautoMusicResponse:
    song_paths: list[str]

SUCCESS_IDEA = OpenAIResponse("Test Idea", "A prompt")
ERROR_IDEA = OpenAIResponse("", "")
VIDEO_RESP = ReplicateVideoResponse(url="http://dummy/video.mp4")
IMAGE_RESP = ReplicateImageResponse(url="http://dummy/image.png")
MUSIC_RESP = SonautoMusicResponse(song_paths=["http://dummy/music.mp3"])
