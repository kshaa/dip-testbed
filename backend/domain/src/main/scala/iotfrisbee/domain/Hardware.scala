package iotfrisbee.domain

case class Hardware(id: HardwareId, name: String, batteryPercent: Double, ownerId: UserId)
