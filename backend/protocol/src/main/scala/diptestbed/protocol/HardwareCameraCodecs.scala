package diptestbed.protocol

import cats.implicits._
import diptestbed.protocol.DomainCodecs._
import diptestbed.domain.HardwareCameraMessage._
import diptestbed.domain._
import io.circe.generic.semiauto.deriveCodec
import io.circe.syntax._
import io.circe.{Codec, Decoder, Encoder}

object HardwareCameraCodecs {

  private implicit val pingCodec: Codec[Ping] = deriveCodec[Ping]

  private implicit val cameraAuthRequestCodec: Codec[AuthRequest] = deriveCodec[AuthRequest]
  private implicit val cameraAuthResultCodec: Codec[AuthResult] = deriveCodec[AuthResult]

  private implicit val cameraUnavailableCodec: Codec[CameraUnavailable] = deriveCodec[CameraUnavailable]
  private implicit val stopBroadcastingCodec: Codec[StopBroadcasting] = deriveCodec[StopBroadcasting]
  private implicit val cameraSubscriptionCodec: Codec[CameraSubscription] = deriveCodec[CameraSubscription]

  implicit val hardwareCameraExternalMessageEncoder: Encoder[HardwareCameraMessageExternal] =
    Encoder.instance {
      case c: AuthRequest         => NamedMessage("authRequest", c.asJson).asJson
      case c: AuthResult          => NamedMessage("authResult", c.asJson).asJson
      case c: CameraUnavailable   => NamedMessage("cameraUnavailable", c.asJson).asJson
      case c: StopBroadcasting    => NamedMessage("stopBroadcasting", c.asJson).asJson
      case c: CameraSubscription  => NamedMessage("cameraSubscription", c.asJson).asJson
      case c: Ping                => NamedMessage("ping", c.asJson).asJson
    }
  implicit val hardwareCameraExternalMessageDecoder: Decoder[HardwareCameraMessageExternal] =
    Decoder[NamedMessage].emap { m =>
      {
        val codec: Option[Decoder[HardwareCameraMessageExternal]] = m.command match {
          case "authRequest"        => Decoder[AuthRequest].widen[HardwareCameraMessageExternal].some
          case "authResult"         => Decoder[AuthResult].widen[HardwareCameraMessageExternal].some
          case "cameraUnavailable"  => Decoder[CameraUnavailable].widen[HardwareCameraMessageExternal].some
          case "stopBroadcasting"   => Decoder[StopBroadcasting].widen[HardwareCameraMessageExternal].some
          case "cameraSubscription" => Decoder[CameraSubscription].widen[HardwareCameraMessageExternal].some
          case "ping"               => Decoder[Ping].widen[HardwareCameraMessageExternal].some
          case _                    => None
        }
        codec.toRight("Unknown command").flatMap(_.decodeJson(m.payload).leftMap(_.message))
      }
    }

}
