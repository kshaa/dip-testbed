package iotfrisbee.database.catalog

import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfDiskId, DiskGolfGame, DiskGolfGameId, UserId}
import slick.lifted.ProvenShape

import java.util.UUID

object DiskGolfGameCatalog {
  class DiskGolfGameTable(val dbDriver: JdbcDatabaseDriver) {

    import dbDriver.profile.api._

    class DiskGolfGameTable(tag: Tag) extends Table[DiskGolfGameRow](tag, "disk_golf_game") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def diskUUID: Rep[UUID] = column[UUID]("disk_uuid")
      def playerUUID: Rep[UUID] = column[UUID]("player_uuid")

      def * : ProvenShape[DiskGolfGameRow] =
        (
          uuid,
          diskUUID,
          playerUUID,
        ) <> ((DiskGolfGameRow.apply _).tupled, DiskGolfGameRow.unapply)
    }

    object DiskGolfGameQuery extends TableQuery[DiskGolfGameTable](new DiskGolfGameTable(_))
  }

  case class DiskGolfGameRow(
    id: UUID = UUID.randomUUID(),
    diskUUID: UUID,
    playerUUID: UUID,
  )

  def fromDomain(diskGolfGame: DiskGolfGame): DiskGolfGameRow =
    DiskGolfGameRow(
      diskGolfGame.id.value,
      diskGolfGame.diskId.value,
      diskGolfGame.playerId.value,
    )

  def toDomain(diskGolfGame: DiskGolfGameRow): DiskGolfGame =
    DiskGolfGame(
      DiskGolfGameId(diskGolfGame.id),
      DiskGolfDiskId(diskGolfGame.diskUUID),
      UserId(diskGolfGame.playerUUID),
    )
}
