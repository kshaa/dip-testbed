"""Typed, auto-coded websocket client definition"""

from typing import TypeVar, Generic, Any, Optional
import websockets
from websockets.exceptions import ConnectionClosedError
from result import Result, Err
from codec import Decoder, Encoder

PI = TypeVar('PI')
PO = TypeVar('PO')


class WebSocket(Generic[PI, PO]):
    """Typed, auto-coded websocket client"""
    url: str
    decoder: Decoder[PI]
    encoder: Encoder[PO]
    socket: Optional[Any] = None

    def __init__(self, url: str, decoder: Decoder[PI], encoder: Encoder[PO]):
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
            data = await self.socket.recv()
            # This returns CodecParseException, which mypy doesn't recognize
            # as a type of Exception, which is weird, but lets suppress this
            return self.decoder.transform(data)  # type: ignore
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
            message = self.encoder.transform(data)
            self.socket.send(message)
            return None
        except Exception as e:
            return e
