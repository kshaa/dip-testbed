"""Typed, auto-coded websocket client definition"""

from pprint import pformat
from typing import TypeVar, Generic, Any, Optional, Union
import websockets.client
import websockets
from websockets.exceptions import ConnectionClosedError
from result import Result, Err
from codec import Decoder, Encoder
import log

LOGGER = log.timed_named_logger("websocket")
SERIALIZABLE = TypeVar('SERIALIZABLE')
PI = TypeVar('PI')
PO = TypeVar('PO')


class WebSocket(Generic[SERIALIZABLE, PI, PO]):
    """Typed, auto-coded websocket client"""
    url: str
    decoder: Decoder[Union[str, bytes], SERIALIZABLE, PI]
    encoder: Encoder[Union[str, bytes], SERIALIZABLE, PO]
    socket: Optional[Any] = None

    def __init__(
        self,
        url: str,
        decoder: Decoder[Union[str, bytes], SERIALIZABLE, PI],
        encoder: Encoder[Union[str, bytes], SERIALIZABLE, PO]
    ):
        self.url = url
        self.encoder = encoder
        self.decoder = decoder

    async def connect(self) -> Optional[Exception]:
        """Initialize connection to the websocket server"""
        try:
            # For some reason the `.connect` method isn't detected
            # pylint: disable=E1101
            self.socket = await websockets.connect(self.url)  # type: ignore
            return None
        except Exception as e:
            return e

    async def disconnect(self) -> Optional[Exception]:
        """Close the connection to the websocket server"""
        if self.socket is None:
            return Exception("Already disconnected")
        try:
            await self.socket.close()  # type: ignore
            self.socket = None
            return None
        except Exception as e:
            return e

    async def rx(self) -> Result[PI, Exception]:
        """Receive and auto-decode message from server"""
        if self.socket is None:
            return Err(Exception("Not connected"))
        try:
            data: Union[str, bytes] = await self.socket.recv()
            LOGGER.debug("Received message: %s", pformat(data, indent=4))
            # This returns CodecParseException, which mypy doesn't recognize
            # as a type of Exception, which is weird, but lets suppress this
            return self.decoder.raw_decode(data)  # type: ignore
        except ConnectionClosedError as e:
            self.socket = None
            return Err(e)
        except Exception as e:
            return Err(e)

    async def tx(self, data: PO) -> Optional[Exception]:
        """Transmit and auto-encode message to server"""
        if self.socket is None:
            return Exception("Not connected")
        try:
            LOGGER.debug("Sending message: %s", pformat(data, indent=4))
            message: Union[str, bytes] = self.encoder.raw_encode(data)
            if isinstance(message, bytes):
                await self.socket.send_binary(message)
            elif isinstance(message, str):
                await self.socket.send(message)
            else:
                return Exception("Unknown message type")
            return None
        except Exception as e:
            return e
