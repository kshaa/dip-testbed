package diptestbed.domain

import java.util.UUID

case class HardwareId(value: UUID) extends AnyVal {
  def cameraBroacastTopic(): HardwareCameraBroadcastTopic = HardwareCameraBroadcastTopic(this)
  def cameraMetaTopic(): HardwareCameraMetaTopic = HardwareCameraMetaTopic(this)
  def serialBroadcastTopic(): HardwareSerialBroadcastTopic = HardwareSerialBroadcastTopic(this)
  def actorId(): HardwareActorId = HardwareActorId(this)
}

case class HardwareSerialBroadcastTopic(hardwareId: HardwareId) extends PubSubTopic {
  def text() = f"hardware-${hardwareId.value}-serial-broadcast"
}

case class HardwareCameraBroadcastTopic(hardwareId: HardwareId) extends PubSubTopic {
  def text() = f"hardware-${hardwareId.value}-camera-broadcast"
}

case class HardwareCameraMetaTopic(hardwareId: HardwareId) extends PubSubTopic {
  def text() = f"hardware-${hardwareId.value}-camera-meta"
}

case class HardwareActorId(hardwareId: HardwareId) extends ActorPath {
  def text() = f"hardware-${hardwareId.value}-actor"
}
