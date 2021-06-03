package iotfrisbee.database.catalog

import java.time.ZonedDateTime
import java.util.UUID
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfDiskId, DiskGolfGame, DiskGolfGameId, UserId}
import slick.lifted.ProvenShape

object DiskGolfGameCatalog {
  class DiskGolfGameTable(val dbDriver: JdbcDatabaseDriver) {

    import dbDriver.profile.api._

    class DiskGolfGameTable(tag: Tag) extends Table[DiskGolfGameRow](tag, "disk_golf_game") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def name: Rep[String] = column[String]("name")
      def diskUUID: Rep[UUID] = column[UUID]("disk_uuid")
      def playerUUID: Rep[UUID] = column[UUID]("player_uuid")
      def startTimestamp: Rep[Option[String]] = column[Option[String]]("start_timestamp")
      def finished: Rep[Boolean] = column[Boolean]("finished")

      def * : ProvenShape[DiskGolfGameRow] =
        (
          uuid,
          name,
          diskUUID,
          playerUUID,
          startTimestamp,
          finished,
        ) <> ((DiskGolfGameRow.apply _).tupled, DiskGolfGameRow.unapply)
    }

    object DiskGolfGameQuery extends TableQuery[DiskGolfGameTable](new DiskGolfGameTable(_))
  }

  case class DiskGolfGameRow(
    id: UUID = UUID.randomUUID(),
    name: String,
    diskUUID: UUID,
    playerUUID: UUID,
    startTimestamp: Option[String] = None,
    finished: Boolean = false,
  )

  def fromDomain(diskGolfGame: DiskGolfGame): DiskGolfGameRow =
    DiskGolfGameRow(
      diskGolfGame.id.value,
      diskGolfGame.name,
      diskGolfGame.diskId.value,
      diskGolfGame.playerId.value,
      diskGolfGame.startTimestamp.map(_.toString),
      diskGolfGame.finished,
    )

  def toDomain(diskGolfGame: DiskGolfGameRow): DiskGolfGame =
    DiskGolfGame(
      DiskGolfGameId(diskGolfGame.id),
      diskGolfGame.name,
      DiskGolfDiskId(diskGolfGame.diskUUID),
      UserId(diskGolfGame.playerUUID),
      diskGolfGame.startTimestamp.map(ZonedDateTime.parse(_)),
      diskGolfGame.finished,
    )
}
