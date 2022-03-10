#!/usr/bin/env python
import asyncio
from dataclasses import dataclass
from subprocess import Popen
from typing import List, Optional, Union
import aiohttp
from aiohttp import ClientSession, ClientResponse
from result import Result, Err, Ok
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.existing_file_path import ExistingFilePath
from src.service.managed_url import ManagedURL, ManagedURLBuildError
from src.util import log
from src.util.sh import src_relative_path, runnable_sh

LOGGER = log.timed_named_logger("video_stream")
VLC_SHELL_PATH = 'static/vlc/stream.sh'


@dataclass
class VideoStreamConfig:
    pass

    def to_url(self) -> Result[ManagedURL, ManagedURLBuildError]:
        pass


@dataclass
class ExistingStreamConfig(VideoStreamConfig):
    url: ManagedURL
    def to_url(self) -> Result[ManagedURL, ManagedURLBuildError]:
        return Ok(self.url)


@dataclass
class VLCStreamConfig(VideoStreamConfig):
    video_vlc: str
    audio_device: str
    video_device: ExistingFilePath
    video_width: int
    video_height: int
    video_buffer_size: int
    audio_sample_rate: int
    audio_buffer_size: int
    port: int

    @staticmethod
    def build(
        video_vlc: Optional[str],
        audio_device: Optional[str],
        video_device: ExistingFilePath,
        video_width: int,
        video_height: int,
        video_buffer_size: Optional[int],
        audio_sample_rate: Optional[int],
        audio_buffer_size: Optional[int],
        port: Optional[int]
    ):
        return VLCStreamConfig(
            video_vlc if video_vlc is not None else "vlc",
            audio_device if audio_device is not None else "",
            video_device,
            video_width,
            video_height,
            video_buffer_size if video_buffer_size is not None else 50,
            audio_sample_rate if audio_sample_rate is not None else 44100,
            audio_buffer_size if audio_buffer_size is not None else 50,
            port if port is not None else 8081,
        )

    def vlc_shell_args(self: 'VLCStreamConfig') -> List[str]:
        vlc_script_path = src_relative_path(VLC_SHELL_PATH)
        return [
            "bash",
            "-c",
            f"{vlc_script_path} "
            f"-r \"{self.video_vlc}\" "
            f"-z \"{self.audio_device}\" "
            f"-d \"{self.video_device.value}\" "
            f"-w \"{self.video_width}\" "
            f"-h \"{self.video_height}\" "
            f"-v \"{self.video_buffer_size}\" "
            f"-s \"{self.audio_sample_rate}\" "
            f"-a \"{self.audio_buffer_size}\" "
            f"-p \"{self.port}\" "
        ]

    def to_url(self) -> Result['ManagedURL', 'ManagedURLBuildError']:
        return ManagedURL.build(f"http://localhost:{self.port}/webcam.ogg")


@dataclass
class ManagedVideoStream:
    config: VideoStreamConfig
    process: Optional[Popen]
    session: ClientSession
    connection: ClientResponse

    @staticmethod
    async def spawn_stream(config: VideoStreamConfig) -> Result['ManagedVideoStream', DIPClientError]:
        # Spawn process
        process = None
        if isinstance(config, VLCStreamConfig):
            arguments = config.vlc_shell_args()
            start_result = runnable_sh(arguments)
            if isinstance(start_result, Err):
                return Err(GenericClientError(start_result.value))
            process = start_result.value
            await asyncio.sleep(1)

        # Create stream HTTP connection
        try:
            session = aiohttp.ClientSession()
        except Exception as e:
            if process is not None:
                process.terminate()
            return Err(GenericClientError(f"Failed to create HTTP session, reason: {e}"))
        url_result: Union[Ok[ManagedURL], Err[ManagedURLBuildError]] = config.to_url()
        if isinstance(url_result, Err):
            return Err(GenericClientError(f"Failed to construct stream URL: ${url_result.value}"))
        url_text_result = url_result.value.text()
        if isinstance(url_text_result, Err):
            return Err(GenericClientError(f"Failed to construct stream URL: ${url_text_result.value}"))
        url_text = url_text_result.value
        try:
            response = await session.get(url_text)
        except Exception as e:
            if process is not None:
                process.terminate()
            return Err(GenericClientError(f"Failed to create HTTP connection, reason: {e}"))
        if response.status < 200 or response.status >= 300:
            return Err(GenericClientError(f"Failed to create HTTP connection, reason: {response.status}, {response.reason}"))

        return Ok(ManagedVideoStream(config, process, session, response))

    async def read_chunk(self) -> Result[bytes, DIPClientError]:
        try:
            (bytes, is_last_chunk) = await self.connection.content.readchunk()
            if is_last_chunk:
                return Err(GenericClientError("End of video stream"))
            return Ok(bytes)
        except Exception as e:
            return Err(GenericClientError(f"Video stream chunk read failed, reason: {e}"))

    async def end(self):
        try:
            if self.connection is not None:
                self.connection.close()
            if self.session is not None:
                await self.session.close()
            if self.process is not None:
                self.process.terminate()
        except Exception as e:
            LOGGER.error(f"Failed to stop managed video stream, reason: {e}")