"""Typed, auto-coded websocket client definition"""

from pprint import pformat
from typing import TypeVar, Generic, Any, Optional, Union
import websockets.client
import websockets
from websockets.exceptions import ConnectionClosedError
from result import Result, Err

from src.domain.sensitive_message import SensitiveMessage
from src.protocol.codec import Decoder, Encoder
from src.service.managed_url import ManagedURL
from src.util import log

LOGGER = log.timed_named_logger("websocket")
PI = TypeVar('PI')
PO = TypeVar('PO')


class SocketInterface(Generic[PI, PO]):
    """Interface for interactions w/ sockets"""
    def connected(self) -> bool:
        pass

    async def connect(self) -> Optional[Exception]:
        pass

    async def disconnect(self) -> Optional[Exception]:
        pass

    async def rx(self) -> Result[PI, Exception]:
        pass

    async def tx(self, data: PO) -> Optional[Exception]:
        pass


class WebSocket(SocketInterface[PI, PO]):
    """Typed, auto-coded websocket client"""
    url: ManagedURL
    decoder: Decoder[Union[str, bytes], PI]
    encoder: Encoder[Union[str, bytes], PO]
    socket: Optional[Any] = None

    def __init__(
        self,
        url: ManagedURL,
        decoder: Decoder[Union[str, bytes], PI],
        encoder: Encoder[Union[str, bytes], PO]
    ):
        self.url = url
        self.encoder = encoder
        self.decoder = decoder

    def connected(self) -> bool:
        return self.socket is not None

    async def connect(self) -> Optional[Exception]:
        """Initialize connection to the websocket server"""
        if self.connected():
            return Exception("Already connected")
        try:
            # For some reason the `.connect` method isn't detected
            # pylint: disable=E1101
            url_text_result = self.url.text()
            if isinstance(url_text_result, Err):
                return Exception(f"Failed to serialize connection URL, reason: {url_text_result.value}")
            LOGGER.debug(f"Websocket connecting: {url_text_result}")
            self.socket = await websockets.connect(url_text_result.value)  # type: ignore
            return None
        except Exception as e:
            return e

    async def disconnect(self) -> Optional[Exception]:
        """Close the connection to the websocket server"""
        if not self.connected():
            return Exception("Already disconnected")
        try:
            await self.socket.close()  # type: ignore
            self.socket = None
            return None
        except Exception as e:
            return e

    async def rx(self) -> Result[PI, Exception]:
        """Receive and auto-decode message from server"""
        if not self.connected():
            return Err(Exception("Not connected"))
        try:
            data: Union[str, bytes] = await self.socket.recv()
            LOGGER.debug("Received raw message: %s", pformat(data, indent=4))
            # This returns CodecParseException, which mypy doesn't recognize
            # as a type of Exception, which is weird, but lets suppress this
            return self.decoder.decode(data)  # type: ignore
        except ConnectionClosedError as e:
            self.socket = None
            return Err(e)
        except Exception as e:
            return Err(e)

    async def tx(self, data: PO) -> Optional[Exception]:
        """Transmit and auto-encode message to server"""
        if not self.connected():
            return Exception("Not connected")
        try:
            LOGGER.debug("Sending domain message: %s", pformat(data, indent=4))
            message: Union[str, bytes] = self.encoder.encode(data)
            if isinstance(data, SensitiveMessage):
                LOGGER.debug("Sending raw sensitive message: <redacted>")
            else:
                LOGGER.debug("Sending raw message: %s", pformat(message, indent=4))
            await self.socket.send(message)
            return None
        except Exception as e:
            return e
