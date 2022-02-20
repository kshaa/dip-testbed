package diptestbed.domain

import java.util.UUID

case class HardwareId(value: UUID) extends AnyVal {
  def serialTopic(): HardwareSerialTopic = HardwareSerialTopic(this)
  def actorId(): HardwareActorId = HardwareActorId(this)
}

case class HardwareSerialTopic(hardwareId: HardwareId) extends PubSubTopic {
  def text() = f"hardware-${hardwareId.value}-serial-monitor"
}

case class HardwareActorId(hardwareId: HardwareId) extends ActorPath {
  def text() = f"hardware-${hardwareId.value}-actor"
}
