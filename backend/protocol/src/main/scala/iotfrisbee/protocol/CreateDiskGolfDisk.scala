package iotfrisbee.protocol

import iotfrisbee.domain.{DiskGolfTrackId, HardwareId}

case class CreateDiskGolfDisk(name: String, trackId: DiskGolfTrackId, hardwareId: Option[HardwareId])
