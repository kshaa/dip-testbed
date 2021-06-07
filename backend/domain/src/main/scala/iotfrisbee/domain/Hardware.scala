package iotfrisbee.domain

case class Hardware(id: HardwareId, name: String, batteryPercent: Option[Double], ownerId: UserId)
