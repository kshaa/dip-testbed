package diptestbed.protocol

import io.circe.syntax._
import io.circe.{Decoder, Encoder}
import diptestbed.protocol.Codecs._

sealed trait WebResult[A] {
  val value: A
  implicit val valueEncoder: Encoder[A]
  implicit val valueDecoder: Decoder[A]
}

object WebResult {
  case class Success[A](value: A)(implicit val valueEncoder: Encoder[A], val valueDecoder: Decoder[A])
      extends WebResult[A]
  case class Failure[A](value: A)(implicit val valueEncoder: Encoder[A], val valueDecoder: Decoder[A])
      extends WebResult[A]

  implicit class RichWebResult[A: Encoder: Decoder](webResult: WebResult[A]) {
    def toJsonString: String = webResult.asJson.toString
  }
}
