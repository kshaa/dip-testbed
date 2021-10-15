package iotfrisbee.domain

sealed trait HardwareControlState {}
object HardwareControlState {
  case object Initial extends HardwareControlState
}
