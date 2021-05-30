package iotfrisbee.protocol

import io.circe.Json
import iotfrisbee.domain.HardwareId

case class CreateHardwareMessage(messageType: String, message: Json, hardwareId: HardwareId)
