package diptestbed.protocol

import io.circe.Json
import diptestbed.domain.HardwareId

case class CreateHardwareMessage(messageType: String, message: Json, hardwareId: HardwareId)
