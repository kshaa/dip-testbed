"""Typed, auto-coded websocket client definition"""

from typing import TypeVar, Generic, Any
import websockets
from websockets.exceptions import ConnectionClosedError
from codec import Decoder, Encoder
from fp import Option, Either

PI = TypeVar('PI')
PO = TypeVar('PO')


class WebSocket(Generic[PI, PO]):
    """Typed, auto-coded websocket client"""
    url: str
    decoder: Decoder[PI]
    encoder: Encoder[PO]
    socket: Option[Any] = Option.as_none()

    def __init__(self, url: str, decoder: Decoder[PI], encoder: Encoder[PO]):
        self.url = url
        self.encoder = encoder
        self.decoder = decoder

    async def connect(self) -> Option[Exception]:
        """Initialize connection to the websocket server"""
        try:
            # For some reason the `.connect` method isn't detected
            # pylint: disable=E1101
            self.socket = Option.as_some(
                await websockets.connect(self.url))  # type: ignore
            return Option.as_none()
        except Exception as e:
            return Option.as_some(e)

    async def disconnect(self) -> Option[Exception]:
        """Close the connection to the websocket server"""
        if not self.socket.isDefined:
            return Option.as_some(Exception("Already disconnected"))
        try:
            await self.socket.value.close()
            self.socket = Option.as_none()
            return Option.as_none()
        except Exception as e:
            return Option.as_some(e)

    async def rx(self) -> Either[Exception, PI]:
        """Receive and auto-decode message from server"""
        if not self.socket.isDefined:
            return Either.as_left(Exception("Not connected"))
        try:
            data = await self.socket.value.recv()
            message = self.decoder.transform(data)
            if message.isRight:
                return Either.as_right(message.right)
            else:
                return Either.as_left(message.left)
        except ConnectionClosedError as e:
            self.socket = Option.as_none()
            return Either.as_left(e)
        except Exception as e:
            return Either.as_left(e)

    async def tx(self, data: PO) -> Option[Exception]:
        """Transmit and auto-encode message to server"""
        if not self.socket.isDefined:
            return Option.as_some(Exception("Not connected"))
        try:
            message = self.encoder.transform(data)
            self.socket.value.send(message)
            return Option.as_none()
        except Exception as e:
            return Option.as_some(e)
