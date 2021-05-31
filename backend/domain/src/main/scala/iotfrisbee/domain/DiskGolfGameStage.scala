package iotfrisbee.domain

import java.time.ZonedDateTime

case class DiskGolfGameStage(
  id: DiskGolfGameStageId,
  gameId: DiskGolfGameId,
  finishBasketId: DiskGolfBasketId,
  timestamp: ZonedDateTime,
  throwCount: Int,
)
