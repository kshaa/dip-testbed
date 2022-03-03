package diptestbed.domain

import cats.effect.kernel.Temporal
import cats.implicits._
import diptestbed.domain.HardwareCameraEvent.{CameraListenerHeartbeatFinished, CameraListenerHeartbeatStarted, Started, Subscription}
import diptestbed.domain.HardwareCameraListenerMessage.ListenerCameraHeartbeat
import diptestbed.domain.HardwareCameraMessage.{CameraListenersHeartbeatFinish, CameraListenersHeartbeatStart, StopBroadcasting}
import diptestbed.domain.HeartbeatProjection.expectHeartbeats

object HardwareCameraHeartbeatProjection {
  def project[F[_]: Temporal, A](
    send: (A, Any) => F[Unit],
    publish: (PubSubTopic, Any) => F[Unit],
  )(previousState: HardwareCameraState[A], event: HardwareCameraEvent[A]): Option[F[Unit]] = {
    val start: F[Unit] = send(previousState.self, CameraListenersHeartbeatStart())
    val request: F[Unit] = previousState.hardwareIds.map(id => publish(id.cameraBroacastTopic(), ListenerCameraHeartbeat())).sequence.void
    val finish: F[Unit] = send(previousState.self, CameraListenersHeartbeatFinish())
    val stop = send(previousState.self, StopBroadcasting())
    val expectTimeout = previousState.listenerHeartbeatConfig.waitTimeout
    val scheduleTimeout = previousState.listenerHeartbeatConfig.nextTimeout
    event match {
      case Started() => Some(start)
      case CameraListenerHeartbeatStarted() => Some(expectHeartbeats(request, finish, expectTimeout))
      case CameraListenerHeartbeatFinished() => Some(
        if (previousState.listenerHeartbeatsReceived == 0) stop
        else implicitly[Temporal[F]].sleep(scheduleTimeout) >> start)
      case Subscription(_) => Option.when(!previousState.broadcasting)(start)
      case _ => None
    }
  }
}
