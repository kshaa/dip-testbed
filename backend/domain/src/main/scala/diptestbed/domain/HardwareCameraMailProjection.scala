package diptestbed.domain

import cats.effect.Temporal
import cats.implicits._
import diptestbed.domain.HardwareCameraEvent._
import diptestbed.domain.HardwareCameraListenerMessage.{ListenerCameraChunk, ListenerCameraDropped}
import diptestbed.domain.HardwareCameraMessage._

object HardwareCameraMailProjection {
  def project[F[_]: Temporal, A](
    die: F[Unit],
    send: (A, Any) => F[Unit],
    publish: (PubSubTopic, Any) => F[Unit],
    subscriptionMessage: (PubSubTopic, A) => Any
  )(state: HardwareCameraState[A], event: HardwareCameraEvent[A]): Option[F[Unit]] = {
    event match {
      case _: CheckingAuth[A] | _: CameraPinged[A] | _: CameraListenerHeartbeatEvent[A] =>
        None
      case AuthSucceeded(_)   => Some(
        send(state.camera, AuthResult(None)) >>
          send(state.self, StartLifecycle()))
      case AuthFailed(reason) => Some(send(state.camera, AuthResult(Some(reason))))

      case BroadcastStopped() => Some(send(state.camera, StopBroadcasting()))
      case Started() =>
        Some(state.hardwareIds.map(hardwareId =>
          send(state.pubSubMediator, subscriptionMessage(hardwareId.cameraMetaTopic(), state.self))).sequence.void)
      case ChunkReceived(chunk) => Some(state.hardwareIds.map(id =>
        publish(id.cameraBroacastTopic(), ListenerCameraChunk(chunk))).sequence.void)
      case CameraDropped(reason) => Some(state.hardwareIds.map(id =>
        publish(id.cameraBroacastTopic(), ListenerCameraDropped(reason))).sequence.void >> die)
      case Ended() => Some(state.hardwareIds.map(id =>
        publish(id.cameraBroacastTopic(), ListenerCameraDropped("Unknown end of camera stream"))).sequence.void)
      case Subscription(_) =>
//        val initialChunks = state.initialChunkArray()
        Some(send(state.camera, CameraSubscription()))
//        Some(send(state.camera, CameraSubscription()) >>
//          send(inquirer, ListenerCameraChunk(initialChunks)))
    }
  }
}
