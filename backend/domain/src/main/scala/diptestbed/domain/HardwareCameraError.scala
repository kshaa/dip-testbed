package diptestbed.domain

sealed trait HardwareCameraError
object HardwareCameraError {
  case class NoReaction() extends HardwareCameraError
  case class RequestInquirerObligatory() extends HardwareCameraError
}
