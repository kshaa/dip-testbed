package diptestbed.protocol

import io.circe.generic.semiauto.deriveCodec
import io.circe.generic.extras.semiauto.deriveUnwrappedCodec
import io.circe.{Codec, Decoder, DecodingFailure, Encoder}
import io.circe.syntax._
import cats.implicits._
import diptestbed.domain._
import diptestbed.domain.HardwareControlMessage._
import diptestbed.domain.HardwareSerialMonitorMessage._
import diptestbed.protocol.WebResult._

object Codecs {
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

  private implicit val monitorUnavailableCodec: Codec[MonitorUnavailable] = deriveCodec[MonitorUnavailable]
//  private implicit val serialMessageToAgentCodec: Codec[SerialMessageToAgent] = deriveCodec[SerialMessageToAgent]
//  private implicit val serialMessageToClientCodec: Codec[SerialMessageToClient] = deriveCodec[SerialMessageToClient]

  private implicit val uploadSoftwareRequestCodec: Codec[UploadSoftwareRequest] = deriveCodec[UploadSoftwareRequest]
  private implicit val uploadSoftwareResultCodec: Codec[UploadSoftwareResult] = deriveCodec[UploadSoftwareResult]

  private implicit val serialMonitorRequestCodec: Codec[SerialMonitorRequest] = deriveCodec[SerialMonitorRequest]
  private implicit val serialMonitorRequestStopCodec: Codec[SerialMonitorRequestStop] =
    deriveCodec[SerialMonitorRequestStop]
  private implicit val serialMonitorResultCodec: Codec[SerialMonitorResult] = deriveCodec[SerialMonitorResult]
//  private implicit val serialMonitorMessageToAgentCodec: Codec[SerialMonitorMessageToAgent] =
//    deriveCodec[SerialMonitorMessageToAgent]
//  private implicit val serialMonitorMessageToClientCodec: Codec[SerialMonitorMessageToClient] =
//    deriveCodec[SerialMonitorMessageToClient]
  private implicit val serialMonitorListenersHeartbeatStartCodec: Codec[SerialMonitorListenersHeartbeatStart] =
    deriveCodec[SerialMonitorListenersHeartbeatStart]
  private implicit val serialMonitorListenersHeartbeatPingCodec: Codec[SerialMonitorListenersHeartbeatPing] =
    deriveCodec[SerialMonitorListenersHeartbeatPing]
  private implicit val serialMonitorListenersHeartbeatPongCodec: Codec[SerialMonitorListenersHeartbeatPong] =
    deriveCodec[SerialMonitorListenersHeartbeatPong]
  private implicit val serialMonitorListenersHeartbeatFinishCodec: Codec[SerialMonitorListenersHeartbeatFinish] =
    deriveCodec[SerialMonitorListenersHeartbeatFinish]

  private implicit val pingCodec: Codec[Ping] = deriveCodec[Ping]

  implicit val hardwareControlMessageEncoder: Encoder[HardwareControlMessage] = Encoder.instance {
    case c: UploadSoftwareRequest => NamedMessage("uploadSoftwareRequest", c.asJson).asJson
    case c: UploadSoftwareResult  => NamedMessage("uploadSoftwareResult", c.asJson).asJson

    case c: SerialMonitorRequest         => NamedMessage("serialMonitorRequest", c.asJson).asJson
    case c: SerialMonitorRequestStop     => NamedMessage("serialMonitorRequestStop", c.asJson).asJson
    case c: SerialMonitorResult          => NamedMessage("serialMonitorResult", c.asJson).asJson
    case _: SerialMonitorMessageToAgent  => ??? // Bad practice
    case _: SerialMonitorMessageToClient => ??? // Bad practice
    case c: SerialMonitorListenersHeartbeatStart =>
      NamedMessage("serialMonitorListenersHeartbeatStart", c.asJson).asJson
    case c: SerialMonitorListenersHeartbeatPing => NamedMessage("serialMonitorListenersHeartbeatPing", c.asJson).asJson
    case c: SerialMonitorListenersHeartbeatPong => NamedMessage("SerialMonitorListenersHeartbeatPong", c.asJson).asJson
    case c: SerialMonitorListenersHeartbeatFinish =>
      NamedMessage("SerialMonitorListenersHeartbeatFinish", c.asJson).asJson

    case c: Ping => NamedMessage("ping", c.asJson).asJson
  }
  implicit val hardwareControlMessageDecoder: Decoder[HardwareControlMessage] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareControlMessage]] = m.command match {
          case "uploadSoftwareRequest" => Decoder[UploadSoftwareRequest].widen[HardwareControlMessage].some
          case "uploadSoftwareResult"  => Decoder[UploadSoftwareResult].widen[HardwareControlMessage].some

          case "serialMonitorRequest"        => Decoder[SerialMonitorRequest].widen[HardwareControlMessage].some
          case "serialMonitorRequestStop"    => Decoder[SerialMonitorRequestStop].widen[HardwareControlMessage].some
          case "serialMonitorResult"         => Decoder[SerialMonitorResult].widen[HardwareControlMessage].some
          case "serialMonitorMessageToAgent" => ??? // Bad practice
          case "serialMonitorMessageToClient" => ??? // Bad practice
          case "serialMonitorListenersHeartbeatStart" =>
            Decoder[SerialMonitorListenersHeartbeatStart].widen[HardwareControlMessage].some
          case "serialMonitorListenersHeartbeatPing" =>
            Decoder[SerialMonitorListenersHeartbeatPing].widen[HardwareControlMessage].some
          case "serialMonitorListenersHeartbeatPong" =>
            Decoder[SerialMonitorListenersHeartbeatPong].widen[HardwareControlMessage].some
          case "serialMonitorListenersHeartbeatFinish" =>
            Decoder[SerialMonitorListenersHeartbeatFinish].widen[HardwareControlMessage].some

          case "ping" => Decoder[Ping].widen[HardwareControlMessage].some
          case _      => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }

  implicit val hardwareSerialMonitorMessageEncoder: Encoder[HardwareSerialMonitorMessage] = Encoder.instance {
    case c: MonitorUnavailable    => NamedMessage("monitorUnavailable", c.asJson).asJson
    case _: SerialMessageToAgent  => ??? // Bad practice
    case _: SerialMessageToClient => ??? // Bad practice
  }
  implicit val hardwareSerialMonitorMessageDecoder: Decoder[HardwareSerialMonitorMessage] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareSerialMonitorMessage]] = m.command match {
          case "monitorUnavailable"    => Decoder[MonitorUnavailable].widen[HardwareSerialMonitorMessage].some
//          case "serialMessageToAgent"  => Decoder[SerialMessageToAgent].widen[HardwareSerialMonitorMessage].some
//          case "serialMessageToClient" => Decoder[SerialMessageToClient].widen[HardwareSerialMonitorMessage].some
          case _                       => None
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
}
