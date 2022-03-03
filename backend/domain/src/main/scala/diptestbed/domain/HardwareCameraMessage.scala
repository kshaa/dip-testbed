package diptestbed.domain

sealed abstract class HardwareCameraMessage
sealed abstract class HardwareCameraMessageExternal extends HardwareCameraMessage
object HardwareCameraMessage {
  case class StartLifecycle() extends HardwareCameraMessage
  case class EndLifecycle() extends HardwareCameraMessage

  case class CameraSubscription() extends HardwareCameraMessageExternal
  case class StopBroadcasting() extends HardwareCameraMessageExternal
  case class CameraUnavailable(reason: String) extends HardwareCameraMessageExternal
  case class CameraChunk(chunk: Array[Byte]) extends HardwareCameraMessage

  case class Ping() extends HardwareCameraMessageExternal

  case class CameraListenersHeartbeatStart() extends HardwareCameraMessage
  case class CameraListenersHeartbeatPong() extends HardwareCameraMessage
  case class CameraListenersHeartbeatFinish() extends HardwareCameraMessage
}
