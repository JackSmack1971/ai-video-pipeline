from __future__ import annotations

import asyncio
from typing import AsyncIterator

import boto3
from botocore.exceptions import BotoCoreError

from exceptions import ServiceError
from utils.api import api_call_with_retry

from ..media_repository import MediaRepository


class S3MediaRepository(MediaRepository):
    """Media storage backed by S3."""

    def __init__(self, bucket: str, prefix: str = "") -> None:
        self._bucket = bucket
        self._prefix = prefix
        self._client = boto3.client("s3")

    async def _put(self, key: str, body: bytes) -> None:
        await asyncio.to_thread(self._client.put_object, Bucket=self._bucket, Key=key, Body=body)

    async def _get(self, key: str) -> bytes:
        resp = await asyncio.to_thread(self._client.get_object, Bucket=self._bucket, Key=key)
        return await asyncio.to_thread(resp["Body"].read)

    async def save_media(self, path: str, data: AsyncIterator[bytes]) -> str:
        key = f"{self._prefix}{path}"
        buf = bytearray()
        async for chunk in data:
            buf.extend(chunk)
        try:
            await api_call_with_retry("s3_put", lambda: self._put(key, bytes(buf)))
            return path
        except BotoCoreError as exc:
            raise ServiceError(str(exc)) from exc

    async def load_media(self, path: str) -> AsyncIterator[bytes]:
        key = f"{self._prefix}{path}"
        try:
            data = await api_call_with_retry("s3_get", lambda: self._get(key))
        except BotoCoreError as exc:
            raise ServiceError(str(exc)) from exc
        yield data
