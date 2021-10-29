package iotfrisbee.protocol

import io.circe.generic.semiauto.deriveCodec
import io.circe.generic.extras.semiauto.deriveUnwrappedCodec
import io.circe.{Codec, Decoder, DecodingFailure, Encoder}
import io.circe.syntax._
import cats.implicits._
import iotfrisbee.domain._
import iotfrisbee.domain.HardwareControlMessage._
import iotfrisbee.domain.HardwareSerialMonitorMessage._
import iotfrisbee.protocol.WebResult._

import scala.annotation.unused

object Codecs {
  implicit val domainTimeZoneIdCodec: Codec[DomainTimeZoneId] = Codec.from(
    _.as[String].flatMap(DomainTimeZoneId.fromString(_).leftMap(x => DecodingFailure(x.getMessage, List.empty))),
    _.value.asJson,
  )
  implicit val userIdCodec: Codec[UserId] = deriveUnwrappedCodec[UserId]
  implicit val userCodec: Codec[User] = deriveCodec[User]
  implicit val hardwareIdCodec: Codec[HardwareId] = deriveUnwrappedCodec[HardwareId]
  implicit val hardwareCodec: Codec[Hardware] = deriveCodec[Hardware]
  implicit val hardwareMessageIdCodec: Codec[HardwareMessageId] = deriveUnwrappedCodec[HardwareMessageId]
  implicit val hardwareMessageCodec: Codec[HardwareMessage] = deriveCodec[HardwareMessage]
  implicit val softwareIdCodec: Codec[SoftwareId] = deriveUnwrappedCodec[SoftwareId]
  implicit val softwareMetaCodec: Codec[SoftwareMeta] = deriveCodec[SoftwareMeta]

  implicit val NamedMessageCodec: Codec[NamedMessage] = deriveCodec[NamedMessage]

  @unused private implicit val baudrateStateCodec: Codec[BaudrateState] = deriveCodec[BaudrateState]

  private implicit val serialMessageCodec: Codec[SerialMessage] = deriveCodec[SerialMessage]
  private implicit val monitorUnavailableCodec: Codec[MonitorUnavailable] = deriveCodec[MonitorUnavailable]
  private implicit val baudrateSetCodec: Codec[BaudrateSet] = deriveCodec[BaudrateSet]
  private implicit val baudrateChangedCodec: Codec[BaudrateChanged] = deriveCodec[BaudrateChanged]

  private implicit val uploadSoftwareRequestCodec: Codec[UploadSoftwareRequest] = deriveCodec[UploadSoftwareRequest]
  private implicit val uploadSoftwareResultCodec: Codec[UploadSoftwareResult] = deriveCodec[UploadSoftwareResult]

  implicit def eitherEncoder[A, B](implicit a: Encoder[A], b: Encoder[B]): Encoder[Either[A, B]] = {
    Encoder.instance {
      case Left(x)  => a.apply(x)
      case Right(x) => b.apply(x)
    }
  }
  implicit def eitherDecoder[A, B](implicit a: Decoder[A], b: Decoder[B]): Decoder[Either[A, B]] = {
    val left: Decoder[Either[A, B]] = a.map(Left.apply)
    val right: Decoder[Either[A, B]] = b.map(Right.apply)
    left or right
  }

  private implicit val SerialMonitorRequestCodec: Codec[SerialMonitorRequest] = deriveCodec[SerialMonitorRequest]
  private implicit val SerialMonitorResultCodec: Codec[SerialMonitorResult] = deriveCodec[SerialMonitorResult]
  private implicit val SerialMonitorMessageCodec: Codec[SerialMonitorMessage] = deriveCodec[SerialMonitorMessage]

  private implicit val pingCodec: Codec[Ping] = deriveCodec[Ping]

  implicit val hardwareControlMessageEncoder: Encoder[HardwareControlMessage] = Encoder.instance {
    case c: UploadSoftwareRequest => NamedMessage("uploadSoftwareRequest", c.asJson).asJson
    case c: UploadSoftwareResult  => NamedMessage("uploadSoftwareResult", c.asJson).asJson

    case c: SerialMonitorRequest => NamedMessage("serialMonitorRequest", c.asJson).asJson
    case c: SerialMonitorResult  => NamedMessage("serialMonitorResult", c.asJson).asJson
    case c: SerialMonitorMessage => NamedMessage("serialMonitorMessage", c.asJson).asJson

    case c: Ping => NamedMessage("ping", c.asJson).asJson
  }
  implicit val hardwareControlMessageDecoder: Decoder[HardwareControlMessage] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareControlMessage]] = m.command match {
          case "uploadSoftwareRequest" => Decoder[UploadSoftwareRequest].widen[HardwareControlMessage].some
          case "uploadSoftwareResult"  => Decoder[UploadSoftwareResult].widen[HardwareControlMessage].some

          case "serialMonitorRequest" => Decoder[SerialMonitorRequest].widen[HardwareControlMessage].some
          case "serialMonitorResult"  => Decoder[SerialMonitorResult].widen[HardwareControlMessage].some
          case "serialMonitorMessage" => Decoder[SerialMonitorMessage].widen[HardwareControlMessage].some

          case "ping" => Decoder[Ping].widen[HardwareControlMessage].some
          case _      => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }

  implicit val hardwareSerialMonitorMessageEncoder: Encoder[HardwareSerialMonitorMessage] = Encoder.instance {
    case c: BaudrateSet        => NamedMessage("baudrateSet", c.asJson).asJson
    case c: BaudrateChanged    => NamedMessage("baudrateChanged", c.asJson).asJson
    case c: MonitorUnavailable => NamedMessage("monitorUnavailable", c.asJson).asJson
    case c: SerialMessage      => NamedMessage("serialMessage", c.asJson).asJson
  }
  implicit val hardwareSerialMonitorMessageDecoder: Decoder[HardwareSerialMonitorMessage] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareSerialMonitorMessage]] = m.command match {
          case "baudrateSet"        => Decoder[BaudrateSet].widen[HardwareSerialMonitorMessage].some
          case "baudrateChanged"    => Decoder[BaudrateChanged].widen[HardwareSerialMonitorMessage].some
          case "monitorUnavailable" => Decoder[MonitorUnavailable].widen[HardwareSerialMonitorMessage].some
          case "serialMessage"      => Decoder[SerialMessage].widen[HardwareSerialMonitorMessage].some
          case _                    => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }

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
  implicit val createHardwareMessageCodec: Codec[CreateHardwareMessage] = deriveCodec[CreateHardwareMessage]
}
