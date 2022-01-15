package diptestbed.domain

case class SerialConfig(
  receiveSize: Int,
  baudrate: Int,
  timeout: Float,
)

sealed trait HardwareSerialMonitorMessage {}
object HardwareSerialMonitorMessage {
  case class SerialMessageToAgent(bytes: Array[Byte]) extends HardwareSerialMonitorMessage
  case class SerialMessageToClient(bytes: Array[Byte]) extends HardwareSerialMonitorMessage
  case class MonitorUnavailable(reason: String) extends HardwareSerialMonitorMessage
}
