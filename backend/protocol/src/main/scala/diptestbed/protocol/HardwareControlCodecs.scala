package diptestbed.protocol

import cats.implicits._
import diptestbed.protocol.DomainCodecs._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareControlMessageInternal._
import diptestbed.domain._
import io.circe.generic.semiauto.deriveCodec
import io.circe.syntax._
import io.circe.{Codec, Decoder, Encoder}

object HardwareControlCodecs {
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

  private implicit val controlAuthRequestCodec: Codec[AuthRequest] = deriveCodec[AuthRequest]
  private implicit val controlAuthResultCodec: Codec[AuthResult] = deriveCodec[AuthResult]

  private implicit val hardwareControlMessageInternalEncoder: Encoder[HardwareControlMessageInternal] =
    Encoder.instance {
      case c: AuthResult => NamedMessage("authResult", c.asJson).asJson

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
    case c: AuthRequest => NamedMessage("authRequest", c.asJson).asJson

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
          case "authRequest" =>
            Decoder[AuthRequest].widen[HardwareControlMessageExternalNonBinary].some

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
          case "authResult" => Decoder[AuthResult].widen[HardwareControlMessageInternal].some
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

  implicit val hardwareControlMessageNonBinaryEncoder: Encoder[HardwareControlMessageNonBinary] =
    Encoder.instance {
      case m: HardwareControlMessageExternalNonBinary => m.asJson
      case m: HardwareControlMessageInternal          => m.asJson
    }

  implicit val hardwareControlMessageNonBinaryDecoder: Decoder[HardwareControlMessageNonBinary] =
    Decoder[HardwareControlMessageExternalNonBinary]
      .widen[HardwareControlMessageNonBinary]
      .orElse(Decoder[HardwareControlMessageInternal].widen[HardwareControlMessageNonBinary])

}
