package diptestbed.domain

import cats.effect.kernel.Temporal
import cats.implicits._
import diptestbed.domain.HardwareControlEvent._
import diptestbed.domain.HardwareControlMessageInternal._
import diptestbed.domain.HeartbeatProjection.expectHeartbeats

object HardwareControlHeartbeatProjection {
  def project[F[_]: Temporal, A](
    send: (A, HardwareControlMessage) => F[Unit],
    publish: (PubSubTopic, HardwareControlMessage) => F[Unit],
  )(previousState: HardwareControlState[A], event: HardwareControlEvent[A]): Option[F[Unit]] = {
    val start: F[Unit] = send(previousState.self, SerialMonitorListenersHeartbeatStart())
    val request: F[Unit] = publish(previousState.hardwareId.serialBroadcastTopic(), SerialMonitorListenersHeartbeatPing())
    val finish: F[Unit] = send(previousState.self, SerialMonitorListenersHeartbeatFinish())
    val stop = send(previousState.agent, SerialMonitorRequestStop())
    val expectTimeout = previousState.listenerHeartbeatConfig.waitTimeout
    val scheduleTimeout = previousState.listenerHeartbeatConfig.nextTimeout
    val heartbeatsInCycle = previousState.listenerHeartbeatConfig.heartbeatsInCycle
    event match {
      case MonitorConfigurationFinished(_, None) => Some(start)
      case ListenerHeartbeatStarted() => Some(expectHeartbeats(request, finish, expectTimeout, heartbeatsInCycle))
      case ListenerHeartbeatFinished() => Some(
        if (previousState.listenerHeartbeatsReceived == 0) stop
        else implicitly[Temporal[F]].sleep(scheduleTimeout) >> start)
      case _ => None
    }
  }
}
