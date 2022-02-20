package diptestbed.domain

import scala.concurrent.duration._

case class HardwareListenerHeartbeatConfig(
  // Time until next heartbeat check since last finish
  nextTimeout: FiniteDuration,
  // Time to wait for heartbeats
  waitTimeout: FiniteDuration,
)

object HardwareListenerHeartbeatConfig {
  def default(): HardwareListenerHeartbeatConfig = HardwareListenerHeartbeatConfig(5.seconds, 4.seconds)
}
