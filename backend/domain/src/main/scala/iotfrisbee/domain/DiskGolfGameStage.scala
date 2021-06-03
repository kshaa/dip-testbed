package iotfrisbee.domain

import java.time.ZonedDateTime

case class DiskGolfGameStage(
  id: DiskGolfGameStageId,
  gameId: DiskGolfGameId,
  finishBasketId: DiskGolfBasketId,
  finishBasketTimestamp: ZonedDateTime,
  throwCount: Int,
)
