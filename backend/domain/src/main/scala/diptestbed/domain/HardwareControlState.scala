package diptestbed.domain

import diptestbed.domain.HardwareControlAgentState._

case class HardwareControlState[A](
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
      self,
      agent,
      hardwareId,
      0,
      listenerHeartbeatConfig,
      Initial(),
    )
}
