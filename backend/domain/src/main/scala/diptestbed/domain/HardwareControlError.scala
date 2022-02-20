package diptestbed.domain

sealed trait HardwareControlError
object HardwareControlError {
  case object NoReaction extends HardwareControlError
  // The request could be removed here, but I currently need it for backwards compatibility
  case class StateForbidsRequest(request: HardwareControlMessage) extends HardwareControlError
}
