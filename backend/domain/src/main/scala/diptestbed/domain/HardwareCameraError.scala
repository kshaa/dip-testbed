package diptestbed.domain

sealed trait HardwareCameraError
object HardwareCameraError {
  case class RequestInquirerObligatory() extends HardwareCameraError
}
