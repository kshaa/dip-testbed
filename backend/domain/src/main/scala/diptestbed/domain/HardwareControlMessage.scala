package diptestbed.domain

import diptestbed.domain.HardwareSerialMonitorMessage._

sealed trait HardwareControlMessage {}
object HardwareControlMessage {
  case class UploadSoftwareRequest(softwareId: SoftwareId) extends HardwareControlMessage
  case class UploadSoftwareResult(error: Option[String]) extends HardwareControlMessage
  case class SerialMonitorRequest(serialConfig: Option[SerialConfig]) extends HardwareControlMessage
  case class SerialMonitorResult(error: Option[String]) extends HardwareControlMessage
  case class SerialMonitorMessageToAgent(message: SerialMessageToAgent) extends HardwareControlMessage
  case class SerialMonitorMessageToClient(message: SerialMessageToClient) extends HardwareControlMessage
  case class Ping() extends HardwareControlMessage

  val uploadUnavailableMessage: UploadSoftwareResult =
    UploadSoftwareResult(Some("Upload request not available, agent is already doing something"))

  val monitorUnavailableMessage: SerialMonitorResult =
    SerialMonitorResult(Some("Monitor request not available, agent is already doing something"))

  def isNonPingMessage(message: HardwareControlMessage): Option[HardwareControlMessage] =
    message match {
      case Ping()         => None
      case nonPingMessage => Some(nonPingMessage)
    }
}
