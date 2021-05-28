package iotfrisbee.protocol.messages.hardware

import iotfrisbee.domain.UserId

case class CreateHardware(name: String, ownerId: UserId)
