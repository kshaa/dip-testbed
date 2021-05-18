package iotfrisbee.protocol

import io.circe.generic.semiauto.deriveCodec
import io.circe.Codec
import iotfrisbee.domain.{User, UserId}
import iotfrisbee.protocol.messages.WebResult.WebResult
import iotfrisbee.protocol.messages.{Hello, ServiceStatus}

object Codecs {
  implicit val userIdCodec: Codec[UserId] = deriveCodec[UserId]
  implicit val userCodec: Codec[User] = deriveCodec[User]
  implicit val serviceStatusCodec: Codec[ServiceStatus] = deriveCodec[ServiceStatus]
  implicit val helloCodec: Codec[Hello] = Codec.forProduct1[Hello, String]("hello")(Hello)(_.recipient)
  implicit val resultCodec: Codec[WebResult] = Codec.codecForEither("error", "result")
}
