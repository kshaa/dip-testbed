package iotfrisbee.protocol

import iotfrisbee.domain.HardwareId

case class CreateHardwareMessage(messageType: String, message: String, hardwareId: HardwareId)
