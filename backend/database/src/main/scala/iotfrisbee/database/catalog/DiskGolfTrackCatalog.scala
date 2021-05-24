package iotfrisbee.database.catalog

import java.util.{TimeZone, UUID}
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackUUID, UserId}
import slick.lifted.ProvenShape

object DiskGolfTrackCatalog {
  class DiskGolfTrackTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class DiskGolfTrackTable(tag: Tag) extends Table[DiskGolfTrackRow](tag, "disk_golf_track") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def ownerId: Rep[UUID] = column[UUID]("owner_id")
      def name: Rep[String] = column[String]("name")
      def timezone: Rep[String] = column[String]("timezone")

      def * : ProvenShape[DiskGolfTrackRow] =
        (
          uuid,
          ownerId,
          name,
          timezone,
        ) <> ((DiskGolfTrackRow.apply _).tupled, DiskGolfTrackRow.unapply)
    }

    object DiskGolfTrackQuery extends TableQuery[DiskGolfTrackTable](new DiskGolfTrackTable(_))
  }

  case class DiskGolfTrackRow(
    id: UUID,
    ownerId: UUID,
    name: String,
    timezone: String,
  )

  def fromDomain(diskGolfTrack: DiskGolfTrack): DiskGolfTrackRow =
    DiskGolfTrackRow(
      diskGolfTrack.uuid.value,
      diskGolfTrack.ownerId.value,
      diskGolfTrack.name,
      diskGolfTrack.timezone.toString,
    )

  def toDomain(diskGolfTrack: DiskGolfTrackRow): DiskGolfTrack =
    DiskGolfTrack(
      DiskGolfTrackUUID(diskGolfTrack.id),
      UserId(diskGolfTrack.ownerId),
      diskGolfTrack.name,
      TimeZone.getTimeZone(diskGolfTrack.timezone),
    )
}
