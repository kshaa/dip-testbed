package iotfrisbee.domain

import iotfrisbee.domain.HardwareControlMessage.Baudrate

sealed trait HardwareSerialMonitorMessage {}
object HardwareSerialMonitorMessage {
  case class SerialMessage(base64Bytes: String) extends HardwareSerialMonitorMessage
  case class BaudrateSet(baudrate: Baudrate) extends HardwareSerialMonitorMessage
  case class BaudrateChanged(baudrate: Baudrate) extends HardwareSerialMonitorMessage
  case class MonitorUnavailable(reason: String) extends HardwareSerialMonitorMessage
}
