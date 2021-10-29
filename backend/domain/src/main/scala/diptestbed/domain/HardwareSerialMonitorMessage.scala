package diptestbed.domain

case class SerialConfig(
  receiveSize: Int,
  baudrate: Int,
  timeout: Float,
)

sealed trait HardwareSerialMonitorMessage {}
object HardwareSerialMonitorMessage {
  case class SerialMessageToAgent(base64Bytes: String) extends HardwareSerialMonitorMessage
  case class SerialMessageToClient(base64Bytes: String) extends HardwareSerialMonitorMessage
  case class MonitorUnavailable(reason: String) extends HardwareSerialMonitorMessage
}
