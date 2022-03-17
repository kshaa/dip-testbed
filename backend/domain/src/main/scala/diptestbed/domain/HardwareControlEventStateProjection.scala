package diptestbed.domain

import diptestbed.domain.HardwareControlAgentState._
import diptestbed.domain.HardwareControlEvent._

object HardwareControlEventStateProjection {
  def project[A](previousState: HardwareControlState[A], event: HardwareControlEvent[A]): HardwareControlState[A] =
    event match {
      case UploadStarted(inquirer, _) => previousState.copy(agentState = Uploading(inquirer))
      case UploadFinished(_, _)       => previousState.copy(agentState = Initial())

      case AuthSucceeded(user) => previousState.copy(auth = Some(user))
      case AuthFailed(_)       => previousState.copy(auth = None)

      case MonitorConfigurationStarted(inquirer, _) => previousState.copy(agentState = ConfiguringMonitor(inquirer))
      case MonitorConfigurationFinished(_, _)       => previousState.copy(agentState = Initial())

      case ListenerHeartbeatStarted() => previousState.copy(listenerHeartbeatsReceived = 0)
      case ListenerHeartbeatReceived() =>
        previousState.copy(listenerHeartbeatsReceived = previousState.listenerHeartbeatsReceived + 1)

      case _: CheckingAuth[A] | _: MonitorDropped[A] | _: MonitorDropExpected[A] | _: MonitorMessageToClient[A] | _: MonitorMessageToAgent[A] |
           _: MonitorMessageToClient[A] | _: MonitorMessageToAgent[A] | _: ListenerHeartbeatFinished[A] | _: Started[A] |
           _: Ended[A] =>
        previousState
    }
}
