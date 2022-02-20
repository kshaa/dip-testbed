package diptestbed.domain

import cats.effect.kernel.Temporal
import cats.implicits._
import diptestbed.domain.HardwareControlEvent._
import diptestbed.domain.HardwareControlMessageInternal._

object HardwareControlListenerHeartbeatProjection {

  def triggerHeartbeatChecks[F[_], A](
    send: (A, HardwareControlMessage) => F[Unit],
    previousState: HardwareControlState[A],
  ): F[Unit] =
    send(previousState.self, SerialMonitorListenersHeartbeatStart())

  def startHeartbeatChecks[F[_]: Temporal, A](
    send: (A, HardwareControlMessage) => F[Unit],
    previousState: HardwareControlState[A],
    publish: (PubSubTopic, HardwareControlMessage) => F[Unit],
  ): F[Unit] = {
    publish(previousState.hardwareId.serialTopic(), SerialMonitorListenersHeartbeatPing()) >>
      implicitly[Temporal[F]].sleep(previousState.listenerHeartbeatConfig.waitTimeout) >>
      send(previousState.self, SerialMonitorListenersHeartbeatFinish())
  }

  def finishHeartbeatChecks[F[_]: Temporal, A](
    send: (A, HardwareControlMessage) => F[Unit],
    previousState: HardwareControlState[A],
  ): F[Unit] =
    if (previousState.listenerHeartbeatsReceived == 0)
      send(previousState.agent, SerialMonitorRequestStop())
    else
      implicitly[Temporal[F]].sleep(previousState.listenerHeartbeatConfig.nextTimeout) >>
        triggerHeartbeatChecks(send, previousState)

  def project[F[_]: Temporal, A](
    send: (A, HardwareControlMessage) => F[Unit],
    publish: (PubSubTopic, HardwareControlMessage) => F[Unit],
  )(previousState: HardwareControlState[A], event: HardwareControlEvent[A]): Option[F[Unit]] = {
    event match {
      // If serial monitor successfully starts and is being monitored, trigger heartbeat check start
      case MonitorConfigurationFinished(_, None) => Some(triggerHeartbeatChecks(send, previousState))
      case h: ListenerHeartbeatEvent[A] =>
        h match {
          // When heartbeats are started, send ping to listeners and finish after a timeout
          case ListenerHeartbeatStarted() => Some(startHeartbeatChecks(send, previousState, publish))
          // When heartbeats are finished, count them up and either continue heartbeats or stop monitor
          case ListenerHeartbeatFinished() => Some(finishHeartbeatChecks(send, previousState))
          case ListenerHeartbeatReceived() => None
        }
      case _ => None
    }
  }
}
