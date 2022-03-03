package diptestbed.domain

import cats.Monad
import cats.implicits._
import diptestbed.domain.HardwareControlEvent._
import diptestbed.domain.HardwareControlMessageExternalBinary._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareControlMessageInternal._
import diptestbed.domain.HardwareSerialMonitorMessageBinary._

object HardwareControlMailProjection {
  def project[F[_]: Monad, A](
    send: (A, HardwareControlMessage) => F[Unit],
    publish: (PubSubTopic, HardwareControlMessage) => F[Unit],
  )(state: HardwareControlState[A], event: HardwareControlEvent[A]): Option[F[Unit]] = {
    event match {
      case Started() | Ended() | ListenerHeartbeatFinished() | ListenerHeartbeatReceived() |
          ListenerHeartbeatStarted() =>
        None

      case UploadStarted(_, softwareId)       => Some(send(state.agent, UploadSoftwareRequest(softwareId)))
      case UploadFinished(oldInquirer, error) => Some(oldInquirer.traverse(send(_, UploadSoftwareResult(error))).void)

      case MonitorConfigurationStarted(_, settings) => Some(send(state.agent, SerialMonitorRequest(settings)))
      case MonitorConfigurationFinished(oldInquirer, error) =>
        Some(oldInquirer.traverse(send(_, SerialMonitorResult(error))).void)
      case _: MonitorDropExpected[A] => Some(send(state.agent, SerialMonitorRequestStop()))

      case MonitorMessageToClient(bytes) =>
        Some(publish(state.hardwareId.serialBroadcastTopic(), SerialMonitorMessageToClient(SerialMessageToClient(bytes))))
      case MonitorMessageToAgent(bytes) =>
        Some(send(state.agent, SerialMonitorMessageToAgent(SerialMessageToAgent(bytes))))
      case MonitorDropped(reason) =>
        Some(publish(state.hardwareId.serialBroadcastTopic(), SerialMonitorUnavailable(reason)))
    }
  }
}
