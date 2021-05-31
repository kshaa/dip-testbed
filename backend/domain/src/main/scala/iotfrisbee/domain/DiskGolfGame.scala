package iotfrisbee.domain

case class DiskGolfGame(
  id: DiskGolfGameId,
  diskId: DiskGolfDiskId,
  playerId: UserId,
)
