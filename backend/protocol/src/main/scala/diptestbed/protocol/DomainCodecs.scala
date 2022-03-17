package diptestbed.protocol

import cats.implicits._
import diptestbed.domain._
import diptestbed.protocol.WebResult._
import io.circe.generic.extras.semiauto.deriveUnwrappedCodec
import io.circe.generic.semiauto.deriveCodec
import io.circe.syntax._
import io.circe.{Codec, Decoder, DecodingFailure, Encoder}

object DomainCodecs {
  implicit val domainTimeZoneIdCodec: Codec[DomainTimeZoneId] = Codec.from(
    _.as[String].flatMap(DomainTimeZoneId.fromString(_).leftMap(x => DecodingFailure(x.getMessage, List.empty))),
    _.value.asJson,
  )
  implicit val userIdCodec: Codec[UserId] = deriveUnwrappedCodec[UserId]
  implicit val userCodec: Codec[User] = deriveCodec[User]
  implicit val hardwareIdCodec: Codec[HardwareId] = deriveUnwrappedCodec[HardwareId]
  implicit val hardwareCodec: Codec[Hardware] = deriveCodec[Hardware]
  implicit val softwareIdCodec: Codec[SoftwareId] = deriveUnwrappedCodec[SoftwareId]
  implicit val softwareMetaCodec: Codec[SoftwareMeta] = deriveCodec[SoftwareMeta]
  implicit val namedMessageCodec: Codec[NamedMessage] = deriveCodec[NamedMessage]
  implicit val serialConfigCodec: Codec[SerialConfig] = deriveCodec[SerialConfig]
  implicit val unitCodec: Codec[Unit] = deriveCodec[Unit]


  implicit def webResultSuccessCodec[A: Encoder: Decoder]: Codec[Success[A]] =
    Codec.forProduct1[Success[A], A]("success")(Success(_))(_.value)
  implicit def webResultFailureCodec[A: Encoder: Decoder]: Codec[Failure[A]] =
    Codec.forProduct1[Failure[A], A]("failure")(Failure(_))(_.value)
  protected def webResultEncoder[A: Encoder: Decoder]: Encoder[WebResult[A]] =
    Encoder.instance {
      case success: Success[A] => success.asJson
      case failure: Failure[A] => failure.asJson
    }
  protected def webResultDecoder[A: Encoder: Decoder]: Decoder[WebResult[A]] =
    List[Decoder[WebResult[A]]](
      Decoder[Success[A]].widen,
      Decoder[Failure[A]].widen,
    ).reduceLeft(_ or _)
  implicit def webResultCodec[A: Encoder: Decoder]: Codec[WebResult[A]] =
    Codec.from(webResultDecoder, webResultEncoder)

  implicit val helloCodec: Codec[Hello] = Codec.forProduct1[Hello, String]("hello")(Hello)(_.recipient)
  implicit val serviceStatusCodec: Codec[ServiceStatus] = deriveCodec[ServiceStatus]
  implicit val createUserCodec: Codec[CreateUser] = deriveCodec[CreateUser]
  implicit val createHardwareCodec: Codec[CreateHardware] = deriveCodec[CreateHardware]
}
