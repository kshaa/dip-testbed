package iotfrisbee.protocol

import iotfrisbee.domain.UserId

case class CreateHardware(name: String, ownerId: UserId)
