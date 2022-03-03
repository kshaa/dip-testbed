package diptestbed.domain

sealed abstract class HardwareCameraEvent[A]
object HardwareCameraEvent {
  // Lifecycle
  case class Started[A]() extends HardwareCameraEvent[A]
  case class Ended[A]() extends HardwareCameraEvent[A]

  // Camera content
  case class ChunkReceived[A](chunk: Array[Byte]) extends HardwareCameraEvent[A]
  case class CameraDropped[A](reason: String) extends HardwareCameraEvent[A]
  case class CameraPinged[A]() extends HardwareCameraEvent[A]
  
  // Subscribers
  case class Subscription[A](inquirer: A) extends HardwareCameraEvent[A]
  case class BroadcastStopped[A]() extends HardwareCameraEvent[A]

  // Listener liveness check
  sealed abstract class CameraListenerHeartbeatEvent[A] extends HardwareCameraEvent[A]
  case class CameraListenerHeartbeatStarted[A]() extends CameraListenerHeartbeatEvent[A]
  case class CameraListenerHeartbeatReceived[A]() extends CameraListenerHeartbeatEvent[A]
  case class CameraListenerHeartbeatFinished[A]() extends CameraListenerHeartbeatEvent[A]
}
