package diptestbed.domain

sealed abstract class HardwareControlAgentState[A] {}
object HardwareControlAgentState {
  case class Initial[A]() extends HardwareControlAgentState[A]
  case class Uploading[A](requester: Option[A] = None) extends HardwareControlAgentState[A]
  case class ConfiguringMonitor[A](requester: Option[A] = None) extends HardwareControlAgentState[A]
}
