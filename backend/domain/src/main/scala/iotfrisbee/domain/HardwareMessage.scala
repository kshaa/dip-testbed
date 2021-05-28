package iotfrisbee.domain

case class HardwareMessage(id: HardwareMessageId, hardwareId: HardwareId, messageType: String, message: String)
