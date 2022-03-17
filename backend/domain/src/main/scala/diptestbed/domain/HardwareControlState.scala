package diptestbed.domain

import diptestbed.domain.HardwareControlAgentState._

case class HardwareControlState[A](
  auth: Option[User],
  self: A,
  agent: A,
  hardwareId: HardwareId,
  listenerHeartbeatsReceived: Int,
  listenerHeartbeatConfig: HardwareListenerHeartbeatConfig,
  agentState: HardwareControlAgentState[A],
)

object HardwareControlState {
  def initial[A](
    self: A,
    agent: A,
    hardwareId: HardwareId,
    listenerHeartbeatConfig: HardwareListenerHeartbeatConfig,
  ): HardwareControlState[A] =
    HardwareControlState(
      None,
      self,
      agent,
      hardwareId,
      0,
      listenerHeartbeatConfig,
      Initial(),
    )
}
