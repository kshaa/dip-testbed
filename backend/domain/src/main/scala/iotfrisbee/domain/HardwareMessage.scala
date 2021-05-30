package iotfrisbee.domain

import io.circe.Json

case class HardwareMessage(id: HardwareMessageId, hardwareId: HardwareId, messageType: String, message: Json)
