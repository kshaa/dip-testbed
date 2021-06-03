package iotfrisbee.domain

import java.time.ZonedDateTime

case class DiskGolfGame(
  id: DiskGolfGameId,
  name: String,
  diskId: DiskGolfDiskId,
  playerId: UserId,
  startTimestamp: Option[ZonedDateTime],
  finished: Boolean,
)
