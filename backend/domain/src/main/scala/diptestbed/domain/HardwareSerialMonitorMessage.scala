package diptestbed.domain

case class SerialConfig(
  receiveSize: Int,
  baudrate: Int,
  timeout: Float,
)

sealed trait HardwareSerialMonitorMessage

sealed trait HardwareSerialMonitorMessageBinary extends HardwareSerialMonitorMessage
object HardwareSerialMonitorMessageBinary {
  case class SerialMessageToAgent(bytes: Array[Byte]) extends HardwareSerialMonitorMessageBinary
  case class SerialMessageToClient(bytes: Array[Byte]) extends HardwareSerialMonitorMessageBinary
}

sealed trait HardwareSerialMonitorMessageNonBinary extends HardwareSerialMonitorMessage
object HardwareSerialMonitorMessageNonBinary {
  case class AuthResult(error: Option[String]) extends HardwareSerialMonitorMessageNonBinary
  case class MonitorUnavailable(reason: String) extends HardwareSerialMonitorMessageNonBinary
  case class ConnectionClosed(reason: String) extends HardwareSerialMonitorMessageNonBinary
}
