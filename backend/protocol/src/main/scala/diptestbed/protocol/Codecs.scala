package diptestbed.protocol

import io.circe.generic.semiauto.deriveCodec
import io.circe.generic.extras.semiauto.deriveUnwrappedCodec
import io.circe.{Codec, Decoder, DecodingFailure, Encoder}
import io.circe.syntax._
import cats.implicits._
import diptestbed.domain.HardwareCameraMessage.{Ping => CameraPing, CameraSubscription, CameraUnavailable, StopBroadcasting}
import diptestbed.domain._
import diptestbed.domain.HardwareControlMessageInternal._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareSerialMonitorMessageNonBinary._
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

  implicit val unitCodec: Codec[Unit] = deriveCodec[Unit]


  private implicit val monitorUnavailableCodec: Codec[MonitorUnavailable] = deriveCodec[MonitorUnavailable]
  private implicit val connectionClosedCodec: Codec[ConnectionClosed] = deriveCodec[ConnectionClosed]

  private implicit val uploadSoftwareRequestCodec: Codec[UploadSoftwareRequest] = deriveCodec[UploadSoftwareRequest]
  private implicit val uploadSoftwareResultCodec: Codec[UploadSoftwareResult] = deriveCodec[UploadSoftwareResult]

  private implicit val serialMonitorRequestCodec: Codec[SerialMonitorRequest] = deriveCodec[SerialMonitorRequest]
  private implicit val serialMonitorRequestStopCodec: Codec[SerialMonitorRequestStop] =
    deriveCodec[SerialMonitorRequestStop]
  private implicit val serialMonitorResultCodec: Codec[SerialMonitorResult] = deriveCodec[SerialMonitorResult]
  private implicit val serialMonitorListenersHeartbeatStartCodec: Codec[SerialMonitorListenersHeartbeatStart] =
    deriveCodec[SerialMonitorListenersHeartbeatStart]
  private implicit val serialMonitorListenersHeartbeatPingCodec: Codec[SerialMonitorListenersHeartbeatPing] =
    deriveCodec[SerialMonitorListenersHeartbeatPing]
  private implicit val serialMonitorListenersHeartbeatPongCodec: Codec[SerialMonitorListenersHeartbeatPong] =
    deriveCodec[SerialMonitorListenersHeartbeatPong]
  private implicit val serialMonitorListenersHeartbeatFinishCodec: Codec[SerialMonitorListenersHeartbeatFinish] =
    deriveCodec[SerialMonitorListenersHeartbeatFinish]
  private implicit val serialMonitorUnavailableCodec: Codec[SerialMonitorUnavailable] =
    deriveCodec[SerialMonitorUnavailable]
  private implicit val startLifecycleCodec: Codec[StartLifecycle] = deriveCodec[StartLifecycle]
  private implicit val endLifecycleCodec: Codec[EndLifecycle] = deriveCodec[EndLifecycle]

  private implicit val pingCodec: Codec[Ping] = deriveCodec[Ping]

  private implicit val hardwareControlMessageInternalEncoder: Encoder[HardwareControlMessageInternal] =
    Encoder.instance {
      case c: StartLifecycle => NamedMessage("startLifecycle", c.asJson).asJson
      case c: EndLifecycle   => NamedMessage("endLifecycle", c.asJson).asJson

      case c: SerialMonitorRequestStop => NamedMessage("serialMonitorRequestStop", c.asJson).asJson
      case c: SerialMonitorListenersHeartbeatStart =>
        NamedMessage("serialMonitorListenersHeartbeatStart", c.asJson).asJson
      case c: SerialMonitorListenersHeartbeatPing =>
        NamedMessage("serialMonitorListenersHeartbeatPing", c.asJson).asJson
      case c: SerialMonitorListenersHeartbeatFinish =>
        NamedMessage("serialMonitorListenersHeartbeatFinish", c.asJson).asJson
    }

  private implicit val hardwareControlMessageExternalNonBinaryEncoder
    : Encoder[HardwareControlMessageExternalNonBinary] = Encoder.instance {
    case c: UploadSoftwareRequest => NamedMessage("uploadSoftwareRequest", c.asJson).asJson
    case c: UploadSoftwareResult  => NamedMessage("uploadSoftwareResult", c.asJson).asJson

    case c: SerialMonitorRequest                => NamedMessage("serialMonitorRequest", c.asJson).asJson
    case c: SerialMonitorResult                 => NamedMessage("serialMonitorResult", c.asJson).asJson
    case c: SerialMonitorListenersHeartbeatPong => NamedMessage("serialMonitorListenersHeartbeatPong", c.asJson).asJson
    case c: SerialMonitorUnavailable            => NamedMessage("monitorUnavailable", c.asJson).asJson

    case c: Ping => NamedMessage("ping", c.asJson).asJson
  }

  private implicit val hardwareControlMessageExternalNonBinaryDecoder
    : Decoder[HardwareControlMessageExternalNonBinary] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareControlMessageExternalNonBinary]] = m.command match {
          case "uploadSoftwareRequest" =>
            Decoder[UploadSoftwareRequest].widen[HardwareControlMessageExternalNonBinary].some
          case "uploadSoftwareResult" =>
            Decoder[UploadSoftwareResult].widen[HardwareControlMessageExternalNonBinary].some

          case "serialMonitorRequest" =>
            Decoder[SerialMonitorRequest].widen[HardwareControlMessageExternalNonBinary].some
          case "serialMonitorResult" => Decoder[SerialMonitorResult].widen[HardwareControlMessageExternalNonBinary].some
          case "serialMonitorListenersHeartbeatPong" =>
            Decoder[SerialMonitorListenersHeartbeatPong].widen[HardwareControlMessageExternalNonBinary].some
          case "monitorUnavailable" =>
            Decoder[SerialMonitorUnavailable].widen[HardwareControlMessageExternalNonBinary].some

          case "ping" => Decoder[Ping].widen[HardwareControlMessageExternalNonBinary].some
          case _      => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }

  private implicit val hardwareControlMessageInternalDecoder: Decoder[HardwareControlMessageInternal] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareControlMessageInternal]] = m.command match {
          case "startLifecycle" => Decoder[StartLifecycle].widen[HardwareControlMessageInternal].some
          case "endLifecycle"   => Decoder[EndLifecycle].widen[HardwareControlMessageInternal].some
          case "serialMonitorRequestStop" =>
            Decoder[SerialMonitorRequestStop].widen[HardwareControlMessageInternal].some
          case "serialMonitorListenersHeartbeatStart" =>
            Decoder[SerialMonitorListenersHeartbeatStart].widen[HardwareControlMessageInternal].some
          case "serialMonitorListenersHeartbeatPing" =>
            Decoder[SerialMonitorListenersHeartbeatPing].widen[HardwareControlMessageInternal].some
          case "serialMonitorListenersHeartbeatFinish" =>
            Decoder[SerialMonitorListenersHeartbeatFinish].widen[HardwareControlMessageInternal].some
          case _ => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }

  implicit val hardwareSerialMonitorMessageNonBinaryEncoder: Encoder[HardwareSerialMonitorMessageNonBinary] =
    Encoder.instance {
      case c: MonitorUnavailable => NamedMessage("monitorUnavailable", c.asJson).asJson
      case c: ConnectionClosed => NamedMessage("connectionClosed", c.asJson).asJson
    }
  implicit val hardwareSerialMonitorMessageNonBinaryDecoder: Decoder[HardwareSerialMonitorMessageNonBinary] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareSerialMonitorMessageNonBinary]] = m.command match {
          case "monitorUnavailable" => Decoder[MonitorUnavailable].widen[HardwareSerialMonitorMessageNonBinary].some
          case "connectionClosed" => Decoder[ConnectionClosed].widen[HardwareSerialMonitorMessageNonBinary].some
          case _                    => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }

  implicit val hardwareControlMessageNonBinaryEncoder: Encoder[HardwareControlMessageNonBinary] =
    Encoder.instance {
      case m: HardwareControlMessageExternalNonBinary => m.asJson
      case m: HardwareControlMessageInternal          => m.asJson
    }

  implicit val hardwareControlMessageNonBinaryDecoder: Decoder[HardwareControlMessageNonBinary] =
    Decoder[HardwareControlMessageExternalNonBinary]
      .widen[HardwareControlMessageNonBinary]
      .orElse(Decoder[HardwareControlMessageInternal].widen[HardwareControlMessageNonBinary])


  private implicit val cameraUnavailableCodec: Codec[CameraUnavailable] = deriveCodec[CameraUnavailable]
  private implicit val stopBroadcastingCodec: Codec[StopBroadcasting] = deriveCodec[StopBroadcasting]
  private implicit val cameraSubscriptionCodec: Codec[CameraSubscription] = deriveCodec[CameraSubscription]
  private implicit val cameraPingCodec: Codec[CameraPing] = deriveCodec[CameraPing]
  implicit val hardwareCameraExternalMessageEncoder: Encoder[HardwareCameraMessageExternal] =
    Encoder.instance {
      case c: CameraUnavailable   => NamedMessage("cameraUnavailable", c.asJson).asJson
      case c: StopBroadcasting    => NamedMessage("stopBroadcasting", c.asJson).asJson
      case c: CameraSubscription  => NamedMessage("cameraSubscription", c.asJson).asJson
      case c: CameraPing          => NamedMessage("ping", c.asJson).asJson
    }
  implicit val hardwareCameraExternalMessageDecoder: Decoder[HardwareCameraMessageExternal] =
    Decoder[NamedMessage].emap { m =>
    {
      val codec: Option[Decoder[HardwareCameraMessageExternal]] = m.command match {
        case "cameraUnavailable"  => Decoder[CameraUnavailable].widen[HardwareCameraMessageExternal].some
        case "stopBroadcasting"   => Decoder[StopBroadcasting].widen[HardwareCameraMessageExternal].some
        case "cameraSubscription" => Decoder[CameraSubscription].widen[HardwareCameraMessageExternal].some
        case "ping"               => Decoder[CameraPing].widen[HardwareCameraMessageExternal].some
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
}
