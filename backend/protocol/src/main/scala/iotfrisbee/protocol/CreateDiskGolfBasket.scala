package iotfrisbee.protocol

import iotfrisbee.domain.{DiskGolfTrackId, HardwareId}

case class CreateDiskGolfBasket(name: String, trackId: DiskGolfTrackId, hardwareId: Option[HardwareId])
