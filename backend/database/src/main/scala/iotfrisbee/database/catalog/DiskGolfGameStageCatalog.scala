package iotfrisbee.database.catalog

import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfBasketId, DiskGolfGameId, DiskGolfGameStage, DiskGolfGameStageId}
import slick.lifted.ProvenShape

import java.time.ZonedDateTime
import java.util.UUID

object DiskGolfGameStageCatalog {
  class DiskGolfGameStageTable(val dbDriver: JdbcDatabaseDriver) {

    import dbDriver.profile.api._

    class DiskGolfGameStageTable(tag: Tag) extends Table[DiskGolfGameStageRow](tag, "disk_golf_game_stage") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def gameUUID: Rep[UUID] = column[UUID]("game_uuid")
      def finishBasketUUID: Rep[UUID] = column[UUID]("finish_basket_uuid")
      def timestamp: Rep[ZonedDateTime] = column[ZonedDateTime]("timestamp")
      def throwCount: Rep[Int] = column[Int]("throw_count")

      def * : ProvenShape[DiskGolfGameStageRow] =
        (
          uuid,
          gameUUID,
          finishBasketUUID,
          timestamp,
          throwCount,
        ) <> ((DiskGolfGameStageRow.apply _).tupled, DiskGolfGameStageRow.unapply)
    }

    object DiskGolfGameStageQuery extends TableQuery[DiskGolfGameStageTable](new DiskGolfGameStageTable(_))
  }

  case class DiskGolfGameStageRow(
    id: UUID = UUID.randomUUID(),
    gameUUID: UUID,
    finishBasketUUID: UUID,
    timestamp: ZonedDateTime,
    throwCount: Int,
  )

  def fromDomain(diskGolfGameStage: DiskGolfGameStage): DiskGolfGameStageRow =
    DiskGolfGameStageRow(
      diskGolfGameStage.id.value,
      diskGolfGameStage.gameId.value,
      diskGolfGameStage.finishBasketId.value,
      diskGolfGameStage.timestamp,
      diskGolfGameStage.throwCount,
    )

  def toDomain(diskGolfGameStage: DiskGolfGameStageRow): DiskGolfGameStage =
    DiskGolfGameStage(
      DiskGolfGameStageId(diskGolfGameStage.id),
      DiskGolfGameId(diskGolfGameStage.id),
      DiskGolfBasketId(diskGolfGameStage.finishBasketUUID),
      diskGolfGameStage.timestamp,
      diskGolfGameStage.throwCount,
    )
}
