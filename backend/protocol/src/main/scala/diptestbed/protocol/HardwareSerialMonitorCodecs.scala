package diptestbed.protocol

import cats.implicits._
import diptestbed.protocol.DomainCodecs._
import diptestbed.domain.HardwareSerialMonitorMessageNonBinary._
import diptestbed.domain._
import io.circe.generic.semiauto.deriveCodec
import io.circe.syntax._
import io.circe.{Codec, Decoder, Encoder}

object HardwareSerialMonitorCodecs {
  private implicit val monitorUnavailableCodec: Codec[MonitorUnavailable] = deriveCodec[MonitorUnavailable]
  private implicit val connectionClosedCodec: Codec[ConnectionClosed] = deriveCodec[ConnectionClosed]
  private implicit val authResultCodec: Codec[AuthResult] = deriveCodec[AuthResult]

  implicit val hardwareSerialMonitorMessageNonBinaryEncoder: Encoder[HardwareSerialMonitorMessageNonBinary] =
    Encoder.instance {
      case c: AuthResult => NamedMessage("authResult", c.asJson).asJson
      case c: MonitorUnavailable => NamedMessage("monitorUnavailable", c.asJson).asJson
      case c: ConnectionClosed => NamedMessage("connectionClosed", c.asJson).asJson
    }
  implicit val hardwareSerialMonitorMessageNonBinaryDecoder: Decoder[HardwareSerialMonitorMessageNonBinary] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareSerialMonitorMessageNonBinary]] = m.command match {
          case "authResult" => Decoder[AuthResult].widen[HardwareSerialMonitorMessageNonBinary].some
          case "monitorUnavailable" => Decoder[MonitorUnavailable].widen[HardwareSerialMonitorMessageNonBinary].some
          case "connectionClosed" => Decoder[ConnectionClosed].widen[HardwareSerialMonitorMessageNonBinary].some
          case _                    => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }
}
