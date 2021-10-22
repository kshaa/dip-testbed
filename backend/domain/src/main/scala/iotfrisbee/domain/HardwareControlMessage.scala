package iotfrisbee.domain

sealed trait HardwareControlMessage {}
object HardwareControlMessage {
  case class UploadSoftwareRequest(softwareId: SoftwareId) extends HardwareControlMessage
  case class UploadSoftwareResult(error: Option[String]) extends HardwareControlMessage
  case class Ping() extends HardwareControlMessage
}
