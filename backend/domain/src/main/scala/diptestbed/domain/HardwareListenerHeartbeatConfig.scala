package diptestbed.domain

import scala.concurrent.duration._

case class HardwareListenerHeartbeatConfig(
  // Time until next heartbeat check since last finish
  nextTimeout: FiniteDuration,
  // Time to wait for heartbeats
  waitTimeout: FiniteDuration,
  // How many heartbeat requests are issued in a single cycle
  heartbeatsInCycle: Int
)

object HardwareListenerHeartbeatConfig {
  def default(): HardwareListenerHeartbeatConfig = HardwareListenerHeartbeatConfig(10.seconds, 8.seconds, 3)
  def fromConfig(appConfig: DIPTestbedConfig): HardwareListenerHeartbeatConfig =
    HardwareListenerHeartbeatConfig(
      appConfig.heartbeatingTimeout,
      appConfig.heartbeatingTime,
      appConfig.heartbeatsInCycle)
}
