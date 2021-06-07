package iotfrisbee.protocol

import iotfrisbee.domain.{DiskGolfDiskId, UserId}

case class CreateDiskGolfGame(name: String, diskId: DiskGolfDiskId, playerId: UserId)
