package diptestbed.domain

import diptestbed.domain.HardwareCameraEvent._

object HardwareCameraEventStateProjection {
  def project[A](previousState: HardwareCameraState[A], event: HardwareCameraEvent[A]): HardwareCameraState[A] =
    event match {
      case ChunkReceived(chunk) => previousState.initialChunks match {
        case Nil => previousState.copy(initialChunks = List(chunk))
        case chunks if previousState.initialChunks.length < previousState.maxInitialChunks =>
          previousState.copy(initialChunks = chunk :: chunks)
        case _ => previousState
      }

      case AuthSucceeded(user) => previousState.copy(auth = Some(user))
      case AuthFailed(_)       => previousState.copy(auth = None)

      case Subscription(_) => previousState.copy(broadcasting = true)
      case BroadcastStopped() => previousState.copy(broadcasting = false, initialChunks = List.empty)

      case CameraListenerHeartbeatStarted() => previousState.copy(listenerHeartbeatsReceived = 0)
      case CameraListenerHeartbeatReceived() =>
        previousState.copy(listenerHeartbeatsReceived = previousState.listenerHeartbeatsReceived + 1)

      case _: CheckingAuth[A] | _: CameraPinged[A] | _: CameraListenerHeartbeatFinished[A] | _: CameraDropped[A] | _: Started[A] | _: Ended[A] =>
        previousState
    }
}
