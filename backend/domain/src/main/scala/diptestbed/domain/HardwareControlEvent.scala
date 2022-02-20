package diptestbed.domain

sealed abstract class HardwareControlEvent[A]
object HardwareControlEvent {
  // Lifecycle
  case class Started[A]() extends HardwareControlEvent[A]
  case class Ended[A]() extends HardwareControlEvent[A]

  // Firmware upload
  case class UploadStarted[A](inquirer: Option[A], softwareId: SoftwareId) extends HardwareControlEvent[A]
  case class UploadFinished[A](oldInquirer: Option[A], error: Option[String]) extends HardwareControlEvent[A]

  // Serial port configuration
  case class MonitorConfigurationStarted[A](inquirer: Option[A], settings: Option[SerialConfig])
      extends HardwareControlEvent[A]
  case class MonitorConfigurationFinished[A](oldInquirer: Option[A], error: Option[String])
      extends HardwareControlEvent[A]
  case class MonitorDropExpected[A]() extends HardwareControlEvent[A]
  case class MonitorDropped[A](reason: String) extends HardwareControlEvent[A]

  // Serial port exchange
  case class MonitorMessageToClient[A](bytes: Array[Byte]) extends HardwareControlEvent[A]
  case class MonitorMessageToAgent[A](bytes: Array[Byte]) extends HardwareControlEvent[A]

  // Serial port listener liveness check
  sealed abstract class ListenerHeartbeatEvent[A] extends HardwareControlEvent[A]
  case class ListenerHeartbeatStarted[A]() extends ListenerHeartbeatEvent[A]
  case class ListenerHeartbeatReceived[A]() extends ListenerHeartbeatEvent[A]
  case class ListenerHeartbeatFinished[A]() extends ListenerHeartbeatEvent[A]
}
