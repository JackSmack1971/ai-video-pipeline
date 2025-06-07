import asyncio
from typing import Optional

from exceptions import APIError


async def merge_video_audio(
    video_path: str,
    music_path: str,
    voice_path: Optional[str],
    output: str,
    duration: int = 10,
) -> str:
    cmd = f'ffmpeg -y -i "{video_path}" -i "{music_path}" '
    if voice_path:
        cmd += (
            f'-i "{voice_path}" '
            f'-filter_complex "[1:a]volume=0.4[m];[2:a]adelay=1000|1000,volume=1.5[v];[m][v]amix=inputs=2:duration=longest[a]" '
            f'-map 0:v -map "[a]" '
        )
    else:
        cmd += '-map 0:v -map 1:a '
    cmd += (
        f'-shortest -t {duration} -c:v libx264 -c:a aac -b:a 192k "{output}"'
    )
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, err = await process.communicate()
    if process.returncode != 0:
        raise APIError(f"ffmpeg failed: {err.decode()}")
    return output
