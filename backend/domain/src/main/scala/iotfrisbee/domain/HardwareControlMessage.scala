package iotfrisbee.domain

import iotfrisbee.domain.HardwareSerialMonitorMessage.SerialMessage

sealed trait HardwareControlMessage {}
object HardwareControlMessage {
  type Baudrate = Int
  case class BaudrateState(baudrate: Baudrate, isNew: Boolean)

  case class UploadSoftwareRequest(softwareId: SoftwareId) extends HardwareControlMessage
  case class UploadSoftwareResult(error: Option[String]) extends HardwareControlMessage
  case class SerialMonitorRequest(baudrate: Option[Baudrate]) extends HardwareControlMessage
  case class SerialMonitorResult(baudrateOrError: Either[String, BaudrateState]) extends HardwareControlMessage
  case class SerialMonitorMessage(message: SerialMessage) extends HardwareControlMessage
  case class Ping() extends HardwareControlMessage

  val uploadUnavailableMessage: UploadSoftwareResult =
    UploadSoftwareResult(Some("Upload request not available, agent is already doing something"))

  val monitorUnavailableMessage: SerialMonitorResult =
    SerialMonitorResult(Left("Monitor request not available, agent is already doing something"))

  def isNonPingMessage(message: HardwareControlMessage): Option[HardwareControlMessage] =
    message match {
      case Ping()         => None
      case nonPingMessage => Some(nonPingMessage)
    }

  def isBaudrateChangeMessage(message: HardwareControlMessage): Option[Baudrate] =
    message match {
      case SerialMonitorResult(Right(BaudrateState(baudrate, isChanged))) => Option.when(isChanged)(baudrate)
      case _                                                              => None
    }
}
