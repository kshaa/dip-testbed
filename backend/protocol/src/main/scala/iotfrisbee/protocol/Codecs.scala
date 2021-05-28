package iotfrisbee.protocol

import io.circe.generic.semiauto.deriveCodec
import io.circe.generic.extras.semiauto.deriveUnwrappedCodec
import io.circe.{Codec, Decoder, DecodingFailure, Encoder}
import io.circe.syntax._
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackId, DomainTimeZoneId, Hardware, HardwareId, User, UserId}
import iotfrisbee.protocol.messages.diskGolfTrack.CreateDiskGolfTrack
import iotfrisbee.protocol.messages.hardware.CreateHardware
import iotfrisbee.protocol.messages.http.WebResult.{Failure, Success}
import iotfrisbee.protocol.messages.http.WebResult
import iotfrisbee.protocol.messages.home.{Hello, ServiceStatus}
import iotfrisbee.protocol.messages.user.CreateUser

object Codecs {
  object Domain {
    import cats.implicits._

    implicit val domainTimeZoneIdCodec: Codec[DomainTimeZoneId] = Codec.from(
      _.as[String].flatMap(DomainTimeZoneId.fromString(_).leftMap(x => DecodingFailure(x.getMessage, List.empty))),
      _.value.asJson,
    )
    implicit val userIdCodec: Codec[UserId] = deriveUnwrappedCodec[UserId]
    implicit val userCodec: Codec[User] = deriveCodec[User]
    implicit val diskGolfTrackIdCodec: Codec[DiskGolfTrackId] = deriveUnwrappedCodec[DiskGolfTrackId]
    implicit val diskGolfTrackCodec: Codec[DiskGolfTrack] = deriveCodec[DiskGolfTrack]
    implicit val hardwareIdCodec: Codec[HardwareId] = deriveUnwrappedCodec[HardwareId]
    implicit val hardwareCodec: Codec[Hardware] = deriveCodec[Hardware]
  }

  object Http {
    import cats.syntax.functor._

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
  }

  object Home {
    implicit val helloCodec: Codec[Hello] = Codec.forProduct1[Hello, String]("hello")(Hello)(_.recipient)
    implicit val serviceStatusCodec: Codec[ServiceStatus] = deriveCodec[ServiceStatus]
  }

  object User {
    implicit val createUserCodec: Codec[CreateUser] = deriveCodec[CreateUser]
  }

  object DiskGolfTrack {
    import iotfrisbee.protocol.Codecs.Domain._
    implicit val createDiskGolfTrackCodec: Codec[CreateDiskGolfTrack] = deriveCodec[CreateDiskGolfTrack]
  }

  object Hardware {
    import iotfrisbee.protocol.Codecs.Domain._
    implicit val createHardwareCodec: Codec[CreateHardware] = deriveCodec[CreateHardware]
  }
}
