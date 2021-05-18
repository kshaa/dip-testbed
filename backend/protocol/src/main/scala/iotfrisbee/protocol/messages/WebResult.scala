package iotfrisbee.protocol.messages

import io.circe.{Encoder, Json}
import io.circe.syntax._

object WebResult {
  type WebResult = Either[Json, Json]

  def fromError[A](error: String): WebResult = Left(error.asJson)
  def fromSuccess[A: Encoder](result: A): WebResult = Right(result.asJson)

  implicit class RichWebResult(webResult: WebResult) {
    def toJsonString: String = webResult.merge.toString
  }
}
